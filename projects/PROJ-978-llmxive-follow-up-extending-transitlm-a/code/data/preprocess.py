import json
import os
import sys
import hashlib
import pandas as pd
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configuration paths
RAW_DATA_PATH = Path("data/raw/transitlm_ground_truth.json")
FILTERED_DATA_PATH = Path("data/processed/city_filtered_routes.jsonl")
VOCAB_DATA_PATH = Path("data/processed/vocab_restricted_routes.jsonl")
STRATIFIED_DATA_PATH = Path("data/processed/stratified_routes.parquet")

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_raw_dataset() -> List[Dict[str, Any]]:
    """Load the raw TransitLM dataset."""
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Raw dataset not found at {RAW_DATA_PATH}")
    
    with open(RAW_DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'routes' in data:
        return data['routes']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Unexpected dataset format")

def filter_cities(data: List[Dict[str, Any]], cities: List[str] = None) -> List[Dict[str, Any]]:
    """Filter routes for specific Chinese cities."""
    if cities is None:
        cities = ["Beijing", "Shanghai", "Guangzhou", "Shenzhen"]
    
    filtered = []
    for route in data:
        city = route.get('city', '')
        if city in cities:
            filtered.append(route)
    
    return filtered

def build_vocabulary(data: List[Dict[str, Any]], top_n: int = 5000) -> Dict[str, int]:
    """Build a vocabulary of top-N stations."""
    station_counts = Counter()
    for route in data:
        stops = route.get('stops', [])
        for stop in stops:
            station_counts[stop] += 1
    
    top_stations = station_counts.most_common(top_n)
    vocab = {station: idx for idx, (station, _) in enumerate(top_stations)}
    vocab['<UNKNOWN>'] = len(vocab)
    return vocab

def apply_vocabulary_filter(data: List[Dict[str, Any]], vocab: Dict[str, int]) -> List[Dict[str, Any]]:
    """Apply vocabulary restriction to routes."""
    processed = []
    for route in data:
        stops = route.get('stops', [])
        processed_stops = [vocab.get(stop, vocab['<UNKNOWN>']) for stop in stops]
        
        processed_route = route.copy()
        processed_route['stops'] = processed_stops
        processed_route['original_stops'] = stops
        processed.append(processed_route)
    
    return processed

def stratify_routes(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Stratify routes into short (<15), medium (15-30), and long (>30) categories.
    
    Args:
        data: List of route dictionaries with 'stops' field.
    
    Returns:
        DataFrame with stratified routes and category labels.
    
    Verification:
        - Asserts row_count > 0
        - Asserts categories are balanced (at least one route per category)
    """
    if not data:
        raise ValueError("Input data is empty")
    
    stratified_data = []
    for route in data:
        stops = route.get('stops', [])
        route_length = len(stops)
        
        if route_length < 15:
            category = "short"
        elif route_length <= 30:
            category = "medium"
        else:
            category = "long"
        
        route_entry = route.copy()
        route_entry['route_length'] = route_length
        route_entry['category'] = category
        stratified_data.append(route_entry)
    
    df = pd.DataFrame(stratified_data)
    
    # Verification: row_count > 0
    if len(df) == 0:
        raise ValueError("Stratification resulted in zero rows")
    
    # Verification: categories are balanced (at least one route per category)
    categories = df['category'].unique()
    expected_categories = {"short", "medium", "long"}
    if not expected_categories.issubset(set(categories)):
        missing = expected_categories - set(categories)
        raise ValueError(f"Missing categories in stratification: {missing}")
    
    category_counts = df['category'].value_counts()
    print(f"Stratification results:")
    print(f"  Short (<15): {category_counts.get('short', 0)}")
    print(f"  Medium (15-30): {category_counts.get('medium', 0)}")
    print(f"  Long (>30): {category_counts.get('long', 0)}")
    print(f"  Total: {len(df)}")
    
    return df

def compute_route_metrics(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute basic metrics for routes."""
    metrics = {
        'total_routes': len(data),
        'avg_stops': sum(len(r.get('stops', [])) for r in data) / len(data) if data else 0,
        'min_stops': min(len(r.get('stops', [])) for r in data) if data else 0,
        'max_stops': max(len(r.get('stops', [])) for r in data) if data else 0
    }
    return metrics

def save_processed_data(df: pd.DataFrame, output_path: Path) -> None:
    """Save processed data to Parquet format."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"Saved stratified routes to {output_path}")

def validate_output(df: pd.DataFrame) -> bool:
    """Validate the output DataFrame."""
    required_columns = ['category', 'route_length']
    if not all(col in df.columns for col in required_columns):
        return False
    
    if not df['category'].isin(['short', 'medium', 'long']).all():
        return False
    
    return True

def main():
    """Main execution function for T006c."""
    print("Starting T006c: Stratify routes...")
    
    # Load raw data
    raw_data = load_raw_dataset()
    print(f"Loaded {len(raw_data)} routes")
    
    # Filter cities (T006a dependency)
    filtered_data = filter_cities(raw_data)
    print(f"Filtered to {len(filtered_data)} routes for target cities")
    
    # Apply vocabulary restriction (T006b dependency)
    vocab = build_vocabulary(filtered_data)
    vocab_restricted_data = apply_vocabulary_filter(filtered_data, vocab)
    print(f"Applied vocabulary restriction with {len(vocab)} tokens")
    
    # Stratify routes (T006c main task)
    stratified_df = stratify_routes(vocab_restricted_data)
    
    # Validate output
    if not validate_output(stratified_df):
        raise ValueError("Validation failed for stratified output")
    
    # Save to Parquet
    save_processed_data(stratified_df, STRATIFIED_DATA_PATH)
    
    # Verify file exists and has content
    if not STRATIFIED_DATA_PATH.exists():
        raise FileNotFoundError(f"Output file not created: {STRATIFIED_DATA_PATH}")
    
    print(f"Task T006c completed successfully. Output: {STRATIFIED_DATA_PATH}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
