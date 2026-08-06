"""
Preprocess the TransitLM dataset:
1. Load raw dataset from data/raw/
2. Filter for four Chinese cities: Beijing, Shanghai, Guangzhou, Shenzhen
3. Build vocabulary and apply top-N restriction with <UNKNOWN> token
4. Stratify routes into short (<15), medium (15-30), and long (>30) categories
5. Save processed data to data/processed/
"""
import json
import os
import sys
import hashlib
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Constants
TARGET_CITIES = {"Beijing", "Shanghai", "Guangzhou", "Shenzhen"}
TOP_N_VOCAB = 5000
UNKNOWN_TOKEN = "<UNKNOWN>"
SHORT_THRESHOLD = 15
MEDIUM_THRESHOLD = 30

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_raw_dataset(raw_dir: Path) -> List[Dict[str, Any]]:
    """Load the raw TransitLM dataset from data/raw/."""
    raw_file = raw_dir / "transitlm_sft.json"
    if not raw_file.exists():
        # Try alternative filename
        raw_file = raw_dir / "transitlm.json"
    
    if not raw_file.exists():
        raise FileNotFoundError(
            f"Raw dataset not found in {raw_dir}. "
            "Please run data/download.py first to fetch the dataset."
        )
    
    with open(raw_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected dataset format in {raw_file}")

def filter_cities(routes: List[Dict[str, Any]], cities: set) -> List[Dict[str, Any]]:
    """Filter routes for specified cities."""
    filtered = []
    for route in routes:
        # Handle different possible field names for city
        city = route.get("city") or route.get("origin_city") or route.get("destination_city")
        if city in cities:
            filtered.append(route)
    return filtered

def build_vocabulary(routes: List[Dict[str, Any]], top_n: int) -> Dict[str, int]:
    """Build vocabulary from route stations with top-N restriction."""
    station_counter = Counter()
    
    for route in routes:
        stations = route.get("stations", []) or route.get("stops", [])
        if isinstance(stations, list):
            for station in stations:
                if isinstance(station, str):
                    station_counter[station] += 1
    
    # Get top-N most common stations
    most_common = station_counter.most_common(top_n)
    vocab = {station: idx for idx, (station, _) in enumerate(most_common)}
    
    # Add UNKNOWN token
    vocab[UNKNOWN_TOKEN] = len(vocab)
    
    return vocab

def apply_vocabulary_filter(
    routes: List[Dict[str, Any]], 
    vocab: Dict[str, int]
) -> List[Dict[str, Any]]:
    """Apply vocabulary filter to routes, replacing unknown stations with <UNKNOWN>."""
    filtered_routes = []
    
    for route in routes:
        stations = route.get("stations", []) or route.get("stops", [])
        if not isinstance(stations, list):
            continue
        
        filtered_stations = []
        for station in stations:
            if isinstance(station, str):
                if station in vocab:
                    filtered_stations.append(vocab[station])
                else:
                    filtered_stations.append(vocab[UNKNOWN_TOKEN])
        
        # Create a copy of the route with filtered stations
        new_route = route.copy()
        new_route["stations"] = filtered_stations
        new_route["station_tokens"] = filtered_stations
        new_route["original_stations"] = stations  # Keep original for reference
        
        filtered_routes.append(new_route)
    
    return filtered_routes

def stratify_routes(routes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Stratify routes into short, medium, and long categories based on station count."""
    strata = {
        "short": [],    # < 15 stations
        "medium": [],   # 15-30 stations
        "long": []      # > 30 stations
    }
    
    for route in routes:
        stations = route.get("stations", []) or route.get("station_tokens", [])
        if not isinstance(stations, list):
            continue
        
        length = len(stations)
        
        if length < SHORT_THRESHOLD:
            strata["short"].append(route)
        elif length <= MEDIUM_THRESHOLD:
            strata["medium"].append(route)
        else:
            strata["long"].append(route)
    
    return strata

def compute_route_metrics(routes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute metrics for the processed routes."""
    total_routes = len(routes)
    if total_routes == 0:
        return {
            "total_routes": 0,
            "avg_length": 0,
            "min_length": 0,
            "max_length": 0
        }
    
    lengths = [len(r.get("stations", [])) for r in routes if r.get("stations")]
    
    return {
        "total_routes": total_routes,
        "avg_length": sum(lengths) / len(lengths) if lengths else 0,
        "min_length": min(lengths) if lengths else 0,
        "max_length": max(lengths) if lengths else 0
    }

def save_processed_data(
    strata: Dict[str, List[Dict[str, Any]]],
    vocab: Dict[str, int],
    output_dir: Path,
    metrics: Dict[str, Any]
) -> Path:
    """Save processed data to data/processed/."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save stratified routes
    for category, routes in strata.items():
        output_file = output_dir / f"routes_{category}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(routes, f, ensure_ascii=False, indent=2)
    
    # Save vocabulary
    vocab_file = output_dir / "vocabulary.json"
    with open(vocab_file, "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=2)
    
    # Save combined dataset
    all_routes = []
    for routes in strata.values():
        all_routes.extend(routes)
    
    combined_file = output_dir / "transitlm_processed.json"
    with open(combined_file, "w", encoding="utf-8") as f:
        json.dump(all_routes, f, ensure_ascii=False, indent=2)
    
    # Save metadata
    metadata = {
        "vocabulary_size": len(vocab),
        "target_cities": list(TARGET_CITIES),
        "top_n_vocab": TOP_N_VOCAB,
        "stratification_thresholds": {
            "short": f"< {SHORT_THRESHOLD}",
            "medium": f"{SHORT_THRESHOLD}-{MEDIUM_THRESHOLD}",
            "long": f"> {MEDIUM_THRESHOLD}"
        },
        "route_counts": {
            "short": len(strata["short"]),
            "medium": len(strata["medium"]),
            "long": len(strata["long"]),
            "total": len(all_routes)
        },
        "route_metrics": metrics
    }
    
    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return combined_file

def validate_output(output_dir: Path) -> bool:
    """Validate that processed output files exist and are non-empty."""
    required_files = [
        "routes_short.json",
        "routes_medium.json", 
        "routes_long.json",
        "vocabulary.json",
        "transitlm_processed.json",
        "metadata.json"
    ]
    
    for filename in required_files:
        file_path = output_dir / filename
        if not file_path.exists():
            print(f"ERROR: Missing required file: {file_path}")
            return False
        if file_path.stat().st_size == 0:
            print(f"ERROR: Empty file: {file_path}")
            return False
    
    # Validate metadata contains expected keys
    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    required_keys = ["vocabulary_size", "target_cities", "route_counts"]
    for key in required_keys:
        if key not in metadata:
            print(f"ERROR: Missing metadata key: {key}")
            return False
    
    return True

def main():
    """Main entry point for preprocessing."""
    print("Starting TransitLM dataset preprocessing...")
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    
    # Step 1: Load raw dataset
    print(f"Loading raw dataset from {raw_dir}...")
    routes = load_raw_dataset(raw_dir)
    print(f"Loaded {len(routes)} routes")
    
    # Step 2: Filter for target cities
    print(f"Filtering for cities: {TARGET_CITIES}")
    filtered_routes = filter_cities(routes, TARGET_CITIES)
    print(f"Filtered to {len(filtered_routes)} routes for target cities")
    
    if len(filtered_routes) == 0:
        raise ValueError("No routes found for target cities. Check city names in dataset.")
    
    # Step 3: Build vocabulary
    print(f"Building vocabulary with top-{TOP_N_VOCAB} restriction...")
    vocab = build_vocabulary(filtered_routes, TOP_N_VOCAB)
    print(f"Vocabulary size: {len(vocab)} (including <UNKNOWN>)")
    
    # Step 4: Apply vocabulary filter
    print("Applying vocabulary filter...")
    vocab_filtered_routes = apply_vocabulary_filter(filtered_routes, vocab)
    
    # Step 5: Stratify routes
    print("Stratifying routes by length...")
    strata = stratify_routes(vocab_filtered_routes)
    print(f"  Short (<{SHORT_THRESHOLD}): {len(strata['short'])} routes")
    print(f"  Medium ({SHORT_THRESHOLD}-{MEDIUM_THRESHOLD}): {len(strata['medium'])} routes")
    print(f"  Long (>{MEDIUM_THRESHOLD}): {len(strata['long'])} routes")
    
    # Step 6: Compute metrics
    print("Computing route metrics...")
    metrics = compute_route_metrics(vocab_filtered_routes)
    
    # Step 7: Save processed data
    print(f"Saving processed data to {processed_dir}...")
    output_file = save_processed_data(strata, vocab, processed_dir, metrics)
    
    # Step 8: Validate output
    print("Validating output...")
    if not validate_output(processed_dir):
        raise RuntimeError("Output validation failed")
    
    # Compute checksum
    checksum = compute_sha256(output_file)
    print(f"Output file: {output_file}")
    print(f"SHA256 checksum: {checksum}")
    print("Preprocessing completed successfully!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
