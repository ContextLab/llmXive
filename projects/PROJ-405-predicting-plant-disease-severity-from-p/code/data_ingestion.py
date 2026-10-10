import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import time
import json
import requests
import zipfile

# Imports from project structure
from config import get_path, ensure_dirs
from utils.logging_config import setup_logging, get_logger
from utils.feature_extraction import extract_features
from weather_linker import get_weather_for_record, merge_weather_and_features

logger = get_logger(__name__)

def download_plantvillage(limit: Optional[int] = None) -> List[Dict]:
    """
    Download PlantVillage dataset from the official HuggingFace zip URL.
    Streams the download to avoid loading the entire file into memory.
    Extracts images to the raw data directory and returns a list of
    dictionaries containing at least the ``image_path`` key.

    Args:
        limit: Optional maximum number of images to return. If provided,
               only the first ``limit`` images (in alphabetical order) are
               returned.

    Returns:
        List of dictionaries, each representing an image record with
        ``image_path`` (and later metadata fields will be added).
    """
    dataset_url = (
        "https://huggingface.co/datasets/PlantVillage/PlantVillage/resolve/main/PlantVillage.zip"
    )

    raw_dir = get_path("data_raw") / "plantvillage"
    ensure_dirs(raw_dir)

    zip_path = raw_dir / "PlantVillage.zip"

    if not zip_path.is_file():
        logger.info(f"Downloading PlantVillage dataset (≈ 1‑GB) to {zip_path} ...")
        try:
            with requests.get(dataset_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
        except Exception as e:
            logger.critical(f"Failed to download PlantVillage dataset: {e}")
            raise

    # Extract only if not already extracted
    extracted_flag = raw_dir / ".extracted"
    if not extracted_flag.is_file():
        logger.info(f"Extracting PlantVillage archive to {raw_dir} ...")
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(raw_dir)
            extracted_flag.touch()
        except Exception as e:
            logger.critical(f"Failed to extract PlantVillage archive: {e}")
            raise

    # Walk the extracted directory and collect image file paths
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    records: List[Dict] = []
    for root, _, files in os.walk(raw_dir):
        for fname in sorted(files):
            if Path(fname).suffix.lower() in image_extensions:
                img_path = Path(root) / fname
                records.append({"image_path": str(img_path)})
                if limit and len(records) >= limit:
                    break
        if limit and len(records) >= limit:
            break

    logger.info(f"Collected {len(records)} image records (limit={limit}).")
    return records

def extract_metadata_from_path(image_path: str) -> Dict[str, Any]:
    """
    Extract metadata from image filename or path.
    Expected format: .../path/to/image_YYYYMMDD_lat_lon.jpg
    """
    parts = image_path.split('/')
    filename = parts[-1]

    import re
    match = re.search(r'(\d{4}-\d{2}-\d{2})_(\d+\.\d+)_(-?\d+\.\d+)', filename)
    if match:
        date_str = match.group(1)
        lat = float(match.group(2))
        lon = float(match.group(3))
        return {
            "image_path": image_path,
            "image_date": datetime.strptime(date_str, "%Y-%m-%d"),
            "location_lat": lat,
            "location_lon": lon
        }
    else:
        # No location/date encoded – return None for those fields
        return {
            "image_path": image_path,
            "image_date": None,
            "location_lat": None,
            "location_lon": None
        }

def process_image_features(images_data: List[Dict]) -> List[Dict]:
    """
    Process a list of image records to extract visual features.
    """
    results = []
    for record in images_data:
        img_path = record.get("image_path")
        if not img_path or not os.path.exists(img_path):
            logger.warning(f"Image not found: {img_path}. Skipping.")
            continue

        try:
            features = extract_features(img_path)
            record.update(features)
            results.append(record)
        except Exception as e:
            logger.error(f"Failed to extract features for {img_path}: {e}")
            continue
    return results

def filter_records_with_location(records: List[Dict]) -> List[Dict]:
    """
    T018: Exclude records with missing location metadata.
    Log a warning for each excluded record and ensure they are NOT present in the final output.
    """
    filtered = []
    excluded_count = 0

    for record in records:
        lat = record.get("location_lat")
        lon = record.get("location_lon")

        if lat is None or lon is None:
            logger.warning(
                f"Excluding record due to missing location metadata: {record.get('image_path', 'unknown')}. "
                f"Lat: {lat}, Lon: {lon}"
            )
            excluded_count += 1
            continue

        filtered.append(record)

    logger.info(f"Filtered {excluded_count} records with missing location. "
                f"Remaining valid records: {len(filtered)}")
    return filtered

def merge_data(image_features_df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge image features and weather data on the ``image_path`` column.
    Performs an inner join so that only records for which both feature and weather
    information are available are retained.

    Args:
        image_features_df: DataFrame containing visual features and metadata.
        weather_df: DataFrame containing weather columns (must include ``image_path``).

    Returns:
        Merged DataFrame.
    """
    if "image_path" not in image_features_df.columns or "image_path" not in weather_df.columns:
        logger.error("Both DataFrames must contain an 'image_path' column for merging.")
        raise KeyError("Missing 'image_path' column in one of the DataFrames.")

    merged = pd.merge(image_features_df, weather_df, on="image_path", how="inner")
    logger.info(f"Merged dataset contains {len(merged)} records.")
    return merged

def verify_merge(df: pd.DataFrame) -> bool:
    """
    Verify that the merged dataframe has non‑null values in weather columns.
    """
    weather_cols = ["mean_temp", "mean_humidity", "total_precipitation"]
    for col in weather_cols:
        if col not in df.columns:
            logger.error(f"Missing required weather column: {col}")
            return False
        if df[col].isnull().any():
            logger.warning(f"Found null values in weather column: {col}")
    return True

def run_feature_extraction_pipeline(limit: Optional[int] = None) -> pd.DataFrame:
    """
    Main pipeline function to download, extract, filter, and merge data.
    """
    # 1. Download
    raw_records = download_plantvillage(limit=limit)

    # 2. Extract metadata from filenames (adds date & location fields)
    records_with_meta = [extract_metadata_from_path(r["image_path"]) for r in raw_records]

    # 3. Extract visual features
    processed_data = process_image_features(records_with_meta)

    # 4. Filter out records missing location metadata (T018)
    valid_records = filter_records_with_location(processed_data)

    if not valid_records:
        logger.critical("No valid records with location metadata found. Pipeline aborted.")
        return pd.DataFrame()

    # 5. Separate image‑feature DataFrame
    image_features_df = pd.DataFrame(valid_records)

    # 6. Fetch weather and build a weather‑only DataFrame
    weather_records = []
    for rec in valid_records:
        lat = rec["location_lat"]
        lon = rec["location_lon"]
        date = rec.get("image_date") or datetime.now()
        weather = get_weather_for_record(lat, lon, date)
        if weather:
            weather_entry = {"image_path": rec["image_path"], **weather}
            weather_records.append(weather_entry)
        else:
            logger.warning(f"Weather fetch failed for {rec['image_path']}; record will be omitted.")

    if not weather_records:
        logger.error("Failed to retrieve any weather data. Pipeline cannot continue.")
        return pd.DataFrame()

    weather_df = pd.DataFrame(weather_records)

    # 7. Merge using the dedicated ``merge_data`` function
    df = merge_data(image_features_df, weather_df)

    # 8. Verify merged dataset
    if not verify_merge(df):
        logger.error("Verification failed. Output may be incomplete.")

    # 9. Save unified dataset
    output_dir = get_path("data_processed")
    ensure_dirs(output_dir)
    output_path = output_dir / "unified_analysis.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved unified dataset to {output_path}")

    return df

def main():
    """Entry point for data ingestion."""
    setup_logging()
    logger.info("Starting Data Ingestion Pipeline...")

    # Run with a small limit for quick testing; remove ``limit`` for full run.
    df = run_feature_extraction_pipeline(limit=100)

    if not df.empty:
        logger.info("Pipeline completed successfully.")
    else:
        logger.error("Pipeline failed to produce data.")
        sys.exit(1)

if __name__ == "__main__":
    main()
