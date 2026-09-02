import json
import os
import sys
import hashlib
import pandas as pd
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

# Constants for token handling
UNKNOWN_TOKEN = "<UNKNOWN>"
VALIDITY_METRIC_THRESHOLD = 0.0

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_raw_dataset(file_path: str) -> List[Dict[str, Any]]:
    """Load the raw dataset from a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def filter_cities(data: List[Dict[str, Any]], cities: List[str]) -> List[Dict[str, Any]]:
    """Filter the dataset for specific cities."""
    city_set = set(cities)
    return [route for route in data if route.get('city') in city_set]

def build_vocabulary(data: List[Dict[str, Any]], top_n: int) -> Dict[str, int]:
    """Build a vocabulary of top-N stations."""
    station_counts = Counter()
    for route in data:
        if 'stations' in route:
            station_counts.update(route['stations'])
    
    # Get top N stations
    top_stations = [station for station, _ in station_counts.most_common(top_n)]
    vocab = {station: idx for idx, station in enumerate(top_stations)}
    vocab[UNKNOWN_TOKEN] = len(vocab)  # Add UNKNOWN token at the end
    return vocab

def apply_vocabulary_filter(data: List[Dict[str, Any]], vocab: Dict[str, int]) -> List[Dict[str, Any]]:
    """Apply vocabulary restriction to routes."""
    result = []
    for route in data:
        filtered_route = route.copy()
        if 'stations' in route:
            filtered_stations = []
            for station in route['stations']:
                if station in vocab:
                    filtered_stations.append(station)
                else:
                    filtered_stations.append(UNKNOWN_TOKEN)
            filtered_route['stations'] = filtered_stations
        result.append(filtered_route)
    return result

def stratify_routes(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Stratify routes into short, medium, and long categories."""
    rows = []
    for route in data:
        length = len(route.get('stations', []))
        category = 'short' if length < 15 else ('medium' if length <= 30 else 'long')
        rows.append({
            'route_id': route.get('route_id'),
            'city': route.get('city'),
            'length': length,
            'category': category,
            'stations': route.get('stations', []),
            'ground_truth': route.get('ground_truth', [])
        })
    
    df = pd.DataFrame(rows)
    return df

def compute_route_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute metrics for each route."""
    metrics = []
    for _, row in df.iterrows():
        stations = row['stations']
        ground_truth = row.get('ground_truth', [])
        
        # Count UNKNOWN tokens
        unknown_count = sum(1 for s in stations if s == UNKNOWN_TOKEN)
        
        # Compute validity metrics, excluding UNKNOWN unless ground truth matches
        valid_matches = 0
        total_comparable = 0
        
        for i, (pred, truth) in enumerate(zip(stations, ground_truth)):
            # Skip UNKNOWN tokens unless ground truth is also UNKNOWN
            if pred == UNKNOWN_TOKEN:
                if truth == UNKNOWN_TOKEN:
                    # Ground truth matches UNKNOWN, count as valid
                    valid_matches += 1
                    total_comparable += 1
                # else: UNKNOWN in prediction but not in ground truth, exclude from metric
            else:
                # Regular prediction
                total_comparable += 1
                if pred == truth:
                    valid_matches += 1
        
        validity_score = valid_matches / total_comparable if total_comparable > 0 else 0.0
        
        metrics.append({
            'route_id': row['route_id'],
            'length': row['length'],
            'category': row['category'],
            'unknown_count': unknown_count,
            'validity_score': validity_score,
            'total_comparable': total_comparable,
            'valid_matches': valid_matches
        })
    
    return pd.DataFrame(metrics)

def save_processed_data(df: pd.DataFrame, output_path: str) -> None:
    """Save processed data to a file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if output_path.endswith('.parquet'):
        df.to_parquet(output_path, index=False)
    elif output_path.endswith('.jsonl'):
        with open(output_path, 'w', encoding='utf-8') as f:
            for _, row in df.iterrows():
                f.write(json.dumps(row.to_dict()) + '\n')
    elif output_path.endswith('.json'):
        df.to_json(output_path, orient='records', indent=2)
    else:
        raise ValueError(f"Unsupported file format: {output_path}")

def validate_output(df: pd.DataFrame, expected_categories: List[str]) -> bool:
    """Validate the output dataframe."""
    if df.empty:
        return False
    
    categories = set(df['category'].unique())
    expected_set = set(expected_categories)
    
    return categories == expected_set and len(df) > 0

def main():
    """Main function to run the preprocessing pipeline."""
    # Load raw dataset
    raw_data_path = "data/raw/transitlm_ground_truth.json"
    if not os.path.exists(raw_data_path):
        print(f"Error: Raw dataset not found at {raw_data_path}")
        sys.exit(1)
    
    data = load_raw_dataset(raw_data_path)
    
    # Filter cities (Chinese cities as per project context)
    cities = ["Beijing", "Shanghai", "Guangzhou", "Shenzhen"]
    filtered_data = filter_cities(data, cities)
    
    # Build vocabulary
    vocab = build_vocabulary(filtered_data, top_n=1000)
    
    # Apply vocabulary filter
    vocab_restricted_data = apply_vocabulary_filter(filtered_data, vocab)
    
    # Stratify routes
    stratified_df = stratify_routes(vocab_restricted_data)
    
    # Compute route metrics (includes UNKNOWN token handling)
    metrics_df = compute_route_metrics(stratified_df)
    
    # Save outputs
    save_processed_data(stratified_df, "data/processed/stratified_routes.parquet")
    save_processed_data(metrics_df, "data/analysis/route_metrics.json")
    
    # Validate output
    if validate_output(stratified_df, ['short', 'medium', 'long']):
        print("Preprocessing completed successfully!")
    else:
        print("Warning: Output validation failed")

if __name__ == "__main__":
    main()