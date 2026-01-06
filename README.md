# RK3588 YOLOv11 Real-time Detection

本项目基于瑞芯微 RK3588 平台，使用 RKNN-Toolkit2 进行 YOLOv11 目标检测模型的实时推理。项目支持 Docker 容器化部署，提供了完整的环境配置和运行脚本，能够利用 RK3588 的 NPU 进行硬件加速推理。

## 🌟 项目特性
- **高性能推理**：利用 RK3588 NPU (6TOPS) 加速 YOLOv11 模型。
- **容器化部署**：提供 Docker 镜像，一键运行，无需繁琐的环境配置。
- **多输入支持**：支持 USB 摄像头、本地视频文件、RTSP 流（通过 OpenCV）。
- **实时可视化**：提供实时检测画面预览，支持 FPS、推理耗时显示。

## 🛠️ 环境准备 (RK3588)

在 RK3588 开发板（如 Orange Pi 5, Radxa Rock 5B, LubanCat 等）上运行本项目前，需要安装 Docker。

### 安装 Docker
在板卡上执行以下命令（需要联网）：

```bash
# 1. 下载安装脚本
curl -fsSL https://get.docker.com -o get-docker.sh

# 2. 使用阿里云镜像源安装（推荐国内用户）
sudo sh get-docker.sh --mirror Aliyun

# 3. 启动 Docker 并设置开机自启
sudo systemctl enable docker
sudo systemctl start docker

# 4. (可选) 将当前用户加入 docker 用户组，避免每次都输 sudo
sudo usermod -aG docker $USER
# 注意：执行完上一条命令后需要注销并重新登录才能生效
```

## 🚀 快速开始

### 1. 拉取镜像
```bash
sudo docker pull ghcr.io/litxaohu/rk3588_yolo:latest
```

### 2. 运行检测

#### 方式 A：使用 USB 摄像头 (推荐)
将摄像头插入 USB 口，确认设备节点（通常为 `/dev/video0` 或 `/dev/video1`）。

```bash
# 假设摄像头是 /dev/video0
sudo docker run --rm --privileged --net=host --env DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /dev/bus/usb:/dev/bus/usb \
    --device /dev/video0:/dev/video0 \
    --device /dev/dri/renderD129:/dev/dri/renderD129 \
    -v /proc/device-tree/compatible:/proc/device-tree/compatible \
    -v $(pwd)/model:/app/model \
    ghcr.io/litxaohu/rk3588_yolo:latest \
    python realtime_detection.py --model_path model/yolo11n.rknn --camera_id 0
```
**注意**：
- `--device /dev/video0:/dev/video0`：将宿主机的摄像头映射到容器。
- `--camera_id 0`：告诉程序使用索引为 0 的摄像头。

#### 方式 B：使用本地 MP4 视频文件
将视频文件放在当前目录下（例如 `test.mp4`）。

```bash
sudo docker run --rm --privileged --net=host --env DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    --device /dev/dri/renderD129:/dev/dri/renderD129 \
    -v /proc/device-tree/compatible:/proc/device-tree/compatible \
    -v $(pwd)/model:/app/model \
    -v $(pwd)/test.mp4:/app/test.mp4 \
    ghcr.io/litxaohu/rk3588_yolo:latest \
    python realtime_detection.py --model_path model/yolo11n.rknn --video_path /app/test.mp4
```

## 📂 项目结构

```text
RK3588_Yolo/
├── Dockerfile              # Docker 镜像构建文件
├── README.md               # 项目说明文档
├── realtime_detection.py   # 主程序：推理、后处理、显示
├── requirements.txt        # Python 依赖
├── model/                  # 存放 RKNN 模型文件
│   ├── yolo11n.rknn
│   └── ...
└── lib/                    # (可选) 存放 librknnrt.so 等动态库
```

## 💻 二次开发指南

### 代码说明
- **`realtime_detection.py`**:
    - `RKNNLiteModel`: 封装了 RKNN 初始化、加载模型、推理的逻辑。
    - `preprocess_frame`: 图像预处理（Resize, Padding, Color conversion）。
    - `post_process`: YOLO 后处理（Box解码, NMS 非极大值抑制）。
    - `main`: 主循环，处理视频流，调用推理并显示结果。

### 修改模型
1. 将训练好并转换完成的 `.rknn` 模型放入 `model/` 目录。
2. 运行命令时修改 `--model_path` 参数指向新模型。

### 重新构建镜像
如果你修改了代码或依赖，需要重新构建 Docker 镜像：

```bash
# 在项目根目录下执行
sudo docker build -t rk3588_yolo:local .
```

构建完成后，使用 `rk3588_yolo:local` 替换命令中的镜像名即可运行。

## ❓ 常见问题 (Troubleshooting)

### Q1: 报错 `Can not find dynamic library on RK3588!` 或缺少 `librknnrt.so`
**原因**：容器内缺少 RKNN 运行时库。
**解决**：
1. 下载 `librknnrt.so` (通常在 RKNN-Toolkit2 仓库中)。
2. 将其放入项目根目录的 `lib/` 文件夹。
3. 运行容器时添加映射：`-v $(pwd)/lib/librknnrt.so:/usr/lib/librknnrt.so`。

### Q2: 报错 `Could not load the Qt platform plugin "xcb"`
**原因**：Docker 镜像缺少 GUI 相关的系统库。
**解决**：最新版镜像已修复此问题。如果遇到，请尝试更新镜像或手动安装 `libxcb-xinerama0` 等库。

### Q3: 预览画面太大，屏幕放不下
**解决**：代码中已默认将窗口大小调整为 1280x720。如需自定义，请修改 `realtime_detection.py` 中的 `cv2.resizeWindow` 参数。
