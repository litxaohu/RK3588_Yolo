# RK3576 YOLOv5 High-Performance Web Service

This project implements a high-performance deployment of the YOLOv5 object detection model on the Rockchip RK3576 platform based on RKNN-Toolkit-Lite2. It features a pure Python architecture and focuses on providing FastAPI-based Web APIs and MJPEG video streaming for robust backend deployment.

## Directory Structure

- `model/`: Directory for YOLOv5 RKNN model file (`yolov5s.rknn`) and anchors file (`anchors_yolov5.txt`)
- `video/`: Directory for test video file (`test.mp4`)
- `lib/`: NPU runtime dependency libraries (`librknnrt.so`)
- `rknn-toolkit-lite2-packages/`: Python packages for RKNN-Toolkit-Lite2
- `py_utils/`: Inference engine wrapper and YOLOv5 anchor-based post-processing
- `web_detection.py`: Multi-threaded Web API service & video streaming
- `requirements.txt`: Python dependencies list

## Environment Setup

### 1. System Requirements
- Rockchip RK3576 platform (e.g., reComputer RK-CV)
- Ubuntu 20.04 / Debian 11
- Python 3.7+

### 2. Install Dependencies

Install basic dependencies:
```bash
pip3 install -r requirements.txt
```

Install RKNN-Toolkit-Lite2 (Choose the `.whl` file matching your Python version):
```bash
# Example for Python 3.9:
pip3 install rknn-toolkit-lite2-packages/rknn_toolkit_lite2-2.0.0b0-cp39-cp39-linux_aarch64.whl
```

## Running Guide

> **Note:** Before running, please ensure that the quantized `yolov5s.rknn` and `anchors_yolov5.txt` are placed in the `model/` directory, and the test video `test.mp4` is placed in the `video/` directory (to be provided by the user).

This project focuses on the High-performance Web Service mode (`web_detection.py`), omitting the local GUI detection script.

```bash
# Start service, process video/test.mp4 by default
python3 web_detection.py --model_path model/yolov5s.rknn --anchors model/anchors_yolov5.txt --video_path video/test.mp4

# Process camera feed (default: /dev/video1)
python3 web_detection.py --model_path model/yolov5s.rknn --anchors model/anchors_yolov5.txt --camera_id 1

# Pure Web mode (No local video source processing)
python3 web_detection.py --model_path model/yolov5s.rknn --anchors model/anchors_yolov5.txt --camera_id -1
```

## Web Access & API Description

After the service starts, it runs on `0.0.0.0:8000` by default.

### 1. Web Real-time Preview
Access in browser: `http://<Board-IP>:8000`
- Provides real-time video stream preview
- Supports dynamic adjustment of Confidence threshold and NMS threshold
- Supports uploading local videos for backend queue processing

### 2. Video Analysis API
- `POST /api/video/upload`: Upload video file
- `POST /api/video/analyze`: Submit video analysis task
- `GET /api/video/status`: Query analysis progress
- `GET /api/video/download/{filename}`: Download analyzed video

### 3. Inference API
- **Endpoint**: `POST /api/models/yolov5/predict`
- **Parameters (Form/File)**:
  - `file`: Upload image file
  - `video`: Upload video file (used with timestamp)
  - `timestamp`: Extract frame at specific time (seconds)
  - `realtime`: Boolean, use the current camera frame
  - `conf`: Confidence threshold (optional)
  - `iou`: NMS IOU threshold (optional)
- **Response Example**:
```json
{
  "success": true,
  "source": "uploaded image",
  "predictions": [
    {
      "class": "person",
      "confidence": 0.89,
      "box": {"x1": 100, "y1": 50, "x2": 200, "y2": 300}
    }
  ],
  "image": {"width": 1280, "height": 720}
}
```
