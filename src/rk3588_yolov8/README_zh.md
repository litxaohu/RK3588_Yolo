# RK3588 YOLOv8 目标检测与 Web 预览项目

该项目基于 RKNN-Toolkit-Lite2，在瑞芯微 RK3588 平台上实现 YOLOv8 目标检测模型的高性能部署。项目采用纯 Python 架构，集成了 FastAPI 提供 Web API 和 MJPEG 视频流预览。

**特别说明**：本工程中的后处理逻辑（包含 DFL 解码和 NMS 非极大值抑制等）**全部使用纯 Numpy 与 OpenCV 进行了重写**，彻底解除了原版 `yolov8.py` 代码对 `torch` 和 `torchvision` 的重度依赖。这使得程序在嵌入式板端占用内存极小，启动与推理速度极快。

## 目录结构

- `model/`: 存放 YOLOv8 的 RKNN 模型文件 (`yolov8n.rknn`)
- `video/`: 存放用于测试的视频文件 (`test.mp4`)
- `lib/`: 存放 NPU 运行时的依赖库 (`librknnrt.so`)
- `rknn-toolkit-lite2-packages/`: 存放 RKNN-Toolkit-Lite2 的 Python 安装包
- `py_utils/`: 包含推理引擎封装和目标检测相关的轻量化后处理工具
- `web_detection.py`: 高性能 Web API 服务与视频推流
- `requirements.txt`: Python 依赖列表

## 环境准备

### 1. 硬件要求
- 瑞芯微 RK3588/RK3576 开发板 (例如: reComputer RK-CV 系列)
- 支持 USB 摄像头 (用于实时检测)

### 2. 系统要求
- 推荐使用 Ubuntu 20.04/22.04 或 Debian 11 系统
- 内核已包含 NPU 驱动

### 3. 安装依赖

```bash
# 1. 更新系统并安装系统依赖
sudo apt update
sudo apt install -y python3-pip python3-dev libgl1-mesa-glx libglib2.0-0

# 2. 安装 Python 基础依赖
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 安装 RKNN-Toolkit-Lite2 (根据 Python 版本选择)
# 以 Python 3.9 为例：
pip3 install rknn-toolkit-lite2-packages/rknn_toolkit_lite2-2.0.0b0-cp39-cp39-linux_aarch64.whl
```

## 运行指南

> **注意：** 在运行之前，请确保已将量化好的 `yolov8n.rknn` 放入 `model/` 目录下，并将测试视频 `test.mp4` 放入 `video/` 目录下（用户自行补充）。

本项目专注于高性能 Web 服务模式，专为 Web 端视频流和 API 设计。

```bash
# 启动服务，默认处理 video/test.mp4
python3 web_detection.py --model_path model/yolov8n.rknn --video video/test.mp4

# 处理摄像头画面 (如 /dev/video0)
python3 web_detection.py --model_path model/yolov8n.rknn --camera_id 0
```

## Web 访问与 API 说明

服务启动后，默认运行在 `0.0.0.0:8000`。

### 1. Web 实时预览
在浏览器中访问：`http://<开发板IP>:8000`
页面提供实时视频流查看（包含目标框的叠加渲染），并支持动态调整置信度 (Confidence) 和 NMS 阈值。

### 2. RESTful API 接口

- **获取当前配置**: `GET /api/config`
- **更新配置**: `POST /api/config`
- **获取视频流**: `GET /api/video_feed`
- **推理预测**: `POST /api/models/yolov8/predict`
  - 支持上传图片 (`file`)
  - 支持上传视频并指定时间戳 (`video`, `timestamp`)
  - 支持使用当前摄像头画面 (`realtime=true`)
  - 返回结果包含类别、置信度、边界框 (`box`)。

## 性能说明

- 项目已默认配置使用 `RKNNLite.NPU_CORE_0_1_2`，充分利用 RK3588 的 3 个 NPU 核心 (6 TOPS 算力)。
- 彻底移除了 `torch` 后，模型加载和 DFL 解码的计算时间开销显著降低。