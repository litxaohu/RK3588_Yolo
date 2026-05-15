# RK3588 Whisper 语音识别 Web 服务与 API 引擎

本项目实现了在瑞芯微 RK3588 平台上，基于 RKNN-Toolkit-Lite2 对 Whisper 模型的高性能部署。采用纯 Python 架构，集成了 FastAPI，提供强大的 Web 交互界面以及工业级的标准 RESTful API 接口，支持短音频同步分析与长音频异步切片分析。

## 目录结构

- `model/`: 存放 Whisper 的 Encoder/Decoder RKNN 模型、`vocab_en/zh.txt` 词表以及 `mel_80_filters.txt` 滤波器文件。
- `audio/`: 存放测试音频文件（如 `test_en.wav`）。
- `workspace/`: 运行时自动创建，用于临时存放前端上传的音频文件。
- `lib/`: NPU 运行时依赖库 (`librknnrt.so`)。
- `rknn-toolkit-lite2-packages/`: RKNN-Toolkit-Lite2 安装包。
- `py_utils/`: 核心业务逻辑，包含音频预处理、C++ 级特征对齐、模型调度以及手搓 Base64 解码器。
- `web_service.py`: 核心启动入口，包含 FastAPI 路由、异步任务队列和 HTML 前端。
- `test_api.py`: 用于测试核心 API 接口的 Python 调用脚本。
- `requirements.txt`: Python 依赖清单。

## API 接口文档

除了直观的 Web UI（访问 `http://<IP>:8000`），本服务还提供 3 个标准化的核心 API 接口供第三方系统调用。

### 1. 获取/修改系统状态 API
- **获取状态**：`GET /api/system/status`
- **修改配置**：`POST /api/system/config`
  - 参数 (Form-Data)：`model_size` (如 `base`), `language` (如 `en` 或 `zh`)

#### 调用示例:
```bash
# 获取当前状态
curl -X GET "http://127.0.0.1:8000/api/system/status"

# 切换为中文识别
curl -X POST "http://127.0.0.1:8000/api/system/config" -F "model_size=base" -F "language=zh"
```

### 2. 短音频同步识别 API (Sync Transcription)
- **URL**: `POST /api/models/whisper/predict`
- **适用场景**: 20 秒以内的短音频指令，要求即时返回。
- **参数 (Form-Data)**:
  - `file`: 音频文件。
  - `language` (可选): 指定语言，热切换模型。

#### 调用示例:
```bash
# 同步识别音频文件
curl -X POST "http://127.0.0.1:8000/api/models/whisper/predict" -F "file=@/home/cat/test_en.wav"

# 指定语言进行识别
curl -X POST "http://127.0.0.1:8000/api/models/whisper/predict" -F "file=@/home/cat/test_zh.wav" -F "language=zh"
```

#### 返回示例 (JSON):
```json
{
  "status": "success",
  "data": {
    "text": "你好，早上好",
    "language": "zh",
    "duration": 4.5,
    "inference_time": 1.2
  }
}
```

### 3. 长音频异步任务队列 API (Async Task Queue)
- **提交任务**: `POST /api/models/whisper/task`
  - **适用场景**: 大于 20 秒的长录音/视频。后台会自动按 20s 滑窗切片，过滤静音并循环推理。
  - **返回**: 包含 `task_id`。
- **轮询进度**: `GET /api/models/whisper/task/{task_id}`

#### 调用示例:
```bash
# 提交长音频任务
curl -X POST "http://127.0.0.1:8000/api/models/whisper/task" -F "file=@/home/cat/long_meeting.wav"

# 轮询任务进度 (将 <task_id> 替换为实际 ID)
curl -X GET "http://127.0.0.1:8000/api/models/whisper/task/<task_id>"
```

#### 返回示例 (JSON):
```json
{
  "status": "success",
  "data": {
    "status": "processing",
    "progress": "Processing chunk 3/15",
    "result": "完整的拼接识别文本...",
    "duration": 300.5
  }
}
```

## 运行与测试

### 1. 使用 Docker 运行 (推荐)

使用提供的 Docker 镜像可以快速部署 Whisper 语音识别服务：

```bash
sudo docker run --rm -it --net=host \
    -e PYTHONUNBUFFERED=1 \
    -e RKNN_LOG_LEVEL=0 \
    -v /proc/device-tree/compatible:/proc/device-tree/compatible \
    recomputer-rk-cv/debug/rk3588_whisper:latest
```
*启动后，在浏览器访问: `http://<开发板IP>:8000`*

### 2. 本地原生运行

1. **安装依赖**:
   ```bash
   pip3 install "setuptools<=69.0.2"
   pip3 install -r requirements.txt
   ```

2. **启动服务**:
   ```bash
   python3 web_service.py --default_model base --port 8000
   ```

### 3. 测试 API 接口
在另一个终端运行测试脚本，会自动发送音频并展示完整 API 交互流程：
```bash
python3 test_api.py
```