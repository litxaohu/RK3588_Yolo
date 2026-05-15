# RK3588 Whisper Speech Recognition Web Service & API Engine

This project implements a high-performance deployment of the OpenAI Whisper speech recognition model on the Rockchip RK3588 platform using RKNN-Toolkit-Lite2. It utilizes a pure Python architecture, integrates FastAPI to provide a powerful Web UI, and exposes industrial-grade RESTful API endpoints. It supports both synchronous short audio transcription and asynchronous long audio chunking transcription.

## Directory Structure

- `model/`: Directory for Whisper's Encoder/Decoder RKNN models, `vocab_en/zh.txt`, and `mel_80_filters.txt`.
- `audio/`: Directory for test audio files (e.g., `test_en.wav`).
- `workspace/`: Auto-created at runtime to temporarily store uploaded audio files.
- `lib/`: NPU runtime dependency libraries (`librknnrt.so`).
- `rknn-toolkit-lite2-packages/`: RKNN-Toolkit-Lite2 installation packages.
- `py_utils/`: Core business logic, including audio preprocessing, C++ level feature alignment, model scheduling, and custom Base64 decoder.
- `web_service.py`: Core startup entry, containing FastAPI routing, asynchronous task queues, and HTML frontend.
- `test_api.py`: Python script for testing core API endpoints.
- `requirements.txt`: Python dependencies list.

## API Documentation

In addition to the intuitive Web UI (accessible at `http://<IP>:8000`), this service provides 3 standardized core API endpoints for third-party system integration.

### 1. System Status API
- **Get Status**: `GET /api/system/status`
- **Update Config**: `POST /api/system/config`
  - Parameters (Form-Data): `model_size` (e.g., `base`), `language` (e.g., `en` or `zh`)

### 2. Sync Transcription API
- **URL**: `POST /api/models/whisper/predict`
- **Use Case**: Short audio commands (under 20 seconds) requiring immediate response.
- **Parameters (Form-Data)**:
  - `file`: Audio file.
  - `language` (Optional): Specify language for hot-swapping.
- **Response Example**:
  ```json
  {
      "status": "success",
      "data": {
          "text": "Hello, good morning",
          "language": "en",
          "duration": 4.5,
          "inference_time": 1.2
      }
  }
  ```

### 3. Async Task Queue API
- **Submit Task**: `POST /api/models/whisper/task`
  - **Use Case**: Long audio/video recordings (>20 seconds). The backend automatically slices the audio into 20s chunks, filters silence, and loops inference.
  - **Response**: Contains `task_id`.
- **Poll Status**: `GET /api/models/whisper/task/{task_id}`
  - **Response Example**:
  ```json
  {
      "status": "success",
      "data": {
          "status": "processing", // or "completed"
          "progress": "Processing chunk 3/15",
          "result": "Full transcribed text...",
          "duration": 300.5
      }
  }
  ```

## Running and Testing

### 1. Run with Docker (Recommended)

You can quickly deploy the Whisper service using the provided Docker image:

```bash
sudo docker run --rm -it --net=host \
    -e PYTHONUNBUFFERED=1 \
    -e RKNN_LOG_LEVEL=0 \
    -v /proc/device-tree/compatible:/proc/device-tree/compatible \
    recomputer-rk-cv/debug/rk3588_whisper:latest
```
*Access the Web UI at: `http://<Board_IP>:8000`*

### 2. Run Natively (Local Environment)

1. **Install Dependencies**:
   ```bash
   pip3 install "setuptools<=69.0.2"
   pip3 install -r requirements.txt
   ```

2. **Start Service**:
   ```bash
   python3 web_service.py --default_model base --port 8000
   ```

### 3. Test API Endpoints
Run the provided test script in another terminal to automatically send audio to the service and demonstrate the API interaction flow:
```bash
python3 test_api.py
```