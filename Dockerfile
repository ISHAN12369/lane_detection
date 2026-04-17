FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1 \
    libxcb1 \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install flask numpy opencv-python pillow scikit-image

EXPOSE 7860
CMD ["python", "app.py"]