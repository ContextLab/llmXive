"""
Unit tests for data/preprocess.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from collections import Counter

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.preprocess import (
    load_raw_dataset,
    filter_cities,
    build_vocabulary,
    apply_vocabulary_filter,
    stratify_routes,
    compute_route_metrics,
    save_processed_data,
    validate_output,
    TARGET_CITIES,
    TOP_N_VOCAB_SIZE,
    SHORT_THRESHOLD,
    MEDIUM_THRESHOLD,
    UNKNOWN_TOKEN
)

def test_filter_cities():
    """Test city filtering functionality."""
    routes = [
        {"city": "Beijing", "stations": ["A", "B", "C"]},
        {"city": "Shanghai", "stations": ["D", "E"]},
        {"city": "Guangzhou", "stations": ["F", "G", "H", "I"]},
        {"city": "Shenzhen", "stations": ["J"]},
        {"city": "Tokyo", "stations": ["K", "L"]}
    ]
    
    filtered = filter_cities(routes, TARGET_CITIES)
    
    assert len(filtered) == 4, f"Expected 4 routes, got {len(filtered)}"
    cities = {r["city"] for r in filtered}
    assert cities == TARGET_CITIES, f"Expected {TARGET_CITIES}, got {cities}"
    assert len([r for r in filtered if r["city"] == "Tokyo"]) == 0

def test_build_vocabulary():
    """Test vocabulary building with top-N restriction."""
    routes = [
        {"city": "Beijing", "stations": ["A", "A", "B"]},
        {"city": "Shanghai", "stations": ["A", "C", "C", "C"]},
        {"city": "Guangzhou", "stations": ["B", "B", "D"]}
    ]
    
    vocab_map, unknown_stations = build_vocabulary(routes, top_n=2)
    
    # A appears 3 times, C appears 3 times, B appears 3 times, D appears 1 time
    # With top_n=2, we should get A and C (or A and B depending on tie-breaking)
    assert len(vocab_map) == 2, f"Expected vocabulary size 2, got {len(vocab_map)}"
    assert UNKNOWN_TOKEN not in vocab_map.values()
    
    # Check that unknown stations exist
    assert len(unknown_stations) > 0

def test_apply_vocabulary_filter():
    """Test vocabulary filtering with UNKNOWN token."""
    routes = [
        {"city": "Beijing", "stations": ["A", "B", "C"]},
        {"city": "Shanghai", "stations": ["D", "E"]}
    ]
    
    vocab_map = {"A": 0, "B": 1}
    unknown_token = "<UNKNOWN>"
    
    filtered = apply_vocabulary_filter(routes, vocab_map, unknown_token)
    
    # First route: A->0, B->1, C->UNKNOWN
    assert filtered[0]["stations"][0] == 0
    assert filtered[0]["stations"][1] == 1
    assert filtered[0]["stations"][2] == unknown_token
    
    # Second route: D->UNKNOWN, E->UNKNOWN
    assert filtered[1]["stations"][0] == unknown_token
    assert filtered[1]["stations"][1] == unknown_token

def test_stratify_routes():
    """Test route stratification by length."""
    routes = [
        {"city": "Beijing", "stations": ["A"] * 10},    # Short
        {"city": "Shanghai", "stations": ["B"] * 15},   # Medium (boundary)
        {"city": "Guangzhou", "stations": ["C"] * 20},  # Medium
        {"city": "Shenzhen", "stations": ["D"] * 30},   # Medium (boundary)
        {"city": "Beijing", "stations": ["E"] * 31},    # Long
        {"city": "Shanghai", "stations": ["F"] * 50}    # Long
    ]
    
    stratified = stratify_routes(routes)
    
    assert len(stratified["short"]) == 1, f"Expected 1 short, got {len(stratified['short'])}"
    assert len(stratified["medium"]) == 3, f"Expected 3 medium, got {len(stratified['medium'])}"
    assert len(stratified["long"]) == 2, f"Expected 2 long, got {len(stratified['long'])}"
    
    # Verify thresholds
    for route in stratified["short"]:
        assert len(route["stations"]) < SHORT_THRESHOLD
    
    for route in stratified["medium"]:
        assert SHORT_THRESHOLD <= len(route["stations"]) <= MEDIUM_THRESHOLD
    
    for route in stratified["long"]:
        assert len(route["stations"]) > MEDIUM_THRESHOLD

def test_compute_route_metrics():
    """Test route metrics computation."""
    routes = [
        {"city": "Beijing", "stations": ["A", "B", "C"]},
        {"city": "Shanghai", "stations": ["D", "E"]}
    ]
    
    processed = compute_route_metrics(routes)
    
    assert processed[0]["route_length"] == 3
    assert processed[0]["city"] == "Beijing"
    assert processed[1]["route_length"] == 2
    assert processed[1]["city"] == "Shanghai"

def test_save_and_validate_output():
    """Test saving and validation of processed data."""
    routes = [
        {"city": "Beijing", "stations": ["A", "B"]},
        {"city": "Shanghai", "stations": ["C", "D", "E"]},
        {"city": "Guangzhou", "stations": ["F"] * 20},
        {"city": "Shenzhen", "stations": ["G"] * 35}
    ]
    
    # Build vocabulary
    vocab_map, _ = build_vocabulary(routes, top_n=10)
    
    # Apply filter
    filtered = apply_vocabulary_filter(routes, vocab_map, UNKNOWN_TOKEN)
    
    # Stratify
    stratified = stratify_routes(filtered)
    
    processed_data = {
        "routes": filtered,
        "stratified": stratified
    }
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # Save data
        save_processed_data(processed_data, temp_path, vocab_map, UNKNOWN_TOKEN)
        
        # Validate
        assert validate_output(temp_path) is True
        
        # Load and verify structure
        with open(temp_path, 'r') as f:
            data = json.load(f)
        
        assert "routes" in data
        assert "stratified" in data
        assert "metadata" in data
        assert len(data["routes"]) == 4
        assert len(data["stratified"]["short"]) == 2
        assert len(data["stratified"]["medium"]) == 1
        assert len(data["stratified"]["long"]) == 1
        
    finally:
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

def test_vocabulary_size_limit():
    """Test that vocabulary is limited to TOP_N size."""
    # Create routes with many unique stations
    routes = []
    for i in range(100):
        routes.append({
            "city": "Beijing",
            "stations": [f"Station_{j}" for j in range(i + 1)]
        })
    
    vocab_map, unknown_stations = build_vocabulary(routes, top_n=TOP_N_VOCAB_SIZE)
    
    assert len(vocab_map) <= TOP_N_VOCAB_SIZE
    assert len(unknown_stations) > 0

if __name__ == "__main__":
    test_filter_cities()
    test_build_vocabulary()
    test_apply_vocabulary_filter()
    test_stratify_routes()
    test_compute_route_metrics()
    test_save_and_validate_output()
    test_vocabulary_size_limit()
    print("All tests passed!")
