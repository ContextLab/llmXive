import json
import os
import sys
import hashlib
import pandas as pd
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Constants for city filtering (matches T006a logic)
TARGET_CITIES = ["Beijing", "Shanghai", "Guangzhou", "Shenzhen"]

# Constants for stratification
SHORT_THRESHOLD = 15
MEDIUM_THRESHOLD = 30

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_raw_dataset(input_path: str) -> List[Dict[str, Any]]:
    """
    Load the raw dataset from a JSON or JSONL file.
    Expects a list of route objects.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Raw dataset not found at {input_path}")

    if path.suffix == ".jsonl":
        data = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data
    elif path.suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

def filter_cities(data: List[Dict[str, Any]], cities: List[str] = TARGET_CITIES) -> List[Dict[str, Any]]:
    """
    Filter routes to keep only those belonging to the specified cities.
    Assumes the route object has a 'city' key.
    """
    return [route for route in data if route.get("city") in cities]

def build_vocabulary(data: List[Dict[str, Any]], top_n: Optional[int] = None) -> Dict[str, int]:
    """
    Build a vocabulary of stations from the dataset.
    If top_n is provided, keep only the top_n most frequent stations.
    """
    station_counts = Counter()
    for route in data:
        if "stops" in route:
            for stop in route["stops"]:
                station_counts[stop] += 1
    
    if top_n:
        most_common = station_counts.most_common(top_n)
        vocab = {station: idx for idx, (station, _) in enumerate(most_common)}
        # Add UNKNOWN token
        vocab["<UNKNOWN>"] = len(vocab)
        return vocab
    
    return {station: idx for idx, station in enumerate(station_counts.keys())}

def apply_vocabulary_filter(data: List[Dict[str, Any]], vocab: Dict[str, int]) -> List[Dict[str, Any]]:
    """
    Apply vocabulary restriction to routes.
    Replaces unknown stations with <UNKNOWN>.
    """
    processed_data = []
    unknown_token = "<UNKNOWN>"
    
    for route in data:
        new_route = route.copy()
        new_stops = []
        for stop in route.get("stops", []):
            if stop in vocab:
                new_stops.append(stop)
            else:
                new_stops.append(unknown_token)
        new_route["stops"] = new_stops
        processed_data.append(new_route)
    
    return processed_data

def stratify_routes(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Stratify routes into short (<15), medium (15-30), and long (>30) categories.
    Saves the result as a Parquet file.
    
    Args:
        data: List of route dictionaries, each containing a 'stops' list.
        output_path: Path to save the output Parquet file.
    
    Raises:
        ValueError: If no routes are found or categories are not balanced (warns but proceeds).
    """
    if not data:
        raise ValueError("Input data is empty. Cannot stratify.")

    short_routes = []
    medium_routes = []
    long_routes = []

    for route in data:
        stops = route.get("stops", [])
        length = len(stops)
        
        route_record = {
            "route_id": route.get("route_id", "unknown"),
            "city": route.get("city", "unknown"),
            "stops": stops,
            "length": length
        }

        if length < SHORT_THRESHOLD:
            route_record["category"] = "short"
            short_routes.append(route_record)
        elif length <= MEDIUM_THRESHOLD:
            route_record["category"] = "medium"
            medium_routes.append(route_record)
        else:
            route_record["category"] = "long"
            long_routes.append(route_record)

    # Verify counts
    counts = {
        "short": len(short_routes),
        "medium": len(medium_routes),
        "long": len(long_routes)
    }
    total = sum(counts.values())

    if total == 0:
        raise ValueError("No routes found after stratification.")

    # Log distribution
    print(f"Stratification complete. Total routes: {total}")
    for cat, count in counts.items():
        pct = (count / total) * 100
        print(f"  {cat}: {count} ({pct:.2f}%)")

    # Create DataFrame
    all_routes = short_routes + medium_routes + long_routes
    df = pd.DataFrame(all_routes)

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save to Parquet
    df.to_parquet(output_path, index=False)
    print(f"Saved stratified routes to {output_path}")

def compute_route_metrics(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute basic metrics for each route (length, unique stops, etc.)."""
    metrics = []
    for route in data:
        stops = route.get("stops", [])
        m = {
            "route_id": route.get("route_id", "unknown"),
            "length": len(stops),
            "unique_stops": len(set(stops))
        }
        metrics.append(m)
    return metrics

def save_processed_data(data: List[Dict[str, Any]], output_path: str, file_format: str = "jsonl") -> None:
    """Save processed data to a file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    if file_format == "jsonl":
        with open(output_path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
    elif file_format == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    else:
        raise ValueError(f"Unsupported format: {file_format}")

def validate_output(file_path: str, expected_schema: Optional[Dict] = None) -> bool:
    """Basic validation of output file existence and non-empty content."""
    if not os.path.exists(file_path):
        return False
    if os.path.getsize(file_path) == 0:
        return False
    return True

def main():
    """
    Main entry point for preprocessing pipeline.
    Executes T006a -> T006b -> T006c sequence if needed, or specific steps.
    """
    # Configuration
    raw_data_path = "data/raw/transitlm_ground_truth.json"
    city_filtered_path = "data/processed/city_filtered_routes.jsonl"
    vocab_restricted_path = "data/processed/vocab_restricted_routes.jsonl"
    stratified_path = "data/processed/stratified_routes.parquet"
    
    # Check if raw data exists (T004 output)
    if not os.path.exists(raw_data_path):
        # Try the alternative path if T004 output was named differently
        alt_path = "data/raw/transitlm_sft_raw.jsonl"
        if os.path.exists(alt_path):
            raw_data_path = alt_path
        else:
            print(f"Error: Raw data not found at {raw_data_path} or {alt_path}.")
            sys.exit(1)

    # 1. Load Raw Data
    print(f"Loading raw data from {raw_data_path}...")
    raw_data = load_raw_dataset(raw_data_path)
    print(f"Loaded {len(raw_data)} routes.")

    # 2. Filter Cities (T006a)
    print("Filtering cities...")
    filtered_data = filter_cities(raw_data)
    print(f"Filtered to {len(filtered_data)} routes.")
    save_processed_data(filtered_data, city_filtered_path, "jsonl")

    # 3. Apply Vocabulary Restriction (T006b)
    # Assuming top 500 stations for demonstration, or use a specific number from config
    vocab_size = 500 
    print(f"Building vocabulary (top {vocab_size})...")
    vocab = build_vocabulary(filtered_data, top_n=vocab_size)
    print(f"Vocabulary size: {len(vocab)}")
    
    print("Applying vocabulary restriction...")
    vocab_restricted_data = apply_vocabulary_filter(filtered_data, vocab)
    save_processed_data(vocab_restricted_data, vocab_restricted_path, "jsonl")

    # 4. Stratify Routes (T006c)
    print("Stratifying routes...")
    stratify_routes(vocab_restricted_data, stratified_path)

    # Validate output
    if validate_output(stratified_path):
        print("T006c completed successfully.")
    else:
        print("T006c failed: Output validation error.")
        sys.exit(1)

if __name__ == "__main__":
    main()
