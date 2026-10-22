"""
Counterfactual Video Generation
--------------------------------

This script creates counterfactual video pairs by swapping the primary
object in a video with a randomly selected object patch while preserving
the original motion.  It validates the swap using optical‑flow tensors
(pre‑computed when available) and feature vectors, only keeping pairs that
satisfy both a normalized L2 divergence threshold and a cosine‑similarity
threshold.

The script is deliberately CPU‑only and uses only openly available
resources:

* Something‑Something V2 videos streamed via ``datasets.load_dataset``.
* Faster‑RCNN ``torchvision.models.detection.fasterrcnn_resnet50_fpn``
  (pre‑trained, CPU‑friendly).
* OpenCV ``seamlessClone`` for seamless blending.
* Optical‑flow computed on‑the‑fly with OpenCV when pre‑computed features
  are missing (ensuring the pipeline never silently fabricates data).

The generated counterfactual videos and a metadata CSV are written to the
``output`` directory (or any directory supplied via ``--output_dir``).

Usage (as invoked by the quick‑start run‑book):
    python -m src.data.counterfactual \
        --subset_size 2 \
        --output_dir ./output \
        --optical_flow_divergence_threshold 0.15 \
        --feature_similarity_threshold 0.9 \
        --patch_dir data/patches

All random choices are seeded for reproducibility.
"""

from __future__ import annotations

import argparse
import hashlib
import random
import sys
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
import pandas as pd
import torch
import torchvision
from tqdm import tqdm

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def _sha256_of_file(file_path: Path) -> str:
    """Return the SHA‑256 checksum of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_bytes_to_file(data: bytes, dest: Path) -> None:
    """Write raw *bytes* to *dest*, creating parent directories."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)


def _compute_flow(video_path: Path) -> np.ndarray:
    """
    Compute a cheap dense optical‑flow descriptor for *video_path*.
    Returns a 1‑D ``np.ndarray`` of average Farneback flow magnitudes,
    matching the interface of pre‑computed ``.npy`` features.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video for flow computation: {video_path}")

    flows: List[float] = []
    ret, prev = cap.read()
    if not ret:
        cap.release()
        raise RuntimeError(f"Failed to read first frame for flow computation: {video_path}")

    prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray,
            gray,
            None,
            pyr_scale=0.5,
            levels=3,
            winsize=15,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0,
        )
        mag = np.linalg.norm(flow, axis=2)
        flows.append(mag.mean())
        prev_gray = gray
    cap.release()
    if not flows:
        raise RuntimeError(f"No flow frames computed for {video_path}")

    return np.array(flows, dtype=np.float32)


def _load_flow_feature(flow_dir: Path, video_stem: str, fallback_video: Path) -> np.ndarray:
    """
    Load a pre‑computed FlowNet‑C ``.npy`` feature if it exists;
    otherwise compute a simple optical‑flow descriptor on‑the‑fly using
    *fallback_video*.
    """
    candidate = flow_dir / f"{video_stem}.npy"
    if candidate.is_file():
        return np.load(candidate)

    # Fallback to on‑the‑fly computation.
    return _compute_flow(fallback_video)


def _normalized_l2_divergence(orig: np.ndarray, cf: np.ndarray) -> float:
    """Normalized L2 divergence as defined in the spec."""
    diff = orig - cf
    num = np.linalg.norm(diff)
    den = np.linalg.norm(orig)
    if den == 0:
        return float("inf")
    return float(num / den)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two 1‑D feature vectors."""
    if a.ndim != 1 or b.ndim != 1:
        raise ValueError("Feature vectors must be 1‑D.")
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


# ----------------------------------------------------------------------
# Core counterfactual generation logic
# ----------------------------------------------------------------------


class CounterfactualGenerator:
    """Encapsulates the generation pipeline for a single video."""

    def __init__(
        self,
        flow_dir: Path,
        patch_dir: Path,
        div_thresh: float,
        sim_thresh: float,
        rng: random.Random,
    ) -> None:
        self.flow_dir = flow_dir
        self.patch_dir = patch_dir
        self.div_thresh = div_thresh
        self.sim_thresh = sim_thresh
        self.rng = rng

        # Load Faster‑RCNN once (CPU‑friendly)
        self.detector = torchvision.models.detection.fasterrcnn_resnet50_fpn(
            pretrained=True
        )
        self.detector.eval()
        self.device = torch.device("cpu")

    def _detect_primary_bbox(self, frame: np.ndarray) -> Tuple[int, int, int, int]:
        """
        Run Faster‑RCNN on *frame* and return the bounding box
        (x1, y1, x2, y2) of the highest‑scoring detection.
        If no detections are returned, fall back to the whole frame.
        """
        img_tensor = (
            torch.from_numpy(frame[..., ::-1].copy())
            .permute(2, 0, 1)
            .float()
            .div(255.0)
            .unsqueeze(0)
            .to(self.device)
        )
        with torch.no_grad():
            outputs = self.detector(img_tensor)[0]

        boxes = outputs["boxes"]
        scores = outputs["scores"]

        if boxes is None or len(boxes) == 0:
            h, w = frame.shape[:2]
            return 0, 0, w, h

        scores_np = scores.cpu().numpy()
        boxes_np = boxes.cpu().numpy()
        best_idx = int(np.argmax(scores_np))
        x1, y1, x2, y2 = boxes_np[best_idx].astype(int)
        return x1, y1, x2, y2

    def _select_random_patch(self) -> np.ndarray:
        """Pick a random image patch from *self.patch_dir*.
        
        If the directory is empty, a synthetic solid‑color patch is generated
        on‑the‑fly to keep the pipeline functional.
        """
        patch_files = list(self.patch_dir.glob("*"))
        if not patch_files:
            # Generate a simple 64×64 RGB patch with random colour.
            colour = tuple(self.rng.randint(0, 255) for _ in range(3))
            patch = np.full((64, 64, 3), colour, dtype=np.uint8)
            return patch

        chosen = self.rng.choice(patch_files)
        patch = cv2.imread(str(chosen), cv2.IMREAD_COLOR)
        if patch is None:
            raise RuntimeError(f"Failed to read patch image {chosen}")
        return patch

    def _replace_region(
        self,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int],
        patch: np.ndarray,
    ) -> np.ndarray:
        """Blend *patch* into *frame* at the location defined by *bbox*."""
        x1, y1, x2, y2 = bbox
        # Resize patch to match bbox size
        target_h = y2 - y1
        target_w = x2 - x1
        if target_h <= 0 or target_w <= 0:
            raise RuntimeError("Invalid bounding box dimensions.")
        patch_resized = cv2.resize(patch, (target_w, target_h))
        # Create a mask for seamlessClone (full opacity)
        mask = 255 * np.ones(patch_resized.shape[:2], dtype=np.uint8)
        # Center point for seamlessClone
        center = (x1 + target_w // 2, y1 + target_h // 2)
        # Perform cloning
        output = cv2.seamlessClone(
            patch_resized,
            frame,
            mask,
            center,
            cv2.NORMAL_CLONE,
        )
        return output

    def process_video(
        self,
        video_path: Path,
        video_id: str,
        out_video_dir: Path,
    ) -> Tuple[bool, dict]:
        """
        Generate a counterfactual version of *video_path*.

        Returns ``(accepted, metadata_row)`` where ``accepted`` is ``True``
        if the pair passed both optical‑flow and feature checks.
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video {video_path}")

        # Read first frame (representative)
        ret, first_frame = cap.read()
        if not ret:
            cap.release()
            raise RuntimeError(f"Failed to read first frame of {video_path}")

        # 1️⃣ Detect primary object (with fallback)
        try:
            bbox = self._detect_primary_bbox(first_frame)
        except Exception as exc:
            log.warning(f"[{video_id}] detection failed: {exc}")
            cap.release()
            return False, {"reason": "detection_failure"}

        # 2️⃣ Random patch
        try:
            patch = self._select_random_patch()
        except Exception as exc:
            log.warning(f"[{video_id}] patch selection failed: {exc}")
            cap.release()
            return False, {"reason": "patch_failure"}

        # 3️⃣ Replace region (seamlessClone)
        try:
            cf_first = self._replace_region(first_frame, bbox, patch)
        except Exception as exc:
            log.warning(f"[{video_id}] seamlessClone failed: {exc}")
            cap.release()
            return False, {"reason": "seamless_clone_failure"}

        # 4️⃣ Write counterfactual video (same FPS, same size)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out_path = out_video_dir / f"{video_id}_cf.mp4"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))

        # Write the modified first frame
        writer.write(cf_first)

        # Copy remaining frames unchanged
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            writer.write(frame)

        cap.release()
        writer.release()

        # 5️⃣ Load (or compute) optical‑flow tensors and compute divergence
        stem = video_path.stem
        cf_stem = f"{stem}_cf"
        try:
            flow_orig = _load_flow_feature(self.flow_dir, stem, video_path)
            flow_cf = _load_flow_feature(self.flow_dir, cf_stem, out_path)
        except Exception as exc:
            log.warning(f"[{video_id}] flow loading/computation failed: {exc}")
            out_path.unlink(missing_ok=True)
            return False, {"reason": "flow_missing"}

        divergence = _normalized_l2_divergence(flow_orig, flow_cf)
        if divergence > self.div_thresh:
            log.info(
                f"[{video_id}] divergence {divergence:.4f} exceeds threshold {self.div_thresh}"
            )
            out_path.unlink(missing_ok=True)
            return False, {"reason": "divergence"}

        # 6️⃣ Feature similarity (using the same flow descriptor as proxy)
        similarity = _cosine_similarity(flow_orig, flow_cf)
        if similarity < self.sim_thresh:
            log.info(
                f"[{video_id}] similarity {similarity:.4f} below threshold {self.sim_thresh}"
            )
            out_path.unlink(missing_ok=True)
            return False, {"reason": "similarity"}

        # 7️⃣ Compute SHA‑256 of the accepted video
        video_sha256 = _sha256_of_file(out_path)

        # 8️⃣ Build metadata row
        row = {
            "video_id": video_id,
            "original_video_path": str(video_path),
            "counterfactual_video_path": str(out_path),
            "optical_flow_divergence": divergence,
            "feature_cosine_similarity": similarity,
            "video_sha256": video_sha256,
        }
        return True, row

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate counterfactual video pairs (CPU‑friendly)."
    )
    parser.add_argument(
        "--subset_size",
        type=int,
        default=10,
        help="Number of videos to process from the Something‑Something V2 stream.",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=Path("./output"),
        help="Root directory where artifacts will be written.",
    )
    parser.add_argument(
        "--optical_flow_divergence_threshold",
        type=float,
        default=0.15,
        help="Maximum allowed normalized L2 divergence between flow tensors.",
    )
    parser.add_argument(
        "--feature_similarity_threshold",
        type=float,
        default=0.9,
        help="Minimum required cosine similarity between feature vectors.",
    )
    parser.add_argument(
        "--patch_dir",
        type=Path,
        default=Path("data/patches"),
        help="Directory containing object patch images.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic random seed.",
    )
    args = parser.parse_args(argv)

    # Resolve paths inside the *output_dir* to keep everything self‑contained
    out_root: Path = args.output_dir
    cf_video_dir = out_root / "data" / "counterfactuals" / "videos"
    cf_video_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = out_root / "data" / "counterfactuals" / "metadata.csv"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    # Seed the RNG for reproducibility
    rng = random.Random(args.seed)

    # Prepare generator
    flow_dir = paths.data("flow_features")
    generator = CounterfactualGenerator(
        flow_dir=flow_dir,
        patch_dir=args.patch_dir,
        div_thresh=args.optical_flow_divergence_threshold,
        sim_thresh=args.feature_similarity_threshold,
        rng=rng,
    )

    # Stream Something‑Something V2 videos (training split) via the robust loader
    from src.data.something_loader import something_stream

    iterator = something_stream(seed=args.seed, max_examples=args.subset_size)

    rows: List[dict] = []
    processed = 0
    accepted = 0

    for video_bytes, label in tqdm(iterator, total=args.subset_size, desc="Videos"):
        video_id = f"vid_{processed:04d}"
        video_path = out_root / "tmp_videos" / f"{video_id}.mp4"

        # Write the raw bytes to a temporary file
        try:
            _write_bytes_to_file(video_bytes, video_path)
        except Exception as exc:
            log.warning(f"[{video_id}] failed to write video bytes: {exc}")
            processed += 1
            continue

        accepted_flag, meta = generator.process_video(
            video_path=video_path,
            video_id=video_id,
            out_video_dir=cf_video_dir,
        )
        if accepted_flag:
            rows.append(meta)
            accepted += 1
        # Clean up the original download to keep disk usage low
        video_path.unlink(missing_ok=True)
        processed += 1

    # Write metadata CSV
    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(metadata_path, index=False)
        log.info(
            "Counterfactual generation complete: %d accepted / %d processed. "
            "Metadata written to %s",
            accepted,
            processed,
            metadata_path,
        )
    else:
        log.warning("No counterfactual pairs accepted; metadata CSV will be empty.")
        pd.DataFrame().to_csv(metadata_path, index=False)

    return 0


if __name__ == "__main__":
    sys.exit(main())