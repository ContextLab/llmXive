"""
Segment semantic ROI masks for faces (using YOLOv8) and weapons (using Detectron2).

The script follows the specification for task T004:
- Looks for existing masks under ``data/raw/ds003123/masks/``.
  If found, they are copied to ``data/interim/masks/`` and provenance is recorded.
- If masks are missing, the script runs:
    * YOLOv8 (``yolov8n.pt``) to detect faces (treated as ``person`` class).
    * Detectron2 (Mask R-CNN pretrained on COCO) to detect weapons.
  Both detectors use a confidence threshold of 0.85.
- For each stimulus image a binary PNG mask is saved:
  ``<stimulus_id>_face.png`` and ``<stimulus_id>_weapon.png``.
- Images with no detections or low‑confidence detections are logged to
  ``data/interim/flagged_images.csv`` and also recorded in
  ``data/interim/detection_metadata.json``. Each metadata entry now includes
  a ``detector_used`` field indicating which detector produced the mask.
- All provenance (copied masks) is saved to ``data/interim/mask_provenance.json``.
- The script exits with status 0 on success; any unexpected exception aborts
  with a clear error (no silent fall‑backs or synthetic data).

The module can be executed as ``python -m code.eye_tracking.segment_roi``.
"""
import json
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any

import cv2
import numpy as np

from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
CONFIDENCE_THRESHOLD = 0.85
WEAPON_CLASS_KEYWORDS = {"knife", "gun", "sword", "weapon", "rifle", "pistol"}

# ----------------------------------------------------------------------
# Lazy import helpers
# ----------------------------------------------------------------------
def _load_yolo_model() -> Any:
    """
    Load the YOLOv8 nano model (CPU‑only). The model will be downloaded
    automatically on first use.
    """
    try:
        # Import inside the function to keep the module import‑time lightweight
        from ultralytics import YOLO
    except Exception as exc:
        logger.error(f"Failed to import YOLOv8 library: {exc}")
        raise RuntimeError("YOLOv8 library is not available.") from exc

    try:
        model = YOLO("yolov8n.pt")
        logger.info("YOLOv8 model loaded successfully.")
        return model
    except Exception as exc:
        logger.error(f"Failed to load YOLOv8 model: {exc}")
        raise RuntimeError("YOLOv8 model loading failed.") from exc

def _load_detectron2_predictor() -> Any:
    """
    Load a Detectron2 Mask R‑CNN model pretrained on COCO.
    Returns a ``DefaultPredictor`` configured for inference on CPU.
    """
    try:
        # Import Detectron2 components lazily
        from detectron2.engine import DefaultPredictor
        from detectron2.config import get_cfg
        from detectron2 import model_zoo
    except Exception as exc:
        logger.error(f"Failed to import Detectron2 library: {exc}")
        raise RuntimeError("Detectron2 library is not available.") from exc

    try:
        cfg = get_cfg()
        cfg.merge_from_file(
            model_zoo.get_config_file(
                "COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"
            )
        )
        cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(
            "COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"
        )
        cfg.MODEL.DEVICE = "cpu"
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = CONFIDENCE_THRESHOLD
        predictor = DefaultPredictor(cfg)
        logger.info("Detectron2 model loaded successfully.")
        return predictor
    except Exception as exc:
        logger.error(f"Failed to load Detectron2 model: {exc}")
        raise RuntimeError("Detectron2 model loading failed.") from exc

# ----------------------------------------------------------------------
# Utility functions
# ----------------------------------------------------------------------
def _create_empty_mask(shape: tuple) -> np.ndarray:
    """Return an all‑zero binary mask with the given (height, width)."""
    return np.zeros(shape, dtype=np.uint8)

def _save_mask(mask: np.ndarray, out_path: Path) -> None:
    """Write a binary mask as a PNG file, ensuring parent directories exist."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Ensure mask is uint8 with values 0 or 255
    mask_to_save = (mask > 0).astype(np.uint8) * 255
    cv2.imwrite(str(out_path), mask_to_save)

def _record_detection(
    metadata: List[Dict],
    stimulus_id: str,
    roi_type: str,
    num_detections: int,
    mean_confidence: Optional[float],
    detector_used: str,
) -> None:
    """Append a detection‑metadata entry, now including the detector name."""
    entry = {
        "stimulus_id": stimulus_id,
        "roi_type": roi_type,
        "num_detections": num_detections,
        "mean_confidence": mean_confidence,
        "detector_used": detector_used,
    }
    metadata.append(entry)

# ----------------------------------------------------------------------
# Core processing functions
# ----------------------------------------------------------------------
def _process_image_with_yolo(
    model: Any, image_path: Path, stimulus_id: str
) -> (np.ndarray, int, Optional[float]):
    """
    Run YOLOv8 on ``image_path`` and produce a binary face mask.

    Returns:
        mask (np.ndarray), number of detections, mean confidence (or None).
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Unable to read image {image_path}")

    results = model(str(image_path))
    # ``results`` is a list with a single Results object for our single image
    detections = results[0].boxes
    if detections is None or len(detections) == 0:
        # No detections → empty mask
        empty_mask = _create_empty_mask(img.shape[:2])
        return empty_mask, 0, None

    # YOLOv8 class names (COCO). We treat class id 0 ("person") as a proxy for "face".
    person_class_id = 0
    mask = _create_empty_mask(img.shape[:2])
    confidences = []

    for box, cls, conf in zip(
        detections.xyxy.cpu().numpy(),
        detections.cls.cpu().numpy(),
        detections.conf.cpu().numpy(),
    ):
        if int(cls) != person_class_id:
            continue
        if conf < CONFIDENCE_THRESHOLD:
            continue
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(mask, (x1, y1), (x2, y2), color=1, thickness=-1)
        confidences.append(float(conf))

    if not confidences:
        # All detections filtered out by confidence
        return _create_empty_mask(img.shape[:2]), 0, None

    mean_conf = sum(confidences) / len(confidences)
    return mask, len(confidences), mean_conf

def _process_image_with_detectron2(
    predictor: Any, image_path: Path, stimulus_id: str
) -> (np.ndarray, int, Optional[float]):
    """
    Run Detectron2 on ``image_path`` and produce a binary weapon mask.

    Returns:
        mask (np.ndarray), number of detections, mean confidence (or None).
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Unable to read image {image_path}")

    outputs = predictor(img)
    instances = outputs["instances"]
    if not instances.has("pred_classes"):
        return _create_empty_mask(img.shape[:2]), 0, None

    pred_classes = instances.pred_classes.cpu().numpy()
    scores = instances.scores.cpu().numpy()
    # Get class names from COCO metadata
    from detectron2.data import MetadataCatalog  # Imported lazily above
    metadata = MetadataCatalog.get("coco_2017_train")
    class_names = metadata.thing_classes

    mask = _create_empty_mask(img.shape[:2])
    confidences = []

    for idx, class_id in enumerate(pred_classes):
        class_name = class_names[class_id].lower()
        if not any(keyword in class_name for keyword in WEAPON_CLASS_KEYWORDS):
            continue
        conf = float(scores[idx])
        if conf < CONFIDENCE_THRESHOLD:
            continue
        # Prefer instance masks if available
        if instances.has("pred_masks"):
            pred_mask = instances.pred_masks[idx].cpu().numpy()
            mask = np.logical_or(mask, pred_mask)
        else:
            # Fallback to bounding box
            bbox = instances.pred_boxes[idx].tensor.cpu().numpy()[0]
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(mask, (x1, y1), (x2, y2), color=1, thickness=-1)
        confidences.append(conf)

    if not confidences:
        return _create_empty_mask(img.shape[:2]), 0, None

    mean_conf = sum(confidences) / len(confidences)
    return mask.astype(np.uint8), len(confidences), mean_conf

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> int:
    """
    Entry point for the ROI‑segmentation task.

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = failure).
    """
    try:
        # ------------------------------------------------------------------
        # Define key paths
        # ------------------------------------------------------------------
        raw_masks_dir = paths.data("raw", "ds003123", "masks")
        raw_stimuli_dir = paths.data("raw", "ds003123", "stimuli")
        interim_masks_dir = paths.interim("masks")
        provenance_path = paths.interim("mask_provenance.json")
        detection_meta_path = paths.interim("detection_metadata.json")
        flagged_csv_path = paths.interim("flagged_images.csv")

        # Ensure output directories exist
        interim_masks_dir.mkdir(parents=True, exist_ok=True)

        # ------------------------------------------------------------------
        # 1️⃣  Check for pre‑existing masks
        # ------------------------------------------------------------------
        preexisting_masks = list(raw_masks_dir.glob("*.png"))
        if preexisting_masks:
            logger.info(
                f"Found {len(preexisting_masks)} pre‑existing mask(s). Copying to interim."
            )
            provenance: List[Dict] = []
            for src_path in preexisting_masks:
                dst_path = interim_masks_dir / src_path.name
                shutil.copy2(src_path, dst_path)
                provenance.append(
                    {"source": str(src_path), "destination": str(dst_path)}
                )
            # Write provenance JSON
            provenance_path.parent.mkdir(parents=True, exist_ok=True)
            with open(provenance_path, "w", encoding="utf-8") as f:
                json.dump(provenance, f, indent=2)
            logger.info(f"Mask provenance written to {provenance_path}")
            # No further processing required
            return 0

        # ------------------------------------------------------------------
        # 2️⃣  No pre‑existing masks → run detectors
        # ------------------------------------------------------------------
        logger.info("No pre‑existing masks found. Running YOLOv8 and Detectron2.")
        yolo_model = _load_yolo_model()
        detectron_predictor = _load_detectron2_predictor()

        # Gather stimulus images
        image_paths = sorted(
            [
                p
                for ext in ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tif", "*.tiff")
                for p in raw_stimuli_dir.glob(ext)
            ]
        )
        if not image_paths:
            raise RuntimeError(
                f"No stimulus images found in {raw_stimuli_dir}. "
                "At least one image is required for ROI segmentation."
            )

        detection_metadata: List[Dict] = []
        flagged_rows: List[Dict] = []

        for img_path in image_paths:
            stimulus_id = img_path.stem
            logger.info(f"Processing stimulus {stimulus_id}")

            # ---- Face mask (YOLOv8) ----
            face_mask, face_cnt, face_conf = _process_image_with_yolo(
                yolo_model, img_path, stimulus_id
            )
            face_mask_path = interim_masks_dir / f"{stimulus_id}_face.png"
            _save_mask(face_mask, face_mask_path)

            _record_detection(
                detection_metadata,
                stimulus_id,
                "face",
                face_cnt,
                face_conf,
                detector_used="yolov8",
            )
            if face_cnt == 0:
                flagged_rows.append(
                    {
                        "stimulus_id": stimulus_id,
                        "roi_type": "face",
                        "num_detections": 0,
                        "mean_confidence": None,
                    }
                )

            # ---- Weapon mask (Detectron2) ----
            weapon_mask, weapon_cnt, weapon_conf = _process_image_with_detectron2(
                detectron_predictor, img_path, stimulus_id
            )
            weapon_mask_path = interim_masks_dir / f"{stimulus_id}_weapon.png"
            _save_mask(weapon_mask, weapon_mask_path)

            _record_detection(
                detection_metadata,
                stimulus_id,
                "weapon",
                weapon_cnt,
                weapon_conf,
                detector_used="detectron2",
            )
            if weapon_cnt == 0:
                flagged_rows.append(
                    {
                        "stimulus_id": stimulus_id,
                        "roi_type": "weapon",
                        "num_detections": 0,
                        "mean_confidence": None,
                    }
                )

        # ------------------------------------------------------------------
        # 3️⃣  Write detection metadata JSON
        # ------------------------------------------------------------------
        detection_meta_path.parent.mkdir(parents=True, exist_ok=True)
        with open(detection_meta_path, "w", encoding="utf-8") as f:
            json.dump(detection_metadata, f, indent=2)
        logger.info(f"Detection metadata written to {detection_meta_path}")

        # ------------------------------------------------------------------
        # 4️⃣  Write flagged images CSV
        # ------------------------------------------------------------------
        import pandas as pd

        flagged_df = pd.DataFrame(flagged_rows)
        flagged_csv_path.parent.mkdir(parents=True, exist_ok=True)
        flagged_df.to_csv(flagged_csv_path, index=False)
        logger.info(f"Flagged images written to {flagged_csv_path}")

        logger.info("ROI segmentation completed successfully.")
        return 0

    except Exception as exc:
        logger.exception(f"ROI segmentation terminated with error: {exc}")
        return 1

if __name__ == "__main__":
    import sys

    sys.exit(main())