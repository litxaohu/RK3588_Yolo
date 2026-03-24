import os
import cv2
import sys
import argparse
import time
import numpy as np
import threading
from fastapi import FastAPI, Response, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import uvicorn
from typing import Optional

# Import shared tools
from py_utils.coco_utils import COCO_test_helper
import py_utils.obb_utils as obb_utils

# Try to import RKNN-Toolkit-Lite2
try:
    from rknnlite.api import RKNNLite
    RKNN_LITE_AVAILABLE = True
except ImportError:
    RKNN_LITE_AVAILABLE = False
    print("Warning: RKNN-Toolkit-Lite2 not available, using fallback")

# Constants
OBJ_THRESH = 0.25
NMS_THRESH = 0.45
IMG_SIZE = (640, 640)  # (width, height)

# Default Classes for YOLOv8-OBB (DOTA dataset usually)
DEFAULT_CLASSES = ('plane', 'ship', 'storage tank', 'baseball diamond', 'tennis court', 
'basketball court', 'ground track field', 'harbor', 'bridge', 'large vehicle', 'small vehicle', 'helicopter',
           'roundabout', 'soccer ball field', 'swimming pool')

CLASSES = DEFAULT_CLASSES

def load_classes(path):
    """
    Load classes from file
    """
    global CLASSES
    if not path or not os.path.exists(path):
        CLASSES = DEFAULT_CLASSES
        return

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            import re
            items = re.findall(r'"([^"]*)"', content)
            if items:
                CLASSES = tuple(items)
                print(f"Successfully loaded {len(CLASSES)} classes from {path}")
            else:
                items = [item.strip().strip('"') for item in content.split(',') if item.strip()]
                if items:
                    CLASSES = tuple(items)
                    print(f"Loaded {len(CLASSES)} classes from {path} (fallback parsing)")
                else:
                    print(f"Warning: No classes found in {path}, using default classes")
                    CLASSES = DEFAULT_CLASSES
    except Exception as e:
        print(f"Error loading classes from {path}: {e}. Using default classes")
        CLASSES = DEFAULT_CLASSES

# Dynamic Configuration
class DetectionConfig:
    def __init__(self):
        self.obj_thresh = 0.25
        self.nms_thresh = 0.45
        self.lock = threading.Lock()

    def update(self, obj_thresh, nms_thresh):
        with self.lock:
            self.obj_thresh = obj_thresh
            self.nms_thresh = nms_thresh

    def get(self):
        with self.lock:
            return self.obj_thresh, self.nms_thresh

det_config = DetectionConfig()

# --- FastAPI Components ---
app = FastAPI(title="RK3576 YOLOv8-OBB Web Preview")

@app.get("/api/config")
async def get_config():
    obj, nms = det_config.get()
    return {"obj_thresh": obj, "nms_thresh": nms}

@app.post("/api/config")
async def update_config(config: dict):
    det_config.update(config.get("obj_thresh", 0.25), config.get("nms_thresh", 0.45))
    return {"status": "success"}

# Global variables
_global_model = None
_global_co_helper = None

@app.post("/api/models/yolo_obb/predict")
async def predict(
    file: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    timestamp: Optional[float] = Form(None),
    realtime: Optional[bool] = Form(False),
    conf: Optional[float] = Form(None),
    iou: Optional[float] = Form(None)
):
    if _global_model is None or _global_co_helper is None:
        return {"success": False, "message": "Model not initialized"}

    try:
        img = None
        source_info = ""

        if file:
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            source_info = "uploaded image"

        elif video:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(await video.read())
                tmp_path = tmp.name
            
            cap = cv2.VideoCapture(tmp_path)
            if cap.isOpened():
                if timestamp is not None:
                    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
                ret, frame = cap.read()
                if ret:
                    img = frame
                    source_info = f"video frame at {timestamp if timestamp else 0}s"
                cap.release()
            os.unlink(tmp_path)

        if img is None:
            img = frame_buffer.get_raw_frame()
            source_info = "realtime camera frame"

        if img is None:
            return {"success": False, "message": "No valid input source found"}

        h_orig, w_orig = img.shape[:2]

        # Preprocess
        # We need ratio and padding to restore coordinates later
        input_img, ratio, (dw, dh) = preprocess_frame_with_info(img, _global_co_helper)

        # Inference
        outputs = _global_model.run(input_img)

        # Post-process
        current_obj_thresh, current_nms_thresh = det_config.get()
        target_conf = conf if conf is not None else current_obj_thresh
        target_iou = iou if iou is not None else current_nms_thresh

        pred_boxes = post_process_obb(outputs, target_conf, target_iou)

        predictions = []
        if pred_boxes:
            for box in pred_boxes:
                # Restore coordinates
                # box has xmin, ymin, xmax, ymax, angle
                # We need to rotate it to get 4 points, then scale back
                
                # 1. Get rotated points in 640x640 scale
                points = obb_utils.rotate_rectangle(box.xmin, box.ymin, box.xmax, box.ymax, box.angle)
                
                # 2. Scale back to original image
                restored_points = []
                for px, py in points:
                    px = (px - dw) / ratio
                    py = (py - dh) / ratio
                    restored_points.append([int(px), int(py)])
                
                predictions.append({
                    "class": CLASSES[box.classId] if box.classId < len(CLASSES) else str(box.classId),
                    "confidence": float(box.score),
                    "poly": restored_points, # List of [x, y]
                    "angle": float(box.angle)
                })

        return {
            "success": True,
            "source": source_info,
            "predictions": predictions,
            "image": {
                "width": w_orig,
                "height": h_orig
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": str(e)}

class FrameBuffer:
    def __init__(self):
        self.frame = None
        self.raw_frame = None
        self.lock = threading.Lock()

    def set_frame(self, frame, raw_frame=None):
        with self.lock:
            self.frame = frame
            if raw_frame is not None:
                self.raw_frame = raw_frame

    def get_frame(self):
        with self.lock:
            return self.frame

    def get_raw_frame(self):
        with self.lock:
            return self.raw_frame.copy() if self.raw_frame is not None else None

frame_buffer = FrameBuffer()

@app.get("/api/video_feed")
async def video_feed():
    def generate():
        while True:
            frame = frame_buffer.get_frame()
            if frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.03)
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/")
async def index():
    return Response(content="""
    <html>
      <head>
        <title>RK3576 YOLOv8-OBB Preview</title>
        <style>
          body { background-color: #1a1a1a; color: white; text-align: center; font-family: sans-serif; margin: 0; padding: 20px; }
          .container { max-width: 1000px; margin: 0 auto; }
          .video-box { margin: 20px auto; display: inline-block; border: 5px solid #333; border-radius: 10px; overflow: hidden; background: #000; }
          .controls { background: #2a2a2a; padding: 20px; border-radius: 10px; display: inline-block; text-align: left; min-width: 400px; }
          .control-group { margin-bottom: 15px; }
          h1 { color: #00e676; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>RK3576 YOLOv8-OBB Real-time Detection</h1>
          <div class="video-box">
            <img src="/api/video_feed" style="max-width: 100%; height: auto;">
          </div>
          <div class="controls">
            <p>Use /api/config to change thresholds.</p>
          </div>
        </div>
      </body>
    </html>
    """, media_type="text/html")

def run_fastapi(host, port):
    uvicorn.run(app, host=host, port=port, log_level="info", log_config=None)

# --- Inference Logic ---

def post_process_obb(outputs, obj_thresh, nms_thresh):
    if outputs is None or len(outputs) < 2:
        return []
    
    # outputs layout: [feature_map1, feature_map2, feature_map3, ..., angle_feature]
    # Assume the last one is angle feature
    angle_feature = outputs[-1]
    features = outputs[:-1]
    
    all_boxes = []
    
    # Calculate cumulative offsets for angle feature indexing
    # We need to identify which feature map corresponds to which stride
    # And we assume angle feature is flattened concatenation of grids in specific order (usually stride 8 -> 16 -> 32)
    
    # First, collect feature map info
    feat_info = []
    for i, x in enumerate(features):
        n, c, h, w = 1, 1, 1, 1
        x_reshaped = None
        
        if x.ndim == 4:
            if x.shape[1] > x.shape[3]: # Likely NCHW
                n, c, h, w = x.shape
                x_reshaped = x.reshape(n, c, -1)
            else: # Likely NHWC
                n, h, w, c = x.shape
                x_reshaped = x.transpose(0, 3, 1, 2).reshape(n, c, -1)
        else:
            continue
            
        stride = IMG_SIZE[0] // w
        feat_info.append({
            'stride': stride,
            'h': h,
            'w': w,
            'data': x_reshaped
        })
    
    # Sort by stride (ascending: 8, 16, 32...) to match angle feature layout
    # Assuming angle feature is concatenated from largest grid (smallest stride) to smallest grid
    feat_info.sort(key=lambda k: k['stride'])
    
    current_offset = 0
    for info in feat_info:
        stride = info['stride']
        h = info['h']
        w = info['w']
        data = info['data']
        
        # Calculate expected grid size for this stride based on IMG_SIZE
        # This is to verify if we are processing in correct order
        # expected_w = IMG_SIZE[0] // stride
        
        boxes = obb_utils.process(data, w, h, stride, angle_feature, current_offset, objectThresh=obj_thresh)
        all_boxes.extend(boxes)
        
        # Update offset for next feature map
        current_offset += h * w
        
    # NMS
    nms_boxes = obb_utils.NMS(all_boxes, nmsThresh=nms_thresh)
    return nms_boxes

def draw_obb(image, boxes, ratio, dw, dh):
    for box in boxes:
        # box coords are in 640x640 scale
        # We need to restore to original image scale
        
        # 1. Get rotated points
        points = obb_utils.rotate_rectangle(box.xmin, box.ymin, box.xmax, box.ymax, box.angle)
        
        # 2. Restore coordinates
        restored_points = []
        for px, py in points:
            px = (px - dw) / ratio
            py = (py - dh) / ratio
            restored_points.append([int(px), int(py)])
            
        # Draw poly
        pts = np.array(restored_points, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(image, [pts], True, (0, 255, 0), 2)
        
        # Draw label
        label = f"{CLASSES[box.classId]}: {box.score:.2f}"
        # Use first point for label
        cv2.putText(image, label, (restored_points[0][0], restored_points[0][1] - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

class RKNNLiteModel:
    def __init__(self, model_path):
        if not RKNN_LITE_AVAILABLE:
            raise ImportError("RKNN-Toolkit-Lite2 is not available")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"RKNN model file not found: {model_path}")
        self.rknn_lite = RKNNLite()
        print(f'Loading RKNN model from {model_path}...', flush=True)
        ret = self.rknn_lite.load_rknn(model_path)
        if ret != 0:
            raise Exception(f"Load RKNN model failed with error code: {ret}")
        print('Initializing runtime...', flush=True)
        ret = self.rknn_lite.init_runtime()
        if ret != 0:
            raise Exception(f"Init runtime failed with error code: {ret}")
        print('RKNN model loaded successfully', flush=True)
    
    def run(self, inputs):
        try:
            if len(inputs.shape) == 3:
                inputs = np.expand_dims(inputs, axis=0)
            if inputs.dtype != np.uint8:
                inputs = inputs.astype(np.uint8)
            return self.rknn_lite.inference(inputs=[inputs])
        except Exception as e:
            print(f"Inference error: {e}")
            return None
    
    def release(self):
        if hasattr(self, 'rknn_lite'):
            self.rknn_lite.release()

def preprocess_frame_with_info(frame, co_helper):
    # wrapper to get info
    img, ratio, (dw, dh) = co_helper.letter_box(im=frame.copy(), new_shape=(IMG_SIZE[1], IMG_SIZE[0]), pad_color=(114,114,114), info_need=True)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img, ratio, (dw, dh)

def main():
    parser = argparse.ArgumentParser(description='YOLOv8-OBB detection on RK3576')
    parser.add_argument('--model_path', type=str, required=True, help='RKNN model path')
    parser.add_argument('--camera_id', type=int, default=-1, help='Camera device ID. If not provided (-1), defaults to using video/test.mp4')
    parser.add_argument('--video_path', type=str, help='Path to video file')
    parser.add_argument('--class_path', type=str, help='Path to class_config.txt')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Web server host')
    parser.add_argument('--port', type=int, default=8000, help='Web server port')
    args = parser.parse_args()

    if not RKNN_LITE_AVAILABLE:
        print("Error: RKNN-Toolkit-Lite2 is not available.")
        return

    if args.class_path:
        load_classes(args.class_path)

    global _global_model, _global_co_helper
    _global_model = RKNNLiteModel(args.model_path)
    _global_co_helper = COCO_test_helper(enable_letter_box=True)

    # Start Web Server
    web_thread = threading.Thread(target=run_fastapi, args=(args.host, args.port), daemon=True)
    web_thread.start()
    print(f"Web Preview available at http://{args.host}:{args.port}")

    # Main Loop
    cap = None
    
    # If no explicit video path and no explicit camera id (or camera_id is default -1)
    if not args.video_path and args.camera_id == -1:
        default_video = os.path.join(os.path.dirname(__file__), 'video', 'test.mp4')
        if os.path.exists(default_video):
            print(f"No camera_id or video_path specified. Using default video: {default_video}")
            args.video_path = default_video
        else:
            print(f"Warning: Default video {default_video} not found. Falling back to camera 0.")
            args.camera_id = 0

    if args.video_path:
        cap = cv2.VideoCapture(args.video_path)
    else:
        cap = cv2.VideoCapture(args.camera_id)
        # Set camera resolution if needed
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not cap.isOpened():
        print("Error: Could not open video source.")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                if args.video_path: # Loop video
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    break

            # We don't set frame to None here, otherwise the web feed will flicker or show nothing.
            # We will set both encoded and raw frame at the end of the loop.
            
            try:
                # Preprocess
                input_img, ratio, (dw, dh) = preprocess_frame_with_info(frame, _global_co_helper)

                # Inference
                outputs = _global_model.run(input_img)

                # Postprocess
                obj_thresh, nms_thresh = det_config.get()
                
                # Use threading to prevent main loop blocking if post-processing is extremely slow
                boxes = post_process_obb(outputs, obj_thresh, nms_thresh)

                # Draw
                draw_frame = frame.copy()
                if boxes:
                    draw_obb(draw_frame, boxes, ratio, dw, dh)
            except Exception as e:
                print(f"Error during processing: {e}")
                import traceback
                traceback.print_exc()
                draw_frame = frame.copy()

            # Encode for Web
            try:
                ret, buffer = cv2.imencode('.jpg', draw_frame)
                if ret:
                    frame_buffer.set_frame(buffer.tobytes(), raw_frame=frame)
            except Exception as e:
                print(f"Error encoding frame: {e}")
                
            # Yield execution to other threads
            time.sleep(0.001)

            # Optional: Local Display if available
            if os.environ.get('DISPLAY'):
                cv2.imshow('RK3576 YOLOv8-OBB', draw_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            # Control framerate
            # time.sleep(0.01)

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        _global_model.release()

if __name__ == '__main__':
    main()
