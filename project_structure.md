# Lane Detection Project Structure

This document provides a technical overview of the Lane Detection Studio project, organized into Algorithm, Pipeline, Metrics, and Citations.

---

## Algorithm

The system implements **LaneNet**, a multi-task deep learning architecture designed for instance segmentation of road lanes.

### Model Architecture
- **Encoder**: A shared backbone extracts high-level features. Supported encoders include:
  - **ENet (Default)**: Optimized for real-time inference (~3M parameters).
  - **U-Net**: Balanced accuracy and speed (~30M parameters).
  - **DeepLabv3+**: ResNet-101 based for maximum accuracy (~50M parameters).
- **Dual Decoders**:
  - **Binary Decoder**: Performs semantic segmentation to identify lane vs. non-lane pixels.
  - **Instance Decoder**: Generates pixel-wise embeddings to distinguish individual lanes.

### Loss Functions
The model is trained using a multi-task loss function:
- **Focal Loss**: Used for binary segmentation to address severe class imbalance (lanes occupy <5% of the image).
- **Discriminative Loss**: Used for instance segmentation to cluster pixels of the same lane while pushing different lanes apart in embedding space.
- **Combined Loss Formula**: `Total Loss = 10 × Binary Loss + (0.3 × Var Loss + 1.0 × Dist Loss)`

---

## Pipeline

The inference pipeline follows a structured flow from raw input to visualized segmentation:

1. **Image Loading**: The source RGB image is loaded using the Pillow (PIL) library.
2. **Preprocessing**:
   - **Resizing**: Images are resized to **512 × 256** to match the model's input requirements.
   - **Normalization**: ImageNet statistics (mean/std) are applied to the input tensor.
3. **Model Forward Pass**: The shared encoder extracts features which are then processed by the simultaneous binary and instance decoders.
4. **Post-processing**:
   - **Binary Reconstruction**: Applies `argmax` and `softmax` to generate a binary mask.
   - **Instance Clustering**: Uses a `sigmoid` activation on embeddings to generate a probability map for lane instances.
5. **Visualization**: The results are converted into a binary mask image and a colored instance map for display in the web interface or CLI.

---

## Metrics

The performance and accuracy of the model are evaluated using standard segmentation metrics:

### Dice Coefficient (F1-Score)
- **Formula**: `Dice = 2 · |A∩B| / (|A| + |B|)`
- **Role**: Measures the overlap between the prediction and ground truth. It is robust to class imbalance and is the preferred metric for lane detection.
- **Range**: `[0, 1]`, with 1 representing perfect overlap.

### Intersection over Union (IoU)
- **Formula**: `IoU = |A∩B| / |A∪B|`
- **Role**: A stricter metric than Dice, penalizing both false positives and false negatives equally. It is a standard benchmark for segmentation tasks.

---

## Citations

The project is built upon the following academic research and architectures:

1. **LaneNet**: Neven, D., et al. (2018). ["Towards End-to-End Lane Detection: an Instance Segmentation Approach"](https://arxiv.org/abs/1802.05591). IEEE IV.
2. **ENet**: Paszke, A., et al. (2016). ["ENet: A Deep Neural Network Architecture for Real-Time Semantic Segmentation"](https://arxiv.org/abs/1606.02147).
3. **Discriminative Loss**: De Brabandere, B., et al. (2017). ["Semantic Instance Segmentation with a Discriminative Loss Function"](https://arxiv.org/abs/1708.02551).
4. **Focal Loss**: Lin, T.-Y., et al. (2017). ["Focal Loss for Dense Object Detection"](https://arxiv.org/abs/1708.02051). ICCV.
5. **DeepLabv3+**: Chen, L.-C., et al. (2018). ["Encoder-Decoder with Atrous Separable Convolution for Semantic Image Segmentation"](https://arxiv.org/abs/1802.02611). ECCV.
