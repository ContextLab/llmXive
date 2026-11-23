import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import cv2
import easyocr
from src.utils.logger import get_module_logger
from src.exceptions import DataIngestionError

logger = get_module_logger(__name__)

# Initialize OCR reader once
reader = easyocr.Reader(['en'], gpu=False) # gpu=False for safety in restricted envs

def extract_psd_from_image(image_path: str, flagged_entry_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts PSD values from an image using OCR.
    Returns a dict with extracted values or None if extraction fails.
    """
    if not config.get('ocr_enabled', False):
        logger.info(f"OCR disabled for entry {flagged_entry_id}, skipping extraction.")
        return None

    try:
        if not os.path.exists(image_path):
            logger.warning(f"Image not found: {image_path}")
            return None

        # Perform OCR
        results = reader.readtext(image_path)
        text = " ".join([r[1] for r in results])

        # Regex for D10, D50, D90
        import re
        pattern = r'D(10|50|90)[\s:]*([0-9]+(?:\.[0-9]+)?)'
        matches = re.findall(pattern, text, re.IGNORECASE)

        if not matches:
            logger.debug(f"No PSD values found in OCR text for {flagged_entry_id}")
            return None

        data = {
            "experiment_id": flagged_entry_id,
            "source": "ocr_fallback",
            "d10": None,
            "d50": None,
            "d90": None
        }

        for match in matches:
            d_key = f"d{match[0]}"
            try:
                data[d_key] = float(match[1])
            except ValueError:
                continue

        return data

    except Exception as e:
        logger.warning(f"OCR extraction failed for {flagged_entry_id}: {e}")
        return None
