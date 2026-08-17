import os
import csv
import logging
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import math

from src.utils.config import get_project_root, get_interim_data_dir, get_interpolation_max_km, get_missing_threshold_percent
from src.utils.logging import setup_logger

logger = setup_logger(__name__)

# Constants
EARTH_RADIUS_KM = 6371.0

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth
    using the Haversine formula. Returns distance in kilometers.
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c

def get_osm_land_use(lat: float, lon: float) -> str:
    """
    Placeholder for OSM land-use lookup.
    In a full implementation, this would query OSM via Overpass API or OSMnx.
    For this task, we assume the data is already mapped or return a default.
    """
    # This function is a stub as per the existing API surface which might rely on
    # T015d having done the heavy lifting. We return a placeholder if needed.
    return "unknown"

def map_land_use_to_noise(land_use: str) -> float:
    """
    Map OSM land-use category to an estimated noise level in dB(A).
    """
    mapping = {
        "urban": 65.0,
        "residential": 55.0,
        "commercial": 70.0,
        "industrial": 75.0,
        "forest": 35.0,
        "water": 40.0,
        "agricultural": 45.0,
        "unknown": 50.0
    }
    return mapping.get(land_use, 50.0)

def map_noise_levels(records: List[Dict], noise_data: Dict[Tuple[float, float], float]) -> List[Dict]:
    """
    Map noise levels from a source dataset to the records.
    """
    mapped_records = []
    for rec in records:
        lat = rec.get('latitude')
        lon = rec.get('longitude')
        if lat is None or lon is None:
            rec['noise_level_db'] = None
            rec['noise_source'] = 'missing_coords'
        else:
            # Exact match
            noise = noise_data.get((lat, lon))
            if noise is not None:
                rec['noise_level_db'] = noise
                rec['noise_source'] = 'global_soundscapes'
            else:
                rec['noise_level_db'] = None
                rec['noise_source'] = 'missing'
        mapped_records.append(rec)
    return mapped_records

def interpolate_noise_nearest_neighbor(records: List[Dict], reference_data: List[Dict], max_km: float) -> List[Dict]:
    """
    For records with missing noise levels, find the nearest neighbor in reference_data
    within max_km and assign that noise level.
    """
    interpolated_count = 0
    failed_count = 0
    max_km_sq = max_km ** 2

    # Index reference data for faster lookup (simple list scan for now, could be KDTree)
    # Reference data must have lat, lon, and noise_level_db
    ref_points = [r for r in reference_data if r.get('latitude') is not None and r.get('longitude') is not None and r.get('noise_level_db') is not None]

    for rec in records:
        if rec.get('noise_level_db') is None and rec.get('noise_source') == 'missing':
            lat = rec['latitude']
            lon = rec['longitude']
            best_dist = float('inf')
            best_noise = None
            best_ref = None

            for ref in ref_points:
                dist = haversine_distance(lat, lon, ref['latitude'], ref['longitude'])
                if dist < best_dist:
                    best_dist = dist
                    best_noise = ref['noise_level_db']
                    best_ref = ref

            if best_dist <= max_km:
                rec['noise_level_db'] = best_noise
                rec['noise_source'] = 'interpolated'
                rec['interpolated_from_lat'] = best_ref['latitude']
                rec['interpolated_from_lon'] = best_ref['longitude']
                rec['interpolation_distance_km'] = best_dist
                interpolated_count += 1
            else:
                rec['noise_source'] = 'interpolation_failed'
                failed_count += 1
        # Else: already has noise or missing coords

    return records

def save_interpolated_records(records: List[Dict], output_path: Path):
    """
    Save the records that were successfully interpolated to a CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        'recording_id', 'species_id', 'latitude', 'longitude',
        'noise_level_db', 'noise_source', 'interpolated_from_lat',
        'interpolated_from_lon', 'interpolation_distance_km'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for rec in records:
            if rec.get('noise_source') == 'interpolated':
                writer.writerow(rec)

def main():
    """
    Main entry point for T015e: Interpolation Validation.
    1. Load the noise_mapped.csv (output of T015).
    2. Verify that all missing noise values within 50km were successfully interpolated.
    3. If >10% of records fail interpolation, log a warning but do NOT halt.
    4. Satisfies SC-006.
    """
    project_root = get_project_root()
    interim_dir = get_interim_data_dir()
    
    noise_mapped_path = interim_dir / "noise_mapped.csv"
    validation_log_path = interim_dir / "interpolation_validation_log.csv"

    if not noise_mapped_path.exists():
        logger.error(f"Input file not found: {noise_mapped_path}")
        raise FileNotFoundError(f"Input file {noise_mapped_path} not found. Run T015 first.")

    # Load data
    records = []
    with open(noise_mapped_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row['latitude'] = float(row['latitude']) if row['latitude'] else None
            row['longitude'] = float(row['longitude']) if row['longitude'] else None
            row['noise_level_db'] = float(row['noise_level_db']) if row['noise_level_db'] else None
            records.append(row)

    total_records = len(records)
    missing_initial = 0
    interpolated_count = 0
    failed_count = 0
    max_km = get_interpolation_max_km()
    missing_threshold_percent = get_missing_threshold_percent()

    # Separate records that need interpolation (missing noise, valid coords)
    # We assume T015d already ran and populated 'interpolated_records.csv' if needed,
    # but T015e's job is to VALIDATE the state of 'noise_mapped.csv' and ensure
    # the pipeline logic holds.
    # However, the task says "Verify that all missing noise values within 50km are successfully interpolated".
    # This implies we need to check the 'noise_source' field in noise_mapped.csv.
    
    # Re-calculate to be sure:
    # We need a reference to know if a point is "within 50km" of a valid source.
    # Since we don't have the raw reference data here, we trust the 'noise_source' field
    # set by T015d/T015 logic.
    # But to strictly satisfy "Verify", we should check if 'interpolation_failed' exists
    # and if the count is high.

    validation_results = []

    for rec in records:
        source = rec.get('noise_source', 'unknown')
        recording_id = rec.get('recording_id', 'unknown')
        
        entry = {
            'recording_id': recording_id,
            'noise_source': source,
            'status': 'OK'
        }

        if source == 'interpolated':
            interpolated_count += 1
            entry['status'] = 'INTERPOLATED_OK'
        elif source == 'interpolation_failed':
            failed_count += 1
            entry['status'] = 'INTERPOLATION_FAILED'
        elif source == 'missing':
            # This means T015d didn't catch it or it's outside 50km
            failed_count += 1
            entry['status'] = 'MISSING_NOT_INTERPOLATED'
        elif source in ['global_soundscapes', 'missing_coords']:
            entry['status'] = 'OK'
        else:
            entry['status'] = 'UNKNOWN_SOURCE'

        validation_results.append(entry)

    # Calculate statistics
    # The "missing" records that needed interpolation are those that were 'missing' initially.
    # In noise_mapped.csv, they should be either 'interpolated' or 'interpolation_failed' or 'missing'.
    # Let's count how many were originally missing (source != global_soundscapes and source != missing_coords)
    # But actually, the task says: "Verify that all missing noise values within 50km are successfully interpolated".
    # If a record is 'interpolation_failed', it means it was within 50km? No, it means it was NOT found within 50km.
    # So the check is: If a record is missing, it should be interpolated. If it's not, it's a failure.
    # The "within 50km" part is a condition for the interpolation attempt.
    # If the attempt failed, it's a failure.
    
    # Total records that were missing noise initially (source is missing or interpolation_failed or interpolated)
    # We assume T015d/T015 logic set the source correctly.
    # We just need to count failures.
    
    # Failure definition: Source is 'interpolation_failed' OR 'missing' (if it should have been interpolated)
    # For this task, we count 'interpolation_failed' and 'missing' (if no source) as failures.
    # But 'missing' might be outside 50km.
    # Let's assume 'interpolation_failed' means "tried but failed (outside 50km or no data)".
    # And 'missing' means "not tried or failed".
    
    # The task says: "If >10% of records fail interpolation, log a warning".
    # "Fail interpolation" = source == 'interpolation_failed' OR source == 'missing' (if it was missing initially).
    # Let's count all records that do NOT have a valid noise level (global_soundscapes or interpolated).
    
    valid_noise_count = sum(1 for r in records if r.get('noise_level_db') is not None)
    missing_noise_count = total_records - valid_noise_count
    
    # The "fail interpolation" count is the number of records that are still missing noise
    # AND were not 'missing_coords'.
    # But the task says "If >10% of records fail interpolation".
    # Let's interpret "records" as "records that needed interpolation".
    # But we don't have that count easily.
    # Let's use the count of 'interpolation_failed' + 'missing' (if not coords missing).
    
    # Simpler: Count records with source == 'interpolation_failed' or source == 'missing' (and not missing_coords)
    # Actually, let's just count the ones that are still missing noise and not missing_coords.
    failed_interpolation_count = 0
    for rec in records:
        if rec.get('noise_level_db') is None:
            if rec.get('noise_source') != 'missing_coords':
                failed_interpolation_count += 1

    # Calculate percentage
    # Denominator: Total records that had missing noise initially.
    # We don't have that number, so we use total_records as a conservative estimate,
    # or we count how many had 'noise_source' == 'missing' in the original (before interpolation).
    # Since we only have the final noise_mapped.csv, we assume all records with missing noise
    # were candidates for interpolation.
    # So: failed_interpolation_count / total_records (or missing_initial_count).
    # Let's use total_records as the denominator for the "10% of records" check,
    # as per the task wording "If >10% of records fail interpolation".
    
    if total_records > 0:
        failure_rate = failed_interpolation_count / total_records
    else:
        failure_rate = 0.0

    logger.info(f"Total records: {total_records}")
    logger.info(f"Interpolated: {interpolated_count}")
    logger.info(f"Failed interpolation (still missing): {failed_interpolation_count}")
    logger.info(f"Failure rate: {failure_rate:.2%}")

    # Write validation log
    validation_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(validation_log_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['recording_id', 'noise_source', 'status'])
        writer.writeheader()
        for res in validation_results:
            writer.writerow(res)

    # Warning check
    if failure_rate > (missing_threshold_percent / 100.0):
        logger.warning(f"High interpolation failure rate: {failure_rate:.2%} (> {missing_threshold_percent}%). "
                       f"Pipeline continues but data quality may be compromised.")
    else:
        logger.info(f"Interpolation failure rate ({failure_rate:.2%}) is within acceptable threshold ({missing_threshold_percent}%).")

    return {
        'total_records': total_records,
        'interpolated': interpolated_count,
        'failed': failed_interpolation_count,
        'failure_rate': failure_rate,
        'status': 'warning' if failure_rate > (missing_threshold_percent / 100.0) else 'ok'
    }

if __name__ == "__main__":
    main()
