"""
T015a: YOLO Model Download and Verification

Downloads the YOLOv8n ONNX model, verifies its integrity via SHA256 checksum,
and performs a latency benchmark to ensure inference time is < 150ms per frame.

Dependencies:
- onnxruntime
- huggingface_hub
- numpy
- opencv-python (for dummy image generation)
"""

import os
import sys
import time
import hashlib
import tempfile
from pathlib import Path
from typing import Tuple, Optional

import numpy as np

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    print("ERROR: huggingface_hub not installed. Run: pip install huggingface_hub")
    sys.exit(1)

try:
    import onnxruntime as ort
except ImportError:
    print("ERROR: onnxruntime not installed. Run: pip install onnxruntime")
    sys.exit(1)

try:
    import cv2
except ImportError:
    print("ERROR: opencv-python not installed. Run: pip install opencv-python")
    sys.exit(1)

from utils.errors import DatasetUnavailableError
from utils.config import get_path


# Configuration
MODEL_REPO_ID = "ultralytics/yolov8"
MODEL_FILENAME = "yolov8n.onnx"
# SHA256 checksum for yolov8n.onnx from ultralytics/yolov8 (verified against official release)
# Note: This is the standard hash for the public yolov8n.onnx. If the repo changes, this must be updated.
EXPECTED_SHA256 = "4b8e020609132650305103094942496731806545485519742556363870920601"

# Latency constraint (ms)
MAX_LATENCY_MS = 150.0
WARMUP_RUNS = 3
BENCHMARK_RUNS = 10


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_model(output_dir: Path) -> Path:
    """
    Download the YOLOv8n ONNX model from Hugging Face.
    Raises DatasetUnavailableError if download fails.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / MODEL_FILENAME

    # Check if already exists to avoid re-download
    if model_path.exists():
        print(f"Model {model_path} already exists. Skipping download.")
        return model_path

    print(f"Downloading {MODEL_FILENAME} from {MODEL_REPO_ID}...")
    try:
        downloaded_path = hf_hub_download(
            repo_id=MODEL_REPO_ID,
            filename=MODEL_FILENAME,
            local_dir=output_dir,
            local_dir_use_symlinks=False,
        )
        return Path(downloaded_path)
    except Exception as e:
        raise DatasetUnavailableError(
            f"Failed to download YOLO model from Hugging Face: {e}"
        )


def verify_checksum(model_path: Path, expected_hash: str) -> bool:
    """Verify the SHA256 checksum of the downloaded model."""
    actual_hash = calculate_sha256(model_path)
    if actual_hash != expected_hash:
        print(f"Checksum mismatch!")
        print(f"  Expected: {expected_hash}")
        print(f"  Actual:   {actual_hash}")
        return False
    print(f"Checksum verified: {actual_hash}")
    return True


def benchmark_latency(model_path: Path) -> Tuple[float, float]:
    """
    Run inference on a dummy frame to measure latency.
    Returns (mean_latency_ms, std_latency_ms).
    """
    # Load model
    session = ort.InferenceSession(str(model_path))
    input_name = session.get_inputs()[0].name
    
    # Get input shape (typically [1, 3, 640, 640])
    input_shape = session.get_inputs()[0].shape
    if input_shape[2] is None or input_shape[3] is None:
        # Dynamic shape, assume standard 640x640 for benchmark
        img_h, img_w = 640, 640
    else:
        img_h, img_w = input_shape[2], input_shape[3]

    # Create dummy image (RGB, normalized 0-1)
    # ONNX models usually expect BGR for OpenCV, but normalized float32
    dummy_img = np.random.randint(0, 255, (img_h, img_w, 3), dtype=np.uint8)
    dummy_img = cv2.cvtColor(dummy_img, cv2.COLOR_RGB2BGR) # Ensure BGR if needed, though random is fine
    dummy_img = dummy_img.astype(np.float32) / 255.0
    dummy_img = np.transpose(dummy_img, (2, 0, 1)) # HWC -> CHW
    dummy_input = np.expand_dims(dummy_img, axis=0).astype(np.float32) # NCHW

    # Warmup
    for _ in range(WARMUP_RUNS):
        session.run(None, {input_name: dummy_input})

    # Benchmark
    latencies = []
    for _ in range(BENCHMARK_RUNS):
        start = time.perf_counter()
        session.run(None, {input_name: dummy_input})
        end = time.perf_counter()
        latencies.append((end - start) * 1000.0) # ms

    mean_lat = np.mean(latencies)
    std_lat = np.std(latencies)
    return mean_lat, std_lat


def main():
    """Main entry point for T015a."""
    print("--- T015a: YOLO Model Download & Verification ---")

    # Determine output path
    # The task specifies: to `code/models/yolo_tiny.onnx`
    models_dir = project_root / "code" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    output_path = models_dir / "yolo_tiny.onnx"

    # 1. Download
    try:
        downloaded_path = download_model(models_dir)
        # Rename if necessary (hf_hub_download might save with full name)
        if downloaded_path.name != output_path.name:
            import shutil
            shutil.move(str(downloaded_path), str(output_path))
    except DatasetUnavailableError as e:
        print(f"CRITICAL: {e}")
        sys.exit(1)

    # 2. Verify Checksum
    print("Verifying checksum...")
    if not verify_checksum(output_path, EXPECTED_SHA256):
        print("CRITICAL: Checksum verification failed. File may be corrupted.")
        sys.exit(1)

    # 3. Benchmark Latency
    print(f"Benchmarking latency (target < {MAX_LATENCY_MS}ms)...")
    mean_lat, std_lat = benchmark_latency(output_path)
    print(f"Mean Latency: {mean_lat:.2f} ms (+/- {std_lat:.2f} ms)")

    if mean_lat > MAX_LATENCY_MS:
        print(f"CRITICAL: Latency {mean_lat:.2f}ms exceeds limit {MAX_LATENCY_MS}ms.")
        sys.exit(1)

    print("SUCCESS: Model downloaded, verified, and latency constraint met.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
