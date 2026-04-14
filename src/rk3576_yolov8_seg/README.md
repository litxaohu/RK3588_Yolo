# RK3576 YOLOv8-Seg Instance Segmentation & Web Preview

This project implements high-performance deployment of the YOLOv8-Seg instance segmentation model on the Rockchip RK3576 platform based on RKNN-Toolkit-Lite2. It uses a pure Python architecture, integrating FastAPI to provide Web APIs and MJPEG video streaming.

**Special Note**: The segmentation post-processing logic in this project (including bounding box decoding, NMS, mask parsing, scaling, and contour extraction) has been **completely rewritten using pure Numpy and OpenCV**, thoroughly removing the heavy dependencies on `torch` and `torchvision` found in the original code. This significantly reduces memory footprint and improves startup and inference speeds on embedded boards.

## Directory Structure

- `model/`: Directory for YOLOv8-Seg RKNN model file (`yolov8n-seg.rknn`)
- `video/`: Directory for test video file (`test.mp4`)
- `lib/`: NPU runtime dependency libraries (`librknnrt.so`)
- `rknn-toolkit-lite2-packages/`: Python packages for RKNN-Toolkit-Lite2
- `py_utils/`: Inference engine wrapper and lightweight segmentation post-processing utilities
- `web_detection.py`: High-performance Web API service & video streaming
- `requirements.txt`: Python dependencies list

## Environment Setup

### 1. Hardware Requirements
- Rockchip RK3576/RK3576 development board (e.g., reComputer RK-CV series)
- USB Camera (for real-time detection)

### 2. System Requirements
- Ubuntu 20.04/22.04 or Debian 11 recommended
- Kernel with NPU driver included

### 3. Install Dependencies

```bash
# 1. Update system and install dependencies
sudo apt update
sudo apt install -y python3-pip python3-dev libgl1-mesa-glx libglib2.0-0

# 2. Install Python basic dependencies
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. Install RKNN-Toolkit-Lite2 (choose according to your Python version)
# Example for Python 3.9:
pip3 install rknn-toolkit-lite2-packages/rknn_toolkit_lite2-2.0.0b0-cp39-cp39-linux_aarch64.whl
```

## Running Guide

> **Note:** Before running, please ensure that the quantized `yolov8n-seg.rknn` is placed in the `model/` directory, and the test video `test.mp4` is placed in the `video/` directory (to be provided by the user).

This project focuses on the High-performance Web Service mode, specifically designed for Web video streaming and APIs.

```bash
# Start service, process video/test.mp4 by default
python3 web_detection.py --model_path model/yolov8n-seg.rknn --video video/test.mp4

# Process camera feed (e.g., /dev/video0)
python3 web_detection.py --model_path model/yolov8n-seg.rknn --camera_id 0
```

## Web Access & API Description

After the service starts, it runs on `0.0.0.0:8000` by default.

### 1. Web Real-time Preview
Access in browser: `http://<Board-IP>:8000`
The page provides real-time video stream viewing (including the overlay rendering of target boxes and semi-transparent segmentation masks) and supports dynamic adjustment of Confidence and NMS thresholds.

### 2. RESTful APIs

- **Get current config**: `GET /api/config`
- **Update config**: `POST /api/config`
- **Get video stream**: `GET /api/video_feed`
- **Inference prediction**: `POST /api/models/yolo11/predict`
  - Supports uploading images (`file`)
  - Supports uploading videos and specifying timestamp (`video`, `timestamp`)
  - Supports using current camera frame (`realtime=true`)
  - The return result includes class, confidence, bounding box (`box`), and **polygon contour coordinates (`polygons`)** extracted via `cv2.findContours`, making it easy for the frontend to render directly using SVG or Canvas.

## Performance Notes

- The project is configured by default to use `RKNNLite.NPU_CORE_0_1_2`, fully utilizing the 3 NPU cores of RK3576 (2 TOPS compute power).
- With `torch` completely removed, the time overhead for model loading and mask computation is significantly reduced.