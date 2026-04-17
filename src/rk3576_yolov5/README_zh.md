# RK3576 YOLOv5 高性能 Web 服务

本项目在瑞芯微 RK3576 平台上基于 RKNN-Toolkit-Lite2 实现了 YOLOv5 目标检测模型的高性能部署。采用纯 Python 架构，去除了本地 GUI 依赖，专注于集成 FastAPI 提供高并发 Web API 与 MJPEG 视频流，完美契合工业级量产后端部署需求。

## 目录结构

- `model/`: YOLOv5 RKNN 模型文件 (`yolov5s.rknn`) 及先验框配置 (`anchors_yolov5.txt`) 存放目录
- `video/`: 测试视频文件 (`test.mp4`) 存放目录
- `lib/`: NPU 运行依赖动态库 (`librknnrt.so`)
- `rknn-toolkit-lite2-packages/`: RKNN-Toolkit-Lite2 官方 Python 安装包
- `py_utils/`: 推理引擎封装及 YOLOv5 Anchor-based Numpy 后处理工具
- `web_detection.py`: 多线程 Web API 服务及视频流核心程序
- `requirements.txt`: Python 依赖清单

## 环境配置

### 1. 系统要求
- 瑞芯微 RK3576 平台 (如 reComputer RK-CV)
- Ubuntu 20.04 / Debian 11 系统
- Python 3.7+

### 2. 安装依赖包

安装基础依赖：
```bash
pip3 install -r requirements.txt
```

安装 RKNN-Toolkit-Lite2 (请根据板端 Python 版本选择对应的 `.whl` 文件)：
```bash
# 以 Python 3.9 为例:
pip3 install rknn-toolkit-lite2-packages/rknn_toolkit_lite2-2.0.0b0-cp39-cp39-linux_aarch64.whl
```

## 运行指南

> **注意：** 运行前请确保已将量化好的 `yolov5s.rknn` 和对应的 `anchors_yolov5.txt` 放置在 `model/` 目录下，测试视频 `test.mp4` 放置在 `video/` 目录下（此部分需用户自行补全）。

本项目专注于高性能 Web 服务 (`web_detection.py`)，抛弃了本地实时弹窗检测脚本。

```bash
# 启动服务，默认处理 video/test.mp4
python3 web_detection.py --model_path model/yolov5s.rknn --anchors model/anchors_yolov5.txt --video_path video/test.mp4

# 处理摄像头画面 (默认使用 /dev/video1)
python3 web_detection.py --model_path model/yolov5s.rknn --anchors model/anchors_yolov5.txt --camera_id 1

# 纯 Web 模式 (不处理本地视频源，仅供上传推理)
python3 web_detection.py --model_path model/yolov5s.rknn --anchors model/anchors_yolov5.txt --camera_id -1
```

## Web 访问与 API 说明

服务启动后，默认运行在 `0.0.0.0:8000`。

### 1. Web 实时预览
在浏览器中访问：`http://<开发板IP>:8000`
- 提供实时视频流预览
- 支持动态调节置信度 (Confidence) 与 NMS 阈值
- 支持上传本地视频进行后端队列分析

### 2. 视频分析 API
- `POST /api/video/upload`: 上传视频文件
- `POST /api/video/analyze`: 提交视频分析任务
- `GET /api/video/status`: 查询分析进度
- `GET /api/video/download/{filename}`: 下载分析完成的视频

### 3. 图像推理 API
- **接口路径**: `POST /api/models/yolov5/predict`
- **参数说明 (Form/File)**:
  - `file`: 上传的图片文件
  - `video`: 上传的视频文件 (配合 timestamp 使用)
  - `timestamp`: 提取视频指定时间的帧 (秒)
  - `realtime`: 布尔值，使用当前摄像头帧
  - `conf`: 置信度阈值 (可选)
  - `iou`: NMS IOU 阈值 (可选)
- **返回示例**:
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