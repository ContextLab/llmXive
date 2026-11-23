"""
Dense baseline acquisition (T016b).

Strategy (per task description):
1. STRICTLY attempt to download the pre-computed dense baseline from the
   HuggingFace hub (repo ``realestate10k/dense_baseline_v1``).
2. If (and only if) that download fails, automatically GENERATE a real
   dense baseline by running the MiDaS_small monocular depth model
   (validated standard model per spec Assumptions) on real photographic
   frames, entirely on CPU.

The output is always written to ``data/raw/dense_baseline_frames.npy``
together with a sidecar provenance JSON recording the exact source,
SHA-256 checksum, model and frame provenance. No synthetic / random data
is ever produced: every pixel of the baseline comes either from the
downloaded artifact or from a real depth-model inference on real frames.
"""
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

CODE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = CODE_DIR.parent
for _p in (str(CODE_DIR), str(PROJECT_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from config import get_raw_dir, ensure_directories  # noqa: E402

TARGET_FILENAME = "dense_baseline_frames.npy"
PROVENANCE_FILENAME = "dense_baseline_provenance.json"
NUM_FRAMES = 16
OUTPUT_SIZE = 256
HF_REPO_ID = "realestate10k/dense_baseline_v1"
HF_DATASET_CANDIDATES = [
    "Falah/RealEstate10K-dataset",
    "nateraw/realestate10k",
]
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}


def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def try_hf_download(target: Path) -> bool:
    """Attempt to download the pre-computed baseline from HuggingFace.

    Returns True on success (file written to ``target``), False if the
    official source is unavailable or returns an error.
    """
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("[dense-baseline] huggingface_hub not installed; "
              "cannot attempt hub download.")
        return False
    try:
        path = hf_hub_download(
            repo_id=HF_REPO_ID, filename=TARGET_FILENAME, repo_type="dataset"
        )
    except Exception as exc:  # any hub error -> documented fallback
        print(f"[dense-baseline] Hub download failed "
              f"({type(exc).__name__}: {exc}).")
        return False
    try:
        arr = np.load(path)
        np.save(target, arr.astype(np.float32))
        print(f"[dense-baseline] Downloaded official baseline from "
              f"{HF_REPO_ID}.")
        return True
    except Exception as exc:
        print(f"[dense-baseline] Downloaded file could not be loaded as "
              f"an .npy array ({exc}).")
        return False


def _local_frames(n: int) -> List[Tuple[np.ndarray, str]]:
    """Collect real frames already downloaded under data/ (if any)."""
    import cv2
    found: List[Tuple[np.ndarray, str]] = []
    for sub in ("raw", "stratified", "processed"):
        base = PROJECT_ROOT / "data" / sub
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if p.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            img = cv2.imread(str(p))
            if img is None:
                continue
            found.append((
                cv2.cvtColor(img, cv2.COLOR_BGR2RGB),
                f"local:{p.relative_to(PROJECT_ROOT)}",
            ))
            if len(found) >= n:
                return found
    return found


def _hf_stream_frames(n: int) -> List[Tuple[np.ndarray, str]]:
    """Stream real frames from candidate RealEstate10K HF datasets."""
    try:
        from datasets import load_dataset
    except ImportError:
        return []
    for repo in HF_DATASET_CANDIDATES:
        try:
            ds = load_dataset(repo, split="train", streaming=True)
            frames: List[Tuple[np.ndarray, str]] = []
            for row in ds:
                img = row.get("image")
                if img is None:
                    img = next(
                        (v for v in row.values() if hasattr(v, "convert")),
                        None,
                    )
                if img is None:
                    continue
                arr = np.array(img.convert("RGB"))
                frames.append((arr, f"hf-dataset:{repo}"))
                if len(frames) >= n:
                    break
            if frames:
                print(f"[dense-baseline] Using real frames streamed from "
                      f"{repo}.")
                return frames
        except Exception as exc:
            print(f"[dense-baseline] HF dataset {repo} unavailable "
                  f"({type(exc).__name__}: {exc}).")
    return []


def _skimage_frames(n: int) -> List[Tuple[np.ndarray, str]]:
    """Last-resort REAL input frames: scikit-image sample photographs.

    These are real photographs (not synthetic, not random); their use is
    clearly labelled in the provenance file because RealEstate10K frames
    were unavailable at generation time.
    """
    from skimage import data as skdata
    names = ["livingroom", "brick", "text", "camera",
             "coffee", "astronaut", "chelsea"]
    frames: List[Tuple[np.ndarray, str]] = []
    for name in names:
        try:
            img = getattr(skdata, name)()
        except Exception:
            continue
        if img.ndim == 2:
            img = np.stack([img] * 3, axis=-1)
        frames.append((
            img.astype(np.uint8),
            f"scikit-image sample photograph '{name}' (real photograph; "
            f"RealEstate10K frames unavailable)",
        ))
        if len(frames) >= n:
            break
    return frames


def generate_midas_baseline(
    frames: List[Tuple[np.ndarray, str]]
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Run MiDaS_small on CPU over the given real frames.

    Returns the stacked depth maps (float32, N x OUTPUT_SIZE x
    OUTPUT_SIZE) and runtime info. This is a REAL model inference —
    no values are invented.
    """
    import cv2
    import torch

    print("[dense-baseline] Loading MiDaS_small from torch hub (CPU)...")
    model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
    model.to("cpu")
    model.eval()
    midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
    transform = midas_transforms.small_transform

    depths: List[np.ndarray] = []
    t0 = time.time()
    with torch.no_grad():
        for img, _src in frames:
            bgr = cv2.cvtColor(np.ascontiguousarray(img), cv2.COLOR_RGB2BGR)
            inp = transform(bgr)
            prediction = model(inp)
            prediction = torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=OUTPUT_SIZE,
                mode="bicubic",
                align_corners=False,
            ).squeeze()
            depths.append(prediction.cpu().numpy().astype(np.float32))
    runtime = time.time() - t0
    print(f"[dense-baseline] MiDaS inference on {len(frames)} frames "
          f"took {runtime:.2f}s on CPU.")
    return np.stack(depths), {"runtime_seconds": runtime}


def main() -> int:
    raw_dir = get_raw_dir()
    ensure_directories(raw_dir)
    target = raw_dir / TARGET_FILENAME
    provenance: Dict[str, Any] = {
        "task": "T016b",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    if target.exists():
        print(f"[dense-baseline] {target} already exists; "
              f"validating integrity only.")
        provenance["source"] = "pre-existing on disk"
    elif try_hf_download(target):
        # Official source available: DO NOT generate or infer anything.
        provenance["source"] = f"huggingface:{HF_REPO_ID}"
    else:
        # Documented fallback: generate with MiDaS on real frames.
        frames = (
            _local_frames(NUM_FRAMES)
            or _hf_stream_frames(NUM_FRAMES)
            or _skimage_frames(NUM_FRAMES)
        )
        if not frames:
            raise RuntimeError(
                "No real frames available anywhere for MiDaS baseline "
                "generation; refusing to fabricate data."
            )
        arr, info = generate_midas_baseline(frames)
        np.save(target, arr)
        provenance["source"] = (
            "MiDaS_small (torch.hub intel-isl/MiDaS, CPU) inference on "
            "real frames (fallback: official download unavailable)"
        )
        provenance["frame_sources"] = [src for _, src in frames]
        provenance.update(info)

    # Integrity validation (checksum + finite values), always performed.
    provenance["sha256"] = calculate_sha256(target)
    arr_check = np.load(target)
    if arr_check.size == 0:
        raise ValueError("Dense baseline array is empty.")
    if not np.isfinite(arr_check).all():
        raise ValueError("Dense baseline contains non-finite values.")
    provenance["shape"] = list(arr_check.shape)
    provenance["dtype"] = str(arr_check.dtype)

    with open(raw_dir / PROVENANCE_FILENAME, "w") as f:
        json.dump(provenance, f, indent=2)

    print(f"[dense-baseline] Wrote {target} "
          f"shape={arr_check.shape} dtype={arr_check.dtype}")
    print(f"[dense-baseline] sha256={provenance['sha256']}")
    print(f"[dense-baseline] Provenance saved to "
          f"{raw_dir / PROVENANCE_FILENAME}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
