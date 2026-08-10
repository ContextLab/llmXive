"""
Image detection logic to identify PSD curves/images in PDFs.

Algorithm:
1. Convert PDF pages to images using pdf2image.
2. Use cv2.Canny with thresholds (low=50, high=150) to detect edges.
3. Use cv2.findContours to find shapes.
4. Flag a page as containing a PSD image if:
   - Number of contours > 10
   - AND the aspect ratio of the bounding box is within [0.5, 2.0].
"""
import json
import logging
import os
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
from pdf2image import convert_from_path

# Ensure we import from the project's utils
from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)

# Constants for detection
CANNY_LOW_THRESHOLD = 50
CANNY_HIGH_THRESHOLD = 150
MIN_CONTOURS = 10
MIN_ASPECT_RATIO = 0.5
MAX_ASPECT_RATIO = 2.0
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "detected_psd_images.json"


def detect_psd_images(pdf_path: str) -> List[str]:
    """
    Detect PSD images in a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file.
        
    Returns:
        List[str]: List of paths to saved image files (PNG) that match the criteria.
                   Returns an empty list if no images are found or on error.
    """
    detected_paths = []
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        logger.error(f"PDF file not found: {pdf_path}")
        return detected_paths

    try:
        logger.info(f"Converting PDF pages to images: {pdf_path}")
        # Convert PDF pages to PIL Images
        images = convert_from_path(str(pdf_path), dpi=200)
    except Exception as e:
        logger.error(f"Failed to convert PDF {pdf_path} to images: {e}")
        return detected_paths

    if not images:
        logger.warning(f"No pages found in PDF: {pdf_path}")
        return detected_paths

    for page_num, pil_image in enumerate(images):
        try:
            # Convert PIL Image to OpenCV format (numpy array)
            img_cv = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

            # Apply GaussianBlur to reduce noise and improve Canny performance
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Canny edge detection
            edges = cv2.Canny(blurred, CANNY_LOW_THRESHOLD, CANNY_HIGH_THRESHOLD)

            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Filter contours to find potential PSD images
            # A PSD image typically has a significant number of contours (lines, text, axes)
            # and a reasonable aspect ratio.
            potential_image_found = False
            for contour in contours:
                if len(contour) < MIN_CONTOURS:
                    continue

                x, y, w, h = cv2.boundingRect(contour)
                
                # Skip very small contours (noise)
                if w < 50 or h < 50:
                    continue

                aspect_ratio = float(w) / h
                
                # Check aspect ratio constraint
                if MIN_ASPECT_RATIO <= aspect_ratio <= MAX_ASPECT_RATIO:
                    # If we found a large enough contour with valid aspect ratio,
                    # we assume it's a candidate for a PSD image.
                    # We could be more strict (e.g., area threshold), but the
                    # contour count + aspect ratio is the primary filter per spec.
                    potential_image_found = True
                    break

            if potential_image_found:
                # Save the detected page as an image
                # Create output filename
                stem = pdf_path.stem
                output_filename = f"{stem}_page{page_num + 1}.png"
                output_path = OUTPUT_DIR / output_filename
                
                # Ensure output directory exists
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                
                # Save the image (convert back to RGB for saving as PNG)
                # cv2 uses BGR, PIL uses RGB. convert_from_path gives RGB.
                # We converted to BGR for OpenCV processing.
                # cv2.imwrite expects the image in the format it was created in.
                # Since we have `img_cv` (BGR), we save that.
                cv2.imwrite(str(output_path), img_cv)
                
                detected_paths.append(str(output_path))
                logger.info(f"Detected PSD image candidate on page {page_num + 1}: {output_path}")
            
        except Exception as e:
            logger.error(f"Error processing page {page_num + 1} of {pdf_path}: {e}")
            continue

    return detected_paths


def save_detection_results(detected_paths: List[str], output_file: Path = OUTPUT_FILE) -> None:
    """
    Save the list of detected image paths to a JSON file.
    
    Args:
        detected_paths (List[str]): List of image file paths.
        output_file (Path): Path to the output JSON file.
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(detected_paths, f, indent=2)
    logger.info(f"Saved detection results to {output_file} ({len(detected_paths)} images found)")


def run_image_detection_pipeline(pdf_paths: List[str]) -> List[str]:
    """
    Run the image detection pipeline on a list of PDF files.
    
    Args:
        pdf_paths (List[str]): List of paths to PDF files.
        
    Returns:
        List[str]: List of all detected image paths across all PDFs.
    """
    all_detected = []
    for pdf_path in pdf_paths:
        logger.info(f"Processing PDF: {pdf_path}")
        detected = detect_psd_images(pdf_path)
        all_detected.extend(detected)
    
    save_detection_results(all_detected)
    return all_detected


if __name__ == "__main__":
    # Example usage for direct execution
    # This would typically be called from a CLI or orchestration script
    import sys
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        results = detect_psd_images(pdf_file)
        print(f"Detected {len(results)} images.")
        if results:
            print(f"Saved to: {OUTPUT_FILE}")
    else:
        print("Usage: python -m src.ingest.image_detector <path_to_pdf>")
        print("Or pass a list of PDFs via a config if extended.")
