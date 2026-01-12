# reComputer-RK-CV

本项目旨在为瑞芯微（Rockchip）系列开发板提供工业级、高性能的计算机视觉（CV）应用方案。目前已支持 **RK3588** 和 **RK3576** 平台，主要集成了 YOLOv11 目标检测模型。

## 项目架构

项目采用多平台适配架构，各平台代码和环境配置独立管理：

```text
reComputer-RK-CV/
├── docker/                 # Docker 镜像配置文件
│   ├── rk3576/             # RK3576 专属 Dockerfile
│   └── rk3588/             # RK3588 专属 Dockerfile
├── src/                    # 源码目录
│   ├── rk3576/             # RK3576 源码、模型及依赖库
│   └── rk3588/             # RK3588 源码、模型及依赖库
└── .github/workflows/      # GitHub Actions 自动化构建脚本
```

## 支持平台

| 平台 | 芯片 | 算力 | 镜像名称 |
| :--- | :--- | :--- | :--- |
| **RK3588** | RK3588/RK3588S | 6 TOPS | `rk3588-yolo` |
| **RK3576** | RK3576 | 6 TOPS | `rk3576-yolo` |

## 快速开始

### 1. 安装 Docker

在开发板上执行以下命令安装 Docker：

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

### 2. 运行项目 (以 RK3576 为例)

首先开启 X11 访问权限（用于预览窗口显示）：

```bash
xhost +local:docker
```

拉取最新镜像

```bash
sudo docker pull ghcr.io/litxaohu/rk3588_yolo:latest
sudo docker pull ghcr.io/litxaohu/rk3576_yolo:latest
```

运行 Docker 容器：

rk3588:

```bash
sudo docker run --rm --privileged --net=host --env DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /dev/bus/usb:/dev/bus/usb \
    --device /dev/video0:/dev/video0 \
    --device /dev/dri/renderD128:/dev/dri/renderD129 \
    -v /proc/device-tree/compatible:/proc/device-tree/compatible \
    ghcr.io/<your-username>/rk3576-yolo:latest
```

rk3576:

```bash
sudo docker run --rm --privileged --net=host --env DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /dev/bus/usb:/dev/bus/usb \
    --device /dev/video0:/dev/video0 \
    --device /dev/dri/renderD128:/dev/dri/renderD128 \
    -v /proc/device-tree/compatible:/proc/device-tree/compatible \
    ghcr.io/<your-username>/rk3576-yolo:latest
```

> **注意**：对于 RK3576，设备路径改为 `/dev/dri/renderD128`。

## 平台详细文档

- [RK3588 使用指南](src/rk3588/README.md)
- [RK3576 使用指南](src/rk3576/README.md)

## 自动化构建

本项目支持通过 GitHub Actions 自动构建多平台镜像。
- 当修改 `src/rk3588/` 目录时，会自动触发 `rk3588-yolo` 镜像的构建。
- 当修改 `src/rk3576/` 目录时，会自动触发 `rk3576-yolo` 镜像的构建。
- 支持手动触发构建，并可指定 `image_tag`。

## 💻 二次开发指南
### 代码说明
- `realtime_detection.py`:
    - RKNNLiteModel: 封装了 RKNN 初始化、加载模型、推理的逻辑。
    - preprocess_frame: 图像预处理（Resize, Padding, Color conversion）。
    - post_process: YOLO 后处理（Box解码, NMS 非极大值抑制）。
    - main: 主循环，处理视频流，调用推理并显示结果。
### 修改模型
1. 将训练好并转换完成的 .rknn 模型放入 model/ 目录。
2. 运行命令时修改 --model_path 参数指向新模型。

### 重新构建镜像
如果你修改了代码或依赖，需要重新构建 Docker 镜像：

# 在项目根目录下执行
sudo docker build -t rk3588_yolo:local .
构建完成后，使用 rk3588_yolo:local 替换命令中的镜像名即可运行。
