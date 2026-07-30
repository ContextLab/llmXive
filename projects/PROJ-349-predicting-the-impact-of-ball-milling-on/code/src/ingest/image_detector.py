"""
Image detection module for identifying PSD curves/images in PDFs.
Implements T014a: Detect PSD images using Canny edge detection and contour analysis.
"""

import json
import logging
import os
import cv2
import numpy as np
from pathlib import Path
from typing import List
from pdf2image import convert_from_path

from src.utils.logger import get_module_logger

# Initialize logger
logger = get_module_logger(__name__)

# Constants for detection
CANNY_LOW_THRESHOLD = 50
CANNY_HIGH_THRESHOLD = 150
MIN_CONTOURS = 10
ASPECT_RATIO_MIN = 0.5
ASPECT_RATIO_MAX = 2.0

def detect_psd_images(pdf_path: str) -> List[str]:
    """
    Detect PSD curves/images in a PDF file.

    Algorithm:
    1. Convert PDF pages to images using pdf2image.
    2. For each page, apply Canny edge detection.
    3. Find contours and analyze bounding boxes.
    4. Flag a page as containing a PSD image if:
       - Number of contours > MIN_CONTOURS
       - Aspect ratio of the largest bounding box is within [0.5, 2.0]

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        List[str]: List of image paths (PNG files) saved for detected PSD images.
    """
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return []

    logger.info(f"Processing PDF: {pdf_path}")

    try:
        # Convert PDF to images (DPI=200 for good resolution)
        images = convert_from_path(pdf_path, dpi=200)
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        return []

    detected_images = []
    output_dir = Path("data/raw/detected_images")
    output_dir.mkdir(parents=True, exist_ok=True)

    for page_num, image in enumerate(images):
        # Convert PIL image to OpenCV format (numpy array)
        img_cv = np.array(image)
        # Convert RGB to BGR for OpenCV
        if len(img_cv.shape) == 3 and img_cv.shape[2] == 3:
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
        elif len(img_cv.shape) == 3 and img_cv.shape[2] == 4:
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGBA2BGR)

        # Convert to grayscale
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Canny edge detection
        edges = cv2.Canny(blurred, CANNY_LOW_THRESHOLD, CANNY_HIGH_THRESHOLD)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Analyze contours
        if len(contours) > MIN_CONTOURS:
            # Find the largest contour by area
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)

            # Calculate aspect ratio
            if w > 0 and h > 0:
                aspect_ratio = w / h
                logger.debug(f"Page {page_num + 1}: Contours={len(contours)}, "
                             f"Aspect Ratio={aspect_ratio:.2f} (Range: {ASPECT_RATIO_MIN}-{ASPECT_RATIO_MAX})")

                if ASPECT_RATIO_MIN <= aspect_ratio <= ASPECT_RATIO_MAX:
                    # Save the detected image
                    output_path = output_dir / f"{Path(pdf_path).stem}_page{page_num + 1}.png"
                    cv2.imwrite(str(output_path), img_cv)
                    detected_images.append(str(output_path))
                    logger.info(f"Detected PSD image on page {page_num + 1}: {output_path}")
                else:
                    logger.debug(f"Page {page_num + 1}: Aspect ratio {aspect_ratio:.2f} out of range, skipped.")
            else:
                logger.debug(f"Page {page_num + 1}: Invalid dimensions (w={w}, h={h}), skipped.")
        else:
            logger.debug(f"Page {page_num + 1}: Contour count {len(contours)} <= {MIN_CONTOURS}, skipped.")

    logger.info(f"Total PSD images detected: {len(detected_images)}")
    return detected_images

def save_detection_results(pdf_path: str, detected_images: List[str], output_json_path: str):
    """
    Save detection results to a JSON file.

    Args:
        pdf_path (str): Path to the source PDF.
        detected_images (List[str]): List of detected image paths.
        output_json_path (str): Path to the output JSON file.
    """
    results = {
        "source_pdf": pdf_path,
        "detected_images": detected_images,
        "count": len(detected_images)
    }

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Saved detection results to {output_json_path}")

def run_image_detection_pipeline(pdf_dir: str = "data/raw/pdfs", output_json: str = "data/raw/detected_psd_images.json"):
    """
    Run the image detection pipeline on all PDFs in a directory.

    Args:
        pdf_dir (str): Directory containing PDF files.
        output_json (str): Path to the output JSON file.
    """
    pdf_dir_path = Path(pdf_dir)
    if not pdf_dir_path.exists():
        logger.warning(f"PDF directory not found: {pdf_dir}. Skipping detection.")
        # Create empty output if no PDFs found
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump({"source_directory": pdf_dir, "detected_images": [], "total_pdfs": 0}, f, indent=2)
        return

    pdf_files = list(pdf_dir_path.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {pdf_dir}.")
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump({"source_directory": pdf_dir, "detected_images": [], "total_pdfs": 0}, f, indent=2)
        return

    all_detected_images = []
    logger.info(f"Found {len(pdf_files)} PDFs to process.")

    for pdf_file in pdf_files:
        try:
            detected = detect_psd_images(str(pdf_file))
            all_detected_images.extend(detected)
        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {e}")

    save_detection_results(
        pdf_dir,
        all_detected_images,
        output_json
    )

    logger.info(f"Pipeline complete. Total images detected: {len(all_detected_images)}")

if __name__ == "__main__":
    # Default execution path
    run_image_detection_pipeline()
