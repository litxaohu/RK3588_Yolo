# RK3576 YOLOv8-Seg 实例分割与 Web 预览项目

该项目基于 RKNN-Toolkit-Lite2，在瑞芯微 RK3576 平台上实现 YOLOv8-Seg 实例分割模型的高性能部署。项目采用纯 Python 架构，集成了 FastAPI 提供 Web API 和 MJPEG 视频流预览，同时支持本地 GUI 实时显示。

**特别说明**：本项目的分割后处理逻辑（包含边界框解码、NMS、掩码解析与缩放、多边形轮廓提取）已经**完全使用纯 Numpy 与 OpenCV 进行了重写**，彻底去除了原版代码中对 `torch` 和 `torchvision` 的沉重依赖。这显著降低了内存占用，并提升了嵌入式板卡上的启动速度与推理速度。

## 核心特性
- **硬件加速**: 充分利用 RK3576 的 2 TOPS NPU 算力架构。
- **实例分割**: 高性能掩码生成与多边形轮廓提取。
- **灵活输入**: 支持摄像头和本地 MP4 视频输入。

## 目录结构
- `lib/`: 存放 NPU 运行时的依赖库 (`librknnrt.so`)
- `model/`: 存放用于 RK3576 转换好的 `.rknn` 模型 (如 `yolov8n-seg.rknn`)
- `py_utils/`: 推理引擎封装与轻量级分割后处理工具
- `web_detection.py`: 主程序 (支持 Web 预览和 API)

## 快速开始

### 1. 运行项目 (单命令，双模式预览)

本项目支持 **本地 GUI** 和 **Web 浏览器** 同时预览。程序会自动检测显示环境，如果未连接显示器，则自动降级为纯 Web 模式。

#### 步骤 A: 配置显示权限 (可选)
如果连接了显示器并希望在本地看到窗口：
```bash
xhost +local:docker
```

#### 步骤 B: 一键运行
```bash
sudo docker run --rm --privileged --net=host \
    -e PYTHONUNBUFFERED=1 \
    -e RKNN_LOG_LEVEL=0 \
    --device /dev/video0:/dev/video0 \
    --device /dev/dri/renderD128:/dev/dri/renderD128 \
    -v /proc/device-tree/compatible:/proc/device-tree/compatible \
    recomputer-rk-cv/debug/rk3576-yolov8-seg:latest \
    python3 web_detection.py --model_path model/yolov8n-seg.rknn --camera_id 0
```
访问地址: `http://<开发板_IP>:8000`

> **注意**: 如果需要自定义类别，可以增加 `-v $(pwd)/class_config.txt:/app/class_config.txt \` 挂载和 `--class_path` 参数。程序默认使用 COCO 80 类。

示例：

```bash
sudo docker run --rm --privileged --net=host \
    -e PYTHONUNBUFFERED=1 \
    -e RKNN_LOG_LEVEL=0 \
    -v $(pwd)/class_config.txt:/app/class_config.txt \
    --device /dev/video0:/dev/video0 \
    --device /dev/dri/renderD128:/dev/dri/renderD128 \
    -v /proc/device-tree/compatible:/proc/device-tree/compatible \
    recomputer-rk-cv/debug/rk3576-yolov8-seg:latest \
    python3 web_detection.py --model_path model/yolov8n-seg.rknn --camera_id 0 --class_path class_config.txt
```

> **注意**: 如果你想使用本地视频进行测试而不是摄像头，请使用 `--video_path` 参数：
```bash
sudo docker run --rm --privileged --net=host \
    -e PYTHONUNBUFFERED=1 \
    -e RKNN_LOG_LEVEL=0 \
    -v $(pwd)/video:/app/video \
    --device /dev/dri/renderD128:/dev/dri/renderD128 \
    -v /proc/device-tree/compatible:/proc/device-tree/compatible \
    recomputer-rk-cv/debug/rk3576-yolov8-seg:latest \
    python3 web_detection.py --model_path model/yolov8n-seg.rknn --video_path video/test.mp4
```

---

## 🔌 API 接口文档

本项目提供了兼容 Ultralytics Cloud API 标准的 RESTful 接口，支持通过图片、视频上传或直接调用摄像头进行实例分割检测。

### 1. 模型推理接口 (Predict)

**接口路径:** `POST /api/models/yolov8_seg/predict` (或 `/api/models/yolo11/predict` 具体取决于脚本映射)

#### 请求参数 (Multipart/Form-Data):
- `file`: (可选) 需要检测的图片文件。
- `video`: (可选) 需要检测的 MP4 视频文件。
- `timestamp`: (可选) 视频文件中的时间戳 (秒)，返回该时刻对应帧的检测结果。默认为 0。
- `realtime`: (可选) 布尔值。如果为 `true` 或未提供 `file`/`video` 参数，则返回当前摄像头帧的检测结果。
- `conf`: (可选) 单次请求的置信度阈值，范围 0.0-1.0。
- `iou`: (可选) 单次请求的 NMS IOU 阈值，范围 0.0-1.0。

#### 使用示例:

**1. 图片检测:**
```bash
curl -X POST "http://127.0.0.1:8000/api/models/yolov8_seg/predict" -F "file=@/home/cat/001.jpg"
```

**2. 视频指定帧检测:**
```bash
curl -X POST "http://127.0.0.1:8000/api/models/yolov8_seg/predict" -F "video=@/home/cat/test.mp4" -F "timestamp=5.5"
```

**3. 获取当前摄像头帧检测:**
```bash
curl -X POST "http://127.0.0.1:8000/api/models/yolov8_seg/predict" -F "realtime=true"
```

#### 响应格式 (JSON):
返回结果包含了提取出的**多边形轮廓坐标 (`polygons`)**，方便前端直接使用 SVG 或 Canvas 渲染。
```json
{
  "success": true,
  "source": "video frame at 5.5s",
  "predictions": [
    {
      "class": "person",
      "confidence": 0.92,
      "box": { "x1": 100, "y1": 200, "x2": 300, "y2": 500 },
      "polygons": [
        [100, 200], [150, 210], [160, 300]
      ]
    }
  ],
  "image": { "width": 1280, "height": 720 }
}
```

### 2. 系统配置接口 (Config)

用于动态调整实时视频流和默认推理的阈值。

#### 获取当前配置
- **接口路径:** `GET /api/config`
- **响应:** `{"obj_thresh": 0.25, "nms_thresh": 0.45}`

#### 更新系统配置
- **接口路径:** `POST /api/config`
- **请求体 (JSON):** `{"obj_thresh": 0.3, "nms_thresh": 0.5}`
- **响应:** `{"status": "success"}`

### 3. 实时视频流接口 (Video Feed)

获取绘制了检测框和半透明掩码的实时 MJPEG 视频流，可直接嵌入到 HTML `<img>` 标签中。

- **接口路径:** `GET /api/video_feed`
- **调用示例:** `<img src="http://<开发板_IP>:8000/api/video_feed">`

---

## 🛠️ 开发者指南 (生产环境建议)
### 代码结构说明
- `web_detection.py`:
    - **双模式支持**: 集成了 FastAPI，同时支持本地渲染和 MJPEG 流媒体输出。
    - **环境自适应**: 自动检测 `DISPLAY` 环境变量，如果不存在则静默跳过 GUI 初始化。
    - **RKNN 推理**: 封装了 RKNN 初始化、模型加载和多核推理逻辑。
    - **动态加载**: 支持通过 `--class_path` 动态加载类别配置。
    - **后处理**: 基于纯 Numpy 实现的高性能边界框解码、NMS 与轮廓提取 (`cv2.findContours`)。

### 修改模型
1. 将训练并转换好的 .rknn 模型放入 `model/` 目录。
2. 在运行命令中添加 `--model_path` 参数指向新模型。