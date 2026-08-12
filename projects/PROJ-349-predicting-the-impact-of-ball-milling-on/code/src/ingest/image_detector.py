"""
Image detection logic to identify PSD curves/images in PDFs.

Algorithm:
1. Convert PDF pages to images using pdf2image.
2. Use cv2.Canny with thresholds (low=50, high=150).
3. Use cv2.findContours to detect edges.
4. Flag a page as containing a PSD image if:
   - Number of contours > 10
   - Aspect ratio of the bounding box is within [0.5, 2.0]
"""
import json
import logging
import os
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
from pdf2image import convert_from_path

from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)


def detect_psd_images(pdf_path: str) -> List[str]:
    """
    Detect pages in a PDF that likely contain PSD curves/images.

    Args:
        pdf_path: Path to the input PDF file.

    Returns:
        A list of strings representing the paths to the detected image files (PNG).
        The image files are saved to data/raw/detected_images/ with filenames like
        <original_name>_page_<page_num>.png.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        RuntimeError: If pdf2image or cv2 fails to process the file.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Ensure output directory exists
    output_dir = Path("data/raw/detected_images")
    output_dir.mkdir(parents=True, exist_ok=True)

    detected_pages = []

    try:
        # Convert PDF to images (DPI 150 is a balance between quality and speed)
        logger.info(f"Converting PDF {pdf_path} to images...")
        images = convert_from_path(str(pdf_path), dpi=150)
    except Exception as e:
        logger.error(f"Failed to convert PDF {pdf_path} to images: {e}")
        raise RuntimeError(f"PDF conversion failed: {e}")

    base_name = pdf_path.stem

    for page_idx, image in enumerate(images):
        # Convert PIL Image to OpenCV format (numpy array)
        # PIL is RGB, OpenCV expects BGR for some operations, but Canny works on grayscale
        # We convert to grayscale directly
        img_cv = np.array(image)
        if img_cv.ndim == 3:
            # Convert RGB to Grayscale
            img_gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
        else:
            img_gray = img_cv

        # Apply Canny edge detection
        # Thresholds: low=50, high=150 as per spec
        edges = cv2.Canny(img_gray, 50, 150)

        # Find contours
        # RETR_EXTERNAL retrieves only the extreme outer contours
        # CHAIN_APPROX_SIMPLE compresses horizontal, vertical, and diagonal segments
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours based on criteria
        is_psd_page = False
        page_contours_count = 0

        for contour in contours:
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)

            # Skip very small contours (noise)
            if w < 10 or h < 10:
                continue

            page_contours_count += 1

            # Calculate aspect ratio
            aspect_ratio = float(w) / h if h > 0 else 0

            # Check criteria:
            # 1. Number of contours > 10 (accumulated check below)
            # 2. Aspect ratio within [0.5, 2.0]
            # We flag the page if we find *at least one* contour that meets the aspect ratio
            # AND the total count of significant contours is > 10.
            # However, the spec says "Flag a page ... if the number of contours > 10 AND ... aspect ratio".
            # This implies the aspect ratio check might apply to the dominant contour or the average.
            # Interpretation: If the page has > 10 contours, AND the bounding box of the *largest* or *aggregate*
            # shape (or perhaps the page itself if treated as one) fits the ratio.
            # Given the ambiguity, a robust heuristic for "PSD curve" (which is usually a plot)
            # is that the plot area (or the main figure) has a reasonable aspect ratio.
            # Let's check if ANY significant contour has the correct aspect ratio,
            # provided the total count of significant contours is > 10.

            if 0.5 <= aspect_ratio <= 2.0:
                # We found a candidate shape with good aspect ratio
                # We need to ensure the total count of contours is > 10
                pass

        # Re-evaluating the logic: "Flag a page ... if the number of contours > 10 AND the aspect ratio ... is within [0.5, 2.0]"
        # This likely means: Count all valid contours. If count > 10, check the aspect ratio of the *main* content.
        # Or, check if the *total* bounding box of all contours fits.
        # Let's try: If count > 10, calculate the bounding box of the union of all significant contours.
        # If that union's aspect ratio is in range, flag it.

        significant_contours = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 10 and h > 10:
                significant_contours.append(contour)

        if len(significant_contours) > 10:
            # Calculate the bounding box of the union of all significant contours
            all_points = []
            for contour in significant_contours:
                for point in contour:
                    all_points.append(point)

            if all_points:
                all_points = np.array(all_points, dtype=np.int32)
                x, y, w, h = cv2.boundingRect(all_points)

                if h > 0:
                    aspect_ratio = float(w) / h
                    if 0.5 <= aspect_ratio <= 2.0:
                        is_psd_page = True

        if is_psd_page:
            # Save the page as an image
            # Convert back to PIL for saving
            output_path = output_dir / f"{base_name}_page_{page_idx + 1}.png"
            image.save(str(output_path), "PNG")
            detected_pages.append(str(output_path))
            logger.info(f"Detected PSD image on page {page_idx + 1}: {output_path}")

    return detected_pages


def save_detection_results(detected_paths: List[str], output_json_path: str) -> None:
    """
    Save the list of detected image paths to a JSON file.

    Args:
        detected_paths: List of paths to detected images.
        output_json_path: Path to the output JSON file.
    """
    output_path = Path(output_json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(detected_paths, f, indent=2)

    logger.info(f"Saved detection results to {output_path}")


def run_image_detection_pipeline(pdf_paths: List[str], output_json_path: str = "data/raw/detected_psd_images.json") -> List[str]:
    """
    Run the image detection pipeline on a list of PDF files.

    Args:
        pdf_paths: List of paths to PDF files.
        output_json_path: Path to the output JSON file.

    Returns:
        A list of all detected image paths.
    """
    all_detected = []

    for pdf_path in pdf_paths:
        try:
            detected = detect_psd_images(pdf_path)
            all_detected.extend(detected)
        except Exception as e:
            logger.error(f"Skipping {pdf_path} due to error: {e}")
            continue

    save_detection_results(all_detected, output_json_path)
    return all_detected


if __name__ == "__main__":
    import sys

    # If run directly, expect a PDF path or a directory of PDFs
    if len(sys.argv) < 2:
        print("Usage: python -m src.ingest.image_detector <pdf_path> [pdf_path2 ...]")
        sys.exit(1)

    pdf_files = sys.argv[1:]
    run_image_detection_pipeline(pdf_files)
