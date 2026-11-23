from __future__ import annotations

import csv
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import config utilities to find project paths
from utils.config import get_project_root, get_processed_dir, get_data_dir
# Import logging utilities (tolerant)
from utils.logging_config import get_logger, log_operation

# Import OpenCV and NumPy for image processing
# These are in requirements.txt (T002)
try:
    import cv2
    import numpy as np
except ImportError:
    print("ERROR: Required packages 'opencv-python' and 'numpy' are missing.")
    print("Please install them via: pip install opencv-python-headless numpy")
    sys.exit(1)

# Import the dataset loading logic if needed, but we will read manifest directly
# to ensure we strictly follow the "test set only" constraint.

def setup_logging() -> logging.Logger:
    """Setup logging for the feature extraction script."""
    logger = get_logger("extract_features")
    # The logger is a ReproducibilityLogger which is tolerant of any call shape.
    # We return it as a standard logging.Logger interface for compatibility if needed,
    # but primarily we use it via the tolerant interface.
    return logger

def estimate_grain_size(image_path: Path) -> float:
    """
    Estimate grain size in micrometers from a processed EBSD image.

    Method:
    1. Load image (grayscale).
    2. Apply Otsu's thresholding to segment grains (assuming processed images
       have high contrast between grain boundaries and interiors, or distinct
       phases).
    3. Morphological operations to clean noise.
    4. Connected components analysis to count grains and estimate area.
    5. Calculate equivalent circular diameter.
    6. Convert pixel area to physical area using known pixel scale (0.1 um/pixel
       for this synthetic dataset as per spec context).

    Returns:
        float: Estimated average grain size in micrometers.
    """
    # 1. Load image
    try:
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to read image {image_path}: {e}")

    # 2. Pre-processing: Gaussian blur to reduce noise
    blur = cv2.GaussianBlur(img, (5, 5), 0)

    # 3. Thresholding: Otsu's binarization
    # We assume grain boundaries are darker or lighter than interiors.
    # Otsu finds the optimal threshold automatically.
    ret, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Invert if necessary (assuming grains are the foreground objects)
    # If the thresholded image is mostly white (background), we might need to invert.
    # For EBSD, often boundaries are distinct. Let's assume grains are the
    # connected components we want to measure. If the majority is background,
    # we invert.
    # Heuristic: If more than 90% of pixels are white, invert.
    if np.count_nonzero(thresh) > thresh.size * 0.9:
        thresh = cv2.bitwise_not(thresh)

    # 4. Morphological operations to close gaps and remove small noise
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(thresh, kernel, iterations=2)
    eroded = cv2.erode(dilated, kernel, iterations=1)

    # 5. Connected Components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        eroded, connectivity=8
    )

    if num_labels <= 1:
        # No grains found (only background)
        return 0.0

    # Filter components: ignore the background (label 0) and very small noise
    grain_areas = []
    pixel_scale_um = 0.1  # 0.1 um per pixel (from synthetic dataset properties)

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        # Filter noise: assume grains are at least 10x10 pixels in processed images
        # or adjust based on actual data scale. 100 pixels = 100 * (0.1)^2 = 1 um^2
        if area > 50:  # Threshold for noise
            grain_areas.append(area)

    if not grain_areas:
        return 0.0

    # Calculate average grain area in pixels
    avg_area_pixels = np.mean(grain_areas)

    # Convert to micrometers (area scale factor = scale^2)
    # Area_um2 = Area_pixels * (pixel_scale_um)^2
    avg_area_um2 = avg_area_pixels * (pixel_scale_um ** 2)

    # Equivalent circular diameter: d = 2 * sqrt(Area / pi)
    avg_diameter_um = 2 * np.sqrt(avg_area_um2 / np.pi)

    return float(avg_diameter_um)

def extract_features_for_dataset(manifest_path: Path, output_path: Path, is_full_dataset: bool = False) -> None:
    """
    Iterate through the dataset specified by the manifest, calculate grain size,
    and write results to CSV.

    Args:
        manifest_path: Path to the manifest CSV file.
        output_path: Path to the output CSV file.
        is_full_dataset: If True, process all images in manifest (for optional full output).
    """
    logger = setup_logging()
    log_operation("start_feature_extraction", manifest=str(manifest_path), output=str(output_path))

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    results: List[Dict[str, Any]] = []

    # Read manifest
    with open(manifest_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    logger.log("processing_manifest", total_rows=len(rows))

    for i, row in enumerate(rows):
        image_id = row.get('image_id') or row.get('filename')
        if not image_id:
            logger.log("warning", message="Missing image_id in manifest row", row=i)
            continue

        # Construct path to image
        # The manifest usually contains relative paths from the processed directory
        image_filename = row.get('filename') or row.get('image_path') or f"{image_id}.png"
        
        # Determine the base directory for images based on the manifest location or context
        # For T022a, input is data/processed/test/ and manifest.csv.
        # We assume the manifest 'filename' is relative to the manifest's parent or a known split dir.
        # Let's assume the manifest is in data/processed/ and points to images in data/processed/test/
        # or the path is absolute/relative within the manifest.
        
        # Strategy: If path is relative, assume it's relative to the manifest's directory
        # or the standard split directory structure.
        manifest_dir = manifest_path.parent
        img_path = manifest_dir / image_filename
        
        if not img_path.exists():
            # Fallback: try looking in the parent's parent (processed) if manifest is in split folder
            if not img_path.exists():
                # Try to find the image in the processed directory structure
                # Common structure: data/processed/test/<filename>
                # If manifest is at data/processed/manifest.csv, then image is in data/processed/test/
                # If manifest is at data/processed/test/manifest.csv, image is in data/processed/test/
                # We'll try to resolve relative to the manifest's directory first.
                pass 
            
            # If still not found, try searching in the processed directory for the filename
            processed_dir = get_processed_dir()
            found_img = None
            for root, _, files in os.walk(processed_dir):
                if image_filename in files:
                    found_img = Path(root) / image_filename
                    break
            
            if found_img:
                img_path = found_img
            else:
                logger.log("error", message=f"Image not found: {image_filename}", image_id=image_id)
                continue

        try:
            grain_size = estimate_grain_size(img_path)
            results.append({
                'image_id': image_id,
                'grain_size_um': grain_size
            })
            if (i + 1) % 100 == 0:
                logger.log("progress", processed=i + 1, total=len(rows))
        except Exception as e:
            logger.log("error", message=f"Failed to process {image_filename}", error=str(e))
            # Continue processing other images

    # Write results
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['image_id', 'grain_size_um']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.log("finished_extraction", output_file=str(output_path), count=len(results))

def main() -> None:
    """Main entry point for the feature extraction script."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract grain size features from EBSD images.")
    parser.add_argument(
        "--manifest",
        type=str,
        default=None,
        help="Path to the manifest CSV file. Defaults to data/processed/manifest.csv if not provided."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to the output CSV file. Defaults to data/features/test_grain_features.csv."
    )
    parser.add_argument(
        "--full-dataset",
        action="store_true",
        help="If provided, also output data/features/all_grain_features.csv using the full manifest."
    )
    parser.add_argument(
        "--test-only",
        action="store_true",
        default=True,
        help="Only process the test set (default). If False, processes the full manifest."
    )

    args = parser.parse_args()
    logger = setup_logging()
    log_operation("main", args=vars(args))

    # Determine paths
    project_root = get_project_root()
    processed_dir = get_processed_dir()
    features_dir = project_root / "data" / "features"
    features_dir.mkdir(parents=True, exist_ok=True)

    # Default manifest: if --test-only, we need the test manifest.
    # The task spec says input is manifest.csv and data/processed/test/.
    # Usually split.py generates data/processed/test/manifest.csv or data/processed/manifest.csv with a split column.
    # Assuming T013 (split) generated data/processed/manifest.csv with a 'split' column,
    # OR it generated separate manifests.
    # Let's assume the standard output of T013 is data/processed/manifest.csv containing all data with a 'split' column,
    # OR separate files. The task says "Input: manifest.csv".
    # We will look for data/processed/manifest.csv first. If it has a 'split' column, we filter.
    # If it's the test-specific manifest (e.g. data/processed/test/manifest.csv), we use that.

    if args.manifest:
        manifest_path = Path(args.manifest)
    else:
        # Default: try to find the manifest
        # Priority 1: data/processed/manifest.csv (if it has split info)
        # Priority 2: data/processed/test/manifest.csv (if split into folders)
        default_manifest = processed_dir / "manifest.csv"
        if default_manifest.exists():
            manifest_path = default_manifest
        else:
            test_manifest = processed_dir / "test" / "manifest.csv"
            if test_manifest.exists():
                manifest_path = test_manifest
            else:
                # Fallback: search for manifest.csv in processed
                for p in processed_dir.rglob("manifest.csv"):
                    manifest_path = p
                    break
                else:
                    raise FileNotFoundError("Could not find manifest.csv in processed directory.")

    if not args.output:
        args.output = str(features_dir / "test_grain_features.csv")

    # Logic for T022a: Strictly limited to test set
    # If the provided manifest is the full one (with split column), we must filter.
    # If it's already the test manifest, we use it directly.
    
    final_manifest_path = manifest_path
    
    # Check if we need to filter by split
    if manifest_path.exists():
        import csv
        with open(manifest_path, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            if headers and 'split' in headers:
                # It's the full manifest. We need to filter for 'test'.
                logger.log("filtering_manifest", message="Manifest contains 'split' column. Filtering for 'test'.")
                # Create a temporary filtered manifest in memory or file?
                # We'll just read and filter in the loop, but for simplicity, let's assume
                # the manifest provided to this script is already the test manifest OR we handle it here.
                # To be safe, we will read the full manifest and filter in the extraction loop
                # OR create a temporary list of test rows.
                # Since extract_features_for_dataset expects a manifest file, let's create a temp one if needed.
                import tempfile
                import shutil
                temp_fd, temp_path = tempfile.mkstemp(suffix=".csv")
                os.close(temp_fd)
                
                with open(manifest_path, 'r') as fin, open(temp_path, 'w', newline='') as fout:
                    reader = csv.DictReader(fin)
                    writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
                    writer.writeheader()
                    for row in reader:
                        if row.get('split') == 'test':
                            writer.writerow(row)
                
                final_manifest_path = Path(temp_path)
                logger.log("created_temp_manifest", path=str(final_manifest_path))
            else:
                # No split column, assume it's the correct subset (test)
                pass

    try:
        # Extract features for test set
        extract_features_for_dataset(final_manifest_path, Path(args.output))
        
        # Optional: Full dataset extraction if flag is set
        if args.full_dataset:
            full_output = features_dir / "all_grain_features.csv"
            # If we created a temp manifest for test, we need the original for full
            if 'temp_path' in locals() and manifest_path.exists():
                extract_features_for_dataset(manifest_path, full_output)
            else:
                extract_features_for_dataset(manifest_path, full_output)
                
        logger.log("success", message="Feature extraction completed.")
    except Exception as e:
        logger.log("error", message="Feature extraction failed.", error=str(e))
        raise
    finally:
        # Cleanup temp manifest if created
        if 'final_manifest_path' in locals() and 'temp_path' in locals():
            if final_manifest_path.exists() and str(final_manifest_path) != str(manifest_path):
                try:
                    os.remove(final_manifest_path)
                except:
                    pass

if __name__ == "__main__":
    main()