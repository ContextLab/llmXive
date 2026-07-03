import numpy as np
from typing import List, Dict, Tuple, Optional, Any
import logging
import pandas as pd
from pathlib import Path
from config import get_config
from utils.logging import get_logger

logger = get_logger(__name__)

def define_generic_roi_grid(
    image_width: int,
    image_height: int,
    grid_rows: int = 3,
    grid_cols: int = 3
) -> List[Dict[str, Any]]:
    """
    Define a generic 3x3 grid of ROIs as a fallback when specific annotations are missing.
    
    Returns a list of ROI dictionaries with 'id', 'x', 'y', 'width', 'height'.
    Coordinates are normalized to 0-1 range relative to image dimensions.
    """
    cell_width = image_width / grid_cols
    cell_height = image_height / grid_rows
    rois = []

    for r in range(grid_rows):
        for c in range(grid_cols):
            roi_id = f"grid_{r}_{c}"
            x = c * cell_width
            y = r * cell_height
            w = cell_width
            h = cell_height
            
            # Normalize to 0-1
            rois.append({
                "id": roi_id,
                "x": x / image_width,
                "y": y / image_height,
                "width": w / image_width,
                "height": h / image_height,
                "x_px": x,
                "y_px": y,
                "width_px": w,
                "height_px": h
            })
    
    logger.info(f"Generated {len(rois)} generic ROI grid cells for {image_width}x{image_height} image")
    return rois

def get_roi_annotations_fallback(
    existing_annotations: Optional[List[Dict[str, Any]]],
    image_width: int,
    image_height: int
) -> List[Dict[str, Any]]:
    """
    Return existing annotations if present and non-empty.
    If missing or empty, generate a 3x3 generic grid fallback.
    """
    if existing_annotations and len(existing_annotations) > 0:
        logger.info(f"Using {len(existing_annotations)} existing ROI annotations")
        return existing_annotations
    
    logger.warning("No ROI annotations found. Applying 3x3 generic grid fallback.")
    return define_generic_roi_grid(image_width, image_height)

def calculate_fixation_in_roi(
    gaze_data: List[Dict[str, Any]],
    roi: Dict[str, Any],
    image_width: int,
    image_height: int
) -> Dict[str, float]:
    """
    Calculate total fixation duration within a specific ROI.
    
    Args:
        gaze_data: List of gaze points with 'x', 'y', 'duration' (in ms)
        roi: ROI dictionary with normalized or pixel coordinates
        image_width: Width of the stimulus image in pixels
        image_height: Height of the stimulus image in pixels
        
    Returns:
        Dictionary with 'total_duration_ms' and 'fixation_count'
    """
    total_duration = 0.0
    fixation_count = 0

    # Determine coordinate system of ROI
    if "x_px" in roi:
        # Pixel coordinates
        x_min, x_max = roi["x_px"], roi["x_px"] + roi["width_px"]
        y_min, y_max = roi["y_px"], roi["y_px"] + roi["height_px"]
    else:
        # Normalized coordinates (0-1)
        x_min = roi["x"] * image_width
        x_max = (roi["x"] + roi["width"]) * image_width
        y_min = roi["y"] * image_height
        y_max = (roi["y"] + roi["height"]) * image_height

    for point in gaze_data:
        px = point.get("x", 0)
        py = point.get("y", 0)
        duration = point.get("duration", 0)

        if x_min <= px < x_max and y_min <= py < y_max:
            total_duration += duration
            fixation_count += 1

    return {
        "total_duration_ms": total_duration,
        "fixation_count": fixation_count
    }

def calculate_saccade_amplitude(gaze_data: List[Dict[str, Any]]) -> float:
    """
    Calculate the mean saccade amplitude (Euclidean distance between consecutive gaze points).
    
    Args:
        gaze_data: List of gaze points with 'x', 'y' in pixels.
        
    Returns:
        Mean saccade amplitude in pixels.
    """
    if len(gaze_data) < 2:
        return 0.0
    
    amplitudes = []
    for i in range(1, len(gaze_data)):
        p1 = gaze_data[i-1]
        p2 = gaze_data[i]
        dx = p2.get("x", 0) - p1.get("x", 0)
        dy = p2.get("y", 0) - p1.get("y", 0)
        amp = np.sqrt(dx**2 + dy**2)
        amplitudes.append(amp)
    
    return float(np.mean(amplitudes))

def calculate_dispersion(gaze_data: List[Dict[str, Any]]) -> float:
    """
    Calculate the dispersion (area of the minimum bounding rectangle) of gaze points.
    
    Args:
        gaze_data: List of gaze points with 'x', 'y' in pixels.
        
    Returns:
        Dispersion area in square pixels.
    """
    if len(gaze_data) < 2:
        return 0.0
    
    xs = [p.get("x", 0) for p in gaze_data]
    ys = [p.get("y", 0) for p in gaze_data]
    
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    
    return float(width * height)

def extract_face_features(
    gaze_data: List[Dict[str, Any]],
    image_width: int,
    image_height: int,
    roi_annotations: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Extract fixation metrics for face features (eyes, mouth) using provided or fallback ROIs.
    
    If roi_annotations are missing, applies the 3x3 grid fallback.
    Returns aggregated features including total fixation duration per ROI,
    saccade amplitude, and dispersion.
    """
    # Apply fallback if necessary
    rois = get_roi_annotations_fallback(roi_annotations, image_width, image_height)

    features = {
        "total_gaze_points": len(gaze_data),
        "rois_analyzed": len(rois),
        "roi_metrics": {},
        "saccade_amplitude_px": calculate_saccade_amplitude(gaze_data),
        "dispersion_px2": calculate_dispersion(gaze_data)
    }

    for roi in rois:
        metrics = calculate_fixation_in_roi(gaze_data, roi, image_width, image_height)
        features["roi_metrics"][roi["id"]] = metrics

    return features

def process_participant_record(
    record: Dict[str, Any],
    config: Any
) -> Dict[str, Any]:
    """
    Process a single participant record from the raw dataset to extract features.
    
    Args:
        record: A dictionary containing 'gaze_data', 'image_width', 'image_height',
                and optionally 'roi_annotations'.
        config: Configuration object.
                
    Returns:
        A dictionary of extracted features including fixation durations, saccade amplitude,
        and dispersion.
    """
    gaze_data = record.get("gaze_data", [])
    image_width = record.get("image_width", config.get("default_image_width", 640))
    image_height = record.get("image_height", config.get("default_image_height", 480))
    roi_annotations = record.get("roi_annotations", None)
    
    # Basic validation
    if not isinstance(gaze_data, list):
        logger.error(f"Invalid gaze_data format in record: {record.get('participant_id', 'unknown')}")
        return {}
        
    if len(gaze_data) == 0:
        logger.warning(f"No gaze data found for participant: {record.get('participant_id', 'unknown')}")
        return {
            "participant_id": record.get("participant_id"),
            "trial_id": record.get("trial_id"),
            "total_gaze_points": 0,
            "saccade_amplitude_px": 0.0,
            "dispersion_px2": 0.0
        }

    features = extract_face_features(gaze_data, image_width, image_height, roi_annotations)
    features["participant_id"] = record.get("participant_id")
    features["trial_id"] = record.get("trial_id")
    
    return features

def main():
    """
    Main entry point to load raw data, extract features, and save to processed CSV.
    Implements FR-003: Compute fixation duration (eye/mouth), saccade amplitude, dispersion.
    """
    config = get_config()
    logger.info("Starting feature extraction pipeline (T018)...")
    
    raw_data_path = Path(config.DATA_RAW_DIR) / "downloaded_dataset.parquet"
    output_path = Path(config.DATA_PROCESSED_DIR) / "features.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not raw_data_path.exists():
        # Fallback for testing if the specific parquet isn't there, try to find any parquet
        logger.warning(f"Primary data file not found: {raw_data_path}. Attempting to find any parquet in raw dir...")
        parquet_files = list(Path(config.DATA_RAW_DIR).glob("*.parquet"))
        if not parquet_files:
            logger.error("No parquet files found in data/raw/. Cannot proceed with feature extraction.")
            return
        raw_data_path = parquet_files[0]
        logger.info(f"Using fallback data file: {raw_data_path}")

    try:
        # Load data
        logger.info(f"Loading data from {raw_data_path}...")
        df_raw = pd.read_parquet(raw_data_path)
        logger.info(f"Loaded {len(df_raw)} records.")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return

    extracted_rows = []
    
    # Process each row
    for idx, row in df_raw.iterrows():
        # Convert row to dict, handling potential nested structures if necessary
        # Assuming the parquet schema has 'gaze_data' as a list of dicts or similar structure
        # If gaze_data is stored as a stringified JSON, we'd need to parse it here.
        # For this implementation, we assume it's already deserialized or we handle common formats.
        
        # Attempt to reconstruct the record dict
        record = row.to_dict()
        
        # Handle case where gaze_data might be a string (common in some parquet exports)
        if isinstance(record.get("gaze_data"), str):
            import json
            try:
                record["gaze_data"] = json.loads(record["gaze_data"])
            except json.JSONDecodeError:
                logger.warning(f"Could not parse gaze_data for row {idx}, skipping.")
                continue

        features = process_participant_record(record, config)
        if features:
            extracted_rows.append(features)

    if not extracted_rows:
        logger.warning("No features extracted. Saving empty CSV.")
        pd.DataFrame().to_csv(output_path, index=False)
        return

    # Convert to DataFrame and save
    df_features = pd.DataFrame(extracted_rows)
    
    # Flatten roi_metrics if necessary, but for now keep as JSON string for simplicity
    # or expand if specific columns are needed. The task asks for fixation duration (eye/mouth).
    # If we have a 3x3 grid, we might need to map specific grid cells to eye/mouth.
    # Since specific ROI mapping isn't provided in the fallback, we output the raw grid metrics.
    # We will serialize the roi_metrics dict to a JSON string for the CSV.
    
    if "roi_metrics" in df_features.columns:
        df_features["roi_metrics"] = df_features["roi_metrics"].apply(lambda x: str(x) if isinstance(x, dict) else x)

    df_features.to_csv(output_path, index=False)
    logger.info(f"Feature extraction complete. Saved {len(df_features)} records to {output_path}")

if __name__ == "__main__":
    main()
