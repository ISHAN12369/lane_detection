import base64
import os
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

from flask import Flask, jsonify, render_template, request
from PIL import Image, ImageOps, UnidentifiedImageError

import test as lane_test


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "test_output"
INFERENCE_LOCK = threading.Lock()

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")


@contextmanager
def working_directory(path: Path):
    previous_dir = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous_dir)


def run_lane_detection(image_path: Path) -> dict[str, bytes]:
    OUTPUT_DIR.mkdir(exist_ok=True)
    args = SimpleNamespace(
        img=str(image_path),
        model_type="ENet",
        model=str(BASE_DIR / "log" / "best_model.pth"),
        width=512,
        height=256,
        save=str(OUTPUT_DIR),
    )

    with INFERENCE_LOCK:
        original_parse_args = lane_test.parse_args
        original_torch_load = lane_test.torch.load
        try:
            lane_test.parse_args = lambda: args
            lane_test.torch.load = lambda *load_args, **load_kwargs: original_torch_load(
                *load_args,
                map_location=lane_test.DEVICE,
                **load_kwargs,
            )
            with working_directory(BASE_DIR):
                lane_test.test()
        finally:
            lane_test.parse_args = original_parse_args
            lane_test.torch.load = original_torch_load

    output_paths = {
        "instance": OUTPUT_DIR / "instance_output.jpg",
        "binary": OUTPUT_DIR / "binary_output.jpg",
    }
    missing_outputs = [name for name, path in output_paths.items() if not path.exists()]
    if missing_outputs:
        missing_files = ", ".join(f"{name}_output.jpg" for name in missing_outputs)
        raise FileNotFoundError(f"Lane detection did not produce: {missing_files}")

    return {name: path.read_bytes() for name, path in output_paths.items()}


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.post("/predict")
def predict():
    uploaded_file = request.files.get("image")
    if uploaded_file is None or uploaded_file.filename == "":
        return jsonify({"error": "Please upload an image file."}), 400

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".jpg",
        ) as temp_file:
            uploaded_file.stream.seek(0)
            try:
                image = Image.open(uploaded_file.stream)
            except UnidentifiedImageError as exc:
                raise ValueError("Unsupported image file. Please upload a valid JPG or PNG image.") from exc

            # Normalize uploads so the existing inference path always receives a 3-channel image.
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.save(temp_file, format="JPEG")
            temp_file.flush()
            temp_path = Path(temp_file.name)

        result_bytes = run_lane_detection(temp_path)
    except Exception as exc:
        app.logger.exception("Prediction failed")
        return jsonify({"error": str(exc)}), 500
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)

    return jsonify(
        {
            "instance_image": base64.b64encode(result_bytes["instance"]).decode("ascii"),
            "binary_image": base64.b64encode(result_bytes["binary"]).decode("ascii"),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
