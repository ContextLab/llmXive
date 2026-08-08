import json
import os
import sys
import hashlib
import pandas as pd
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

# Configuration constants matching project specs
CITY_FILTERS = ["Beijing", "Shanghai", "Guangzhou", "Shenzhen"]
SHORT_THRESHOLD = 15
MEDIUM_THRESHOLD = 30
VOCAB_SIZE_LIMIT = 5000  # Default for vocab restriction if needed in this flow

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_raw_dataset(path: str) -> List[Dict[str, Any]]:
    """Load the raw JSON dataset."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def filter_cities(data: List[Dict[str, Any]], cities: List[str] = None) -> List[Dict[str, Any]]:
    """Filter dataset for specific Chinese cities."""
    if cities is None:
        cities = CITY_FILTERS
    
    filtered = []
    for record in data:
        # Assuming 'city' or 'location_city' field exists, or nested in 'metadata'
        city = record.get('city') or record.get('location_city') or record.get('metadata', {}).get('city')
        if city and city in cities:
            filtered.append(record)
    return filtered

def build_vocabulary(data: List[Dict[str, Any]], limit: int = VOCAB_SIZE_LIMIT) -> Dict[str, int]:
    """Build a frequency-based vocabulary from station names."""
    station_counts = Counter()
    for record in data:
        stops = record.get('stops', [])
        for stop in stops:
            station_name = stop.get('name') if isinstance(stop, dict) else stop
            if station_name:
                station_counts[station_name] += 1
    
    # Keep top N stations, map others to UNKNOWN
    vocab = {name: idx for idx, (name, _) in enumerate(station_counts.most_common(limit - 1))}
    vocab['<UNKNOWN>'] = limit - 1
    return vocab

def apply_vocabulary_filter(data: List[Dict[str, Any]], vocab: Dict[str, int]) -> List[Dict[str, Any]]:
    """Apply vocabulary restriction, replacing unknown stations with <UNKNOWN>."""
    processed = []
    for record in data:
        new_record = record.copy()
        new_stops = []
        for stop in record.get('stops', []):
            stop_name = stop.get('name') if isinstance(stop, dict) else stop
            if stop_name in vocab:
                new_stops.append(stop)
            else:
                # Replace with UNKNOWN token structure
                new_stops.append({'name': '<UNKNOWN>', 'id': vocab['<UNKNOWN>']})
        new_record['stops'] = new_stops
        processed.append(new_record)
    return processed

def stratify_routes(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Stratify routes into short (<15), medium (15-30), and long (>30) categories.
    
    Args:
        data: List of route dictionaries with 'stops' list.
    
    Returns:
        pandas DataFrame with columns: route_id, stop_count, length_category, and original data.
    """
    if not data:
        raise ValueError("Input data is empty. Cannot stratify routes.")
    
    rows = []
    for record in data:
        stops = record.get('stops', [])
        stop_count = len(stops)
        
        if stop_count < SHORT_THRESHOLD:
            category = 'short'
        elif stop_count <= MEDIUM_THRESHOLD:
            category = 'medium'
        else:
            category = 'long'
        
        row = {
            'route_id': record.get('route_id', record.get('id', f"route_{len(rows)}")),
            'stop_count': stop_count,
            'length_category': category,
            'stops': stops, # Store full stops list for downstream usage
            'city': record.get('city'),
            'ground_truth_next': record.get('ground_truth_next') # Keep for evaluation later
        }
        # Flatten other metadata if needed, but keeping raw record in 'stops' is safer for now
        # We will serialize the whole record or specific fields as needed for Parquet
        # For Parquet, we need to ensure 'stops' is serializable (list of dicts is fine in newer pandas/pyarrow)
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Verification: Assert row_count > 0
    assert len(df) > 0, "Stratified dataset is empty."
    
    # Verification: Check balance (warn if heavily skewed, but don't fail unless empty)
    category_counts = df['length_category'].value_counts()
    print(f"Stratification Summary:\n{category_counts}")
    
    return df

def compute_route_metrics(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute basic metrics for the dataset."""
    if not data:
        return {}
    total_routes = len(data)
    total_stops = sum(len(r.get('stops', [])) for r in data)
    return {
        'total_routes': total_routes,
        'total_stops': total_stops,
        'avg_stops_per_route': total_stops / total_routes if total_routes > 0 else 0
    }

def save_processed_data(df: pd.DataFrame, output_path: str):
    """Save the processed DataFrame to a Parquet file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"Saved stratified routes to {output_path}")

def validate_output(file_path: str) -> bool:
    """Validate that the output file exists and is not empty."""
    if not os.path.exists(file_path):
        return False
    if os.path.getsize(file_path) == 0:
        return False
    return True

def main():
    """Main entry point for preprocessing pipeline."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    raw_input_path = project_root / "data" / "raw" / "transitlm_ground_truth.json"
    city_filtered_path = project_root / "data" / "processed" / "city_filtered_routes.jsonl"
    vocab_restricted_path = project_root / "data" / "processed" / "vocab_restricted_routes.jsonl"
    stratified_output_path = project_root / "data" / "processed" / "stratified_routes.parquet"
    
    # Check if intermediate files exist (T006a, T006b outputs)
    # If T006a/b haven't run in this exact environment, we might need to load raw and re-filter
    # But per task description, we assume T006b output is available or we chain from raw if needed.
    # For robustness, we check for vocab_restricted first, then city_filtered, then raw.
    
    input_data = None
    source = ""
    
    if vocab_restricted_path.exists():
        print(f"Loading from vocab_restricted: {vocab_restricted_path}")
        with open(vocab_restricted_path, 'r', encoding='utf-8') as f:
            input_data = [json.loads(line) for line in f]
        source = "vocab_restricted"
    elif city_filtered_path.exists():
        print(f"Loading from city_filtered: {city_filtered_path}")
        with open(city_filtered_path, 'r', encoding='utf-8') as f:
            input_data = [json.loads(line) for line in f]
        source = "city_filtered"
    elif raw_input_path.exists():
        print(f"Loading from raw: {raw_input_path}")
        input_data = load_raw_dataset(str(raw_input_path))
        # Re-apply filters if loading from raw to ensure consistency
        input_data = filter_cities(input_data)
        vocab = build_vocabulary(input_data)
        input_data = apply_vocabulary_filter(input_data, vocab)
        source = "raw (re-processed)"
    else:
        raise FileNotFoundError("No input data found. Expected raw or processed files.")
    
    print(f"Loaded {len(input_data)} routes from {source}")
    
    # Perform Stratification (T006c)
    df_stratified = stratify_routes(input_data)
    
    # Save to Parquet
    save_processed_data(df_stratified, str(stratified_output_path))
    
    # Validate
    if validate_output(str(stratified_output_path)):
        print("T006c Validation: PASSED")
        return 0
    else:
        print("T006c Validation: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
