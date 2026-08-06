"""
Lightweight Model Implementation for TransitLM Follow-up.

Implements a deterministic fixed-lookup strategy for next-station prediction
without GPU acceleration. This model retrieves top-N neighbors from a
pre-built transition graph and selects the highest frequency transition.
"""
import json
import sys
import os
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

# Import configuration
from config import Config, get_env_config

# Import data utilities
from data.graph_utils import load_processed_routes


def build_transition_graph(processed_routes: List[Dict[str, Any]], top_n: int = 5) -> Dict[str, Dict[str, int]]:
    """
    Build a transition graph from processed routes.
    
    Args:
        processed_routes: List of route dictionaries containing station sequences.
        top_n: Number of top transitions to consider during prediction.
    
    Returns:
        A nested dictionary where:
        - Outer key: current station
        - Inner key: next station
        - Value: frequency count of the transition
    """
    transition_counts: Dict[str, Counter] = {}
    
    for route in processed_routes:
        stations = route.get("stations", [])
        if len(stations) < 2:
            continue
        
        # Iterate through station pairs in the route
        for i in range(len(stations) - 1):
            current_station = stations[i]
            next_station = stations[i + 1]
            
            if current_station not in transition_counts:
                transition_counts[current_station] = Counter()
            
            transition_counts[current_station][next_station] += 1
    
    # Convert to top-N transitions for efficiency
    transition_graph = {}
    for station, counter in transition_counts.items():
        # Get top N most frequent transitions
        top_transitions = counter.most_common(top_n)
        transition_graph[station] = {
            next_st: count for next_st, count in top_transitions
        }
    
    return transition_graph


def get_top_n_transitions(
    transition_graph: Dict[str, Dict[str, int]], 
    current_station: str, 
    top_n: int = 5
) -> List[Tuple[str, int]]:
    """
    Retrieve the top-N most frequent transitions from a given station.
    
    Args:
        transition_graph: The pre-built transition graph.
        current_station: The current station to query.
        top_n: Maximum number of transitions to return.
    
    Returns:
        List of tuples (next_station, frequency) sorted by frequency descending.
    """
    if current_station not in transition_graph:
        return []
    
    transitions = transition_graph[current_station]
    sorted_transitions = sorted(transitions.items(), key=lambda x: x[1], reverse=True)
    return sorted_transitions[:top_n]


def predict_next_station(
    transition_graph: Dict[str, Dict[str, int]], 
    current_station: str, 
    visited_stations: Optional[Set[str]] = None,
    top_n: int = 5
) -> Optional[str]:
    """
    Predict the next station using a deterministic fixed-lookup strategy.
    
    Strategy:
    1. Retrieve top-N most frequent transitions from the current station.
    2. Filter out stations that have already been visited (if provided).
    3. Select the station with the highest frequency among valid candidates.
    4. If all top-N are visited, return the most frequent unvisited station 
       from the full transition list, or None if no valid transition exists.
    
    Args:
        transition_graph: The pre-built transition graph.
        current_station: The current station.
        visited_stations: Set of stations already visited in the current route.
        top_n: Number of top transitions to consider initially.
    
    Returns:
        The predicted next station, or None if no valid prediction can be made.
    """
    if current_station not in transition_graph:
        return None
    
    visited = visited_stations or set()
    
    # Get top-N transitions
    top_transitions = get_top_n_transitions(transition_graph, current_station, top_n)
    
    if not top_transitions:
        return None
    
    # Try to find an unvisited station in top-N
    for next_station, _ in top_transitions:
        if next_station not in visited:
            return next_station
    
    # If all top-N are visited, try to find any unvisited station
    all_transitions = sorted(
        transition_graph[current_station].items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    for next_station, _ in all_transitions:
        if next_station not in visited:
            return next_station
    
    # No valid transition found
    return None


class LightweightModel:
    """
    A lightweight, encoder-only retrieval-augmented model for transit prediction.
    
    This model uses a deterministic fixed-lookup strategy based on historical
    transition frequencies. It does not require GPU acceleration and is designed
    for resource-constrained environments.
    """
    
    def __init__(
        self, 
        config: Optional[Config] = None,
        top_n: int = 5
    ):
        """
        Initialize the lightweight model.
        
        Args:
            config: Configuration object (optional).
            top_n: Number of top transitions to consider during prediction.
        """
        self.config = config or get_env_config()
        self.top_n = top_n
        self.transition_graph: Optional[Dict[str, Dict[str, int]]] = None
        self.is_built = False
    
    def build_from_processed_routes(self, processed_routes: List[Dict[str, Any]]) -> None:
        """
        Build the transition graph from processed routes.
        
        Args:
            processed_routes: List of route dictionaries.
        """
        self.transition_graph = build_transition_graph(processed_routes, self.top_n)
        self.is_built = True
    
    def predict_route(self, route: Dict[str, Any]) -> List[str]:
        """
        Predict a full route starting from the first station.
        
        Args:
            route: A route dictionary containing at least the starting station.
        
        Returns:
            A list of predicted stations forming the route.
        """
        if not self.is_built:
            raise RuntimeError("Model not built. Call build_from_processed_routes first.")
        
        if "stations" not in route or not route["stations"]:
            return []
        
        predicted_route = [route["stations"][0]]
        visited = {predicted_route[0]}
        
        # Predict subsequent stations
        while True:
            current_station = predicted_route[-1]
            next_station = predict_next_station(
                self.transition_graph, 
                current_station, 
                visited, 
                self.top_n
            )
            
            if next_station is None:
                break
            
            predicted_route.append(next_station)
            visited.add(next_station)
            
            # Prevent infinite loops (safety check)
            if len(predicted_route) > 100:
                break
        
        return predicted_route
    
    def predict_single_step(
        self, 
        current_station: str, 
        visited_stations: Optional[Set[str]] = None
    ) -> Optional[str]:
        """
        Predict the next single station from a given position.
        
        Args:
            current_station: The current station.
            visited_stations: Set of already visited stations.
        
        Returns:
            The predicted next station, or None.
        """
        if not self.is_built:
            raise RuntimeError("Model not built. Call build_from_processed_routes first.")
        
        return predict_next_station(
            self.transition_graph, 
            current_station, 
            visited_stations, 
            self.top_n
        )


def load_processed_routes(data_path: str) -> List[Dict[str, Any]]:
    """
    Load processed routes from a JSON file.
    
    Args:
        data_path: Path to the processed routes JSON file.
    
    Returns:
        List of route dictionaries.
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed routes file not found: {data_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list format and dict with "routes" key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "routes" in data:
        return data["routes"]
    else:
        raise ValueError("Invalid data format in processed routes file")


def main():
    """
    Main entry point for testing the lightweight model.
    
    This function:
    1. Loads processed routes from data/processed/
    2. Builds the transition graph
    3. Runs predictions on a sample route
    4. Outputs the results to data/analysis/lightweight_predictions.json
    """
    # Configuration
    config = get_env_config()
    processed_data_path = config.PROCESSED_DATA_PATH
    output_path = config.OUTPUT_ANALYSIS_PATH / "lightweight_predictions.json"
    
    print(f"Loading processed routes from: {processed_data_path}")
    try:
        routes = load_processed_routes(processed_data_path)
        print(f"Loaded {len(routes)} routes")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Build model
    print("Building transition graph...")
    model = LightweightModel(config=config, top_n=5)
    model.build_from_processed_routes(routes)
    print(f"Transition graph built with {len(model.transition_graph)} stations")
    
    # Run predictions on a sample of routes
    sample_size = min(100, len(routes))
    predictions = []
    
    print(f"Running predictions on {sample_size} sample routes...")
    for i, route in enumerate(routes[:sample_size]):
        if "stations" not in route or not route["stations"]:
            continue
        
        predicted = model.predict_route(route)
        
        predictions.append({
            "route_id": route.get("id", f"route_{i}"),
            "original_stations": route["stations"][:10],  # First 10 for brevity
            "predicted_stations": predicted[:10],  # First 10 for brevity
            "original_length": len(route["stations"]),
            "predicted_length": len(predicted),
            "overlap": len(set(route["stations"]) & set(predicted))
        })
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_data = {
        "config": {
            "top_n": model.top_n,
            "total_routes_processed": len(routes),
            "sample_size": len(predictions)
        },
        "predictions": predictions
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Predictions saved to: {output_path}")
    print(f"Successfully processed {len(predictions)} routes")


if __name__ == "__main__":
    main()