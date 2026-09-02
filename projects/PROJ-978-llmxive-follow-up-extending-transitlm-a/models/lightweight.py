"""
Lightweight Model Implementation for TransitLM Follow-up.

This module implements a deterministic, frequency-based retrieval model
for next-station prediction, adhering to Constitution Principle VII.
"""

import json
import sys
import os
import pickle
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Project root path resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"

def load_processed_routes(filepath: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load processed route data from a JSONL file.
    
    Args:
        filepath: Path to the JSONL file. Defaults to vocab_restricted_routes.jsonl.
        
    Returns:
        List of route dictionaries.
    """
    if filepath is None:
        filepath = DATA_PROCESSED_DIR / "vocab_restricted_routes.jsonl"
    
    routes = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                routes.append(json.loads(line))
    return routes

def build_transition_graph(routes: List[Dict[str, Any]]) -> Dict[str, Counter]:
    """
    Build a transition graph from route data.
    
    Args:
        routes: List of route dictionaries containing 'stations' or 'sequence'.
        
    Returns:
        Dictionary mapping station_id to Counter of next_station_id frequencies.
    """
    transition_counts = {}
    
    for route in routes:
        # Handle both 'stations' and 'sequence' keys depending on preprocessing
        stations = route.get('stations') or route.get('sequence')
        if not stations or len(stations) < 2:
            continue
        
        for i in range(len(stations) - 1):
            current = stations[i]
            next_station = stations[i + 1]
            
            if current not in transition_counts:
                transition_counts[current] = Counter()
            transition_counts[current][next_station] += 1
    
    return transition_counts

def get_top_n_transitions(
    current_station: str, 
    transition_graph: Dict[str, Counter], 
    n: int = 5
) -> List[Tuple[str, int]]:
    """
    Retrieve the top-N most frequent next stations for a given current station.
    
    Args:
        current_station: The current station ID.
        transition_graph: The pre-built transition graph.
        n: Number of top neighbors to return.
        
    Returns:
        List of (station_id, frequency) tuples, sorted by frequency (desc) then ID (asc).
    """
    if current_station not in transition_graph:
        return []
    
    counts = transition_graph[current_station]
    # Sort by frequency (descending), then by station ID (ascending) for tie-breaking
    sorted_transitions = sorted(
        counts.items(), 
        key=lambda x: (-x[1], x[0])
    )
    
    return sorted_transitions[:n]

def predict_next_station(
    current_station: str, 
    transition_graph: Dict[str, Counter], 
    adjacency_index: Optional[Dict[str, Any]] = None,
    use_index: bool = False
) -> Optional[str]:
    """
    Predict the next station using a deterministic, frequency-based lookup.
    
    This function implements the fixed lookup strategy mandated by 
    Constitution Principle VII.
    
    Strategy:
    1. If an adjacency_index is provided and use_index=True, it uses the 
       pre-computed top-N neighbors from the index.
    2. Otherwise, it uses the transition_graph (built from training data) 
       to determine the most frequent next station.
    
    Tie-breaking:
    - If multiple neighbors have the same frequency, the one with the 
      lowest station ID is selected.
    
    Args:
        current_station: The current station ID.
        transition_graph: Dictionary mapping station_id to Counter of next stations.
        adjacency_index: Optional pre-computed adjacency index (from T012a).
        use_index: If True, prioritize adjacency_index over transition_graph.
        
    Returns:
        The predicted next station ID, or None if no prediction can be made.
    """
    # If using adjacency index (retrieval-augmented)
    if use_index and adjacency_index:
        if current_station in adjacency_index:
            # The index should contain top-N neighbors with frequencies
            neighbors = adjacency_index[current_station]
            if neighbors:
                # Sort by frequency (desc), then ID (asc)
                sorted_neighbors = sorted(
                    neighbors, 
                    key=lambda x: (-x.get('frequency', 0), x.get('station_id', ''))
                )
                return sorted_neighbors[0]['station_id']
    
    # Fallback to frequency-based lookup from transition graph
    if current_station not in transition_graph:
        return None
    
    counts = transition_graph[current_station]
    if not counts:
        return None
    
    # Sort by frequency (descending), then by station ID (ascending) for tie-breaking
    # This satisfies the requirement: "If multiple neighbors have the same frequency, 
    # select the one with the lowest station ID."
    sorted_transitions = sorted(
        counts.items(), 
        key=lambda x: (-x[1], str(x[0]))
    )
    
    return sorted_transitions[0][0]

class LightweightModel:
    """
    A lightweight, encoder-only retrieval-augmented model for next-station prediction.
    
    This model uses deterministic frequency-based lookups instead of learned 
    parameters, making it extremely efficient for edge deployment.
    """
    
    def __init__(
        self, 
        transition_graph: Optional[Dict[str, Counter]] = None,
        adjacency_index: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the lightweight model.
        
        Args:
            transition_graph: Pre-built transition graph from training data.
            adjacency_index: Pre-computed adjacency index for retrieval augmentation.
        """
        self.transition_graph = transition_graph or {}
        self.adjacency_index = adjacency_index or {}
        self.use_index = bool(adjacency_index)
    
    def predict(self, current_station: str) -> Optional[str]:
        """
        Predict the next station given the current station.
        
        Args:
            current_station: The current station ID.
            
        Returns:
            The predicted next station ID.
        """
        return predict_next_station(
            current_station, 
            self.transition_graph, 
            self.adjacency_index, 
            self.use_index
        )
    
    def predict_batch(self, stations: List[str]) -> List[Optional[str]]:
        """
        Predict next stations for a batch of current stations.
        
        Args:
            stations: List of current station IDs.
            
        Returns:
            List of predicted next station IDs.
        """
        return [self.predict(station) for station in stations]

def main():
    """
    Main entry point for testing the lightweight model.
    
    This function loads the necessary data, builds the transition graph,
    and demonstrates prediction on sample routes.
    """
    print("Initializing Lightweight Model...")
    
    # Load processed routes
    routes_path = DATA_PROCESSED_DIR / "vocab_restricted_routes.jsonl"
    if not routes_path.exists():
        print(f"Error: Routes file not found at {routes_path}")
        sys.exit(1)
    
    routes = load_processed_routes(str(routes_path))
    print(f"Loaded {len(routes)} routes.")
    
    # Build transition graph
    transition_graph = build_transition_graph(routes)
    print(f"Built transition graph with {len(transition_graph)} unique stations.")
    
    # Try to load adjacency index (from T012a)
    adjacency_index_path = DATA_PROCESSED_DIR / "adjacency_index.pkl"
    adjacency_index = None
    if adjacency_index_path.exists():
        with open(adjacency_index_path, 'rb') as f:
            adjacency_index = pickle.load(f)
        print(f"Loaded adjacency index with {len(adjacency_index)} entries.")
    
    # Initialize model
    model = LightweightModel(transition_graph, adjacency_index)
    
    # Test predictions on a few sample routes
    print("\nTesting predictions on sample routes:")
    test_count = 0
    for route in routes[:5]:
        stations = route.get('stations') or route.get('sequence')
        if not stations or len(stations) < 2:
            continue
        
        current = stations[0]
        true_next = stations[1]
        predicted = model.predict(current)
        
        status = "✓" if predicted == true_next else "✗"
        print(f"  {status} Current: {current} -> Predicted: {predicted} | True: {true_next}")
        test_count += 1
    
    print(f"\nTested {test_count} transitions.")
    print("Lightweight model implementation complete.")

if __name__ == "__main__":
    main()