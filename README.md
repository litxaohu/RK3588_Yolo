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
```
