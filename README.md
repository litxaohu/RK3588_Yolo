# RKNN Toolkit2 Lite 实时目标检测

Please run: 
`pip install rknn_toolkit_lite2-1.6.0-cp311-cp311-linux_aarch64.whl` to install RKNN Toolkit2 Lite on the target device.

### 安装依赖
`pip install -r requirements.txt` 

```bash
# 基本用法
python realtime_detection.py --model_path your_model.rknn

# 指定摄像头（如果video1不可用）
python realtime_detection.py --model_path your_model.rknn --camera_id 0

# 设置目标FPS
python realtime_detection.py --model_path your_model.rknn --fps 25

# 使用本地视频文件
python realtime_detection.py --model_path your_model.rknn --video_path video/test.mp4
```

### Docker 运行 (GitHub Workflow)

本项目支持通过 Docker 快速运行。

1. **拉取镜像**：
```bash
docker pull ghcr.io/<your-username>/<repo-name>:latest
```

2. **运行容器**：

> 注意：为了显示视频窗口，需要配置 X11 转发。

**Linux (支持 X11):**
```bash
xhost +local:docker
docker run --rm --net=host --privileged --env DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /dev/bus/usb:/dev/bus/usb \
    --device /dev/video0:/dev/video0 \
    --device /dev/video1:/dev/video1 \
    --device /dev/dri/renderD129:/dev/dri/renderD129 \
    -v /proc/device-tree/compatible:/proc/device-tree/compatible \
    -v $(pwd)/model:/app/model \
    ghcr.io/<your-username>/<repo-name>:latest
```

**仅运行推理 (无显示窗口):**
如果不需要显示窗口，可以使用以下命令：
```bash
docker run --rm --privileged \
    --device /dev/video0:/dev/video0 \
    --device /dev/dri/renderD129:/dev/dri/renderD129 \
    -v /proc/device-tree/compatible:/proc/device-tree/compatible \
    -v $(pwd)/model:/app/model \
    ghcr.io/<your-username>/<repo-name>:latest
```

### 常见问题排查

#### 1. 报错 "Invalid RKNN model path" 或 "Load RKNN model failed with error code: -1"
**原因**：容器内找不到模型文件，或者权限不足。
**解决方法**：
- 确保 `-v $(pwd)/model:/app/model` 挂载路径正确。
- 确保宿主机上的 `model` 目录及其中的 `.rknn` 文件具有读取权限（例如 `chmod -R 755 model`）。
- 确保模型文件路径与命令行参数一致（默认是 `model/yolo11n.rknn`）。

#### 2. 报错 "Networking will not work" (IPv4 forwarding)
这是 Docker 的警告，通常不影响本地推理。如果需要网络功能，可以在宿主机启用 IP 转发：
```bash
sysctl -w net.ipv4.ip_forward=1
```
