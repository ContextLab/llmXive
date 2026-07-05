import json
import os
import csv
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import torch
import numpy as np

from models.episodic_chunk import EpisodicChunk
from models.memory_slot import MemoryGrid, MemorySlot
from models.coordinate_assigner import CoordinateAssigner

# --- Existing Functions (Preserved for compatibility) ---

def compute_interference_distance(
    spatial_grid: MemoryGrid,
    baseline_grid: Optional[MemoryGrid] = None
) -> float:
    """
    Compute the interference distance metric.
    For the spatial variant, this is the average Euclidean distance between
    coordinates of chunks that share a semantic cluster but are stored in
    different slots, normalized by the grid size.
    """
    if spatial_grid is None:
        return 0.0
    
    # Placeholder logic to satisfy compilation; real implementation assumes
    # populated grid slots with coordinate data.
    total_dist = 0.0
    count = 0
    
    # Iterate over slots to find chunks
    for slot in spatial_grid.slots:
        if slot.occupancy > 0 and slot.chunk is not None:
            # Calculate distance from center or other metrics
            if slot.coordinate is not None:
                # Simple distance from origin as a proxy for distribution spread
                dist = math.sqrt(slot.coordinate[0]**2 + slot.coordinate[1]**2)
                total_dist += dist
                count += 1
    
    return total_dist / count if count > 0 else 0.0

def compute_exact_match_recall(predictions: List[str], references: List[str]) -> float:
    """Compute exact match recall."""
    if not references:
        return 0.0
    matches = sum(1 for p, r in zip(predictions, references) if p == r)
    return matches / len(references)

def evaluate_model_on_dataset(model, dataset: List[Dict], device: str = "cpu") -> Dict[str, Any]:
    """Evaluate a model on a dataset and return metrics."""
    predictions = []
    references = []
    
    # Mock evaluation loop
    for item in dataset:
        # In a real scenario, this would run model inference
        pred = item.get("predicted_answer", "mock")
        ref = item.get("answer", "mock_ref")
        predictions.append(pred)
        references.append(ref)
    
    recall = compute_exact_match_recall(predictions, references)
    return {"exact_match_recall": recall, "total_samples": len(references)}

def run_evaluation_for_seed(model, dataset: List[Dict], seed: int) -> Dict[str, Any]:
    """Run evaluation for a specific random seed."""
    results = evaluate_model_on_dataset(model, dataset)
    results["seed"] = seed
    return results

def aggregate_results_by_seed(all_results: List[Dict]) -> Dict[str, Any]:
    """Aggregate results from multiple seeds."""
    recalls = [r["exact_match_recall"] for r in all_results]
    return {
        "seeds": [r["seed"] for r in all_results],
        "accuracies": recalls,
        "mean_recall": float(np.mean(recalls)) if recalls else 0.0,
        "std_recall": float(np.std(recalls)) if recalls else 0.0
    }

def log_slot_occupancy_distribution(
    grid: MemoryGrid,
    epoch: int,
    output_dir: str,
    run_id: str
) -> str:
    """
    Log the slot occupancy distribution per epoch.
    Output: artifacts/results/slot_occupancy_epoch_{epoch}.csv
    """
    output_path = Path(output_dir) / f"slot_occupancy_epoch_{epoch}.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["slot_id", "occupancy", "coordinate_x", "coordinate_y"])
        for i, slot in enumerate(grid.slots):
            coord = slot.coordinate if slot.coordinate else (0, 0)
            writer.writerow([i, slot.occupancy, coord[0], coord[1]])
    
    return str(output_path)

# --- New Function for T026: Coordinate Variance Logger ---

def log_coordinate_variance(
    grid: MemoryGrid,
    epoch: int,
    output_dir: str,
    run_id: str
) -> str:
    """
    Implement coordinate variance logger.
    Records variance of assigned coordinates per epoch.
    Output: artifacts/results/coordinate_variance_epoch_{epoch}.csv
    
    The variance is calculated for the X and Y dimensions separately
    across all occupied slots in the memory grid.
    """
    output_path = Path(output_dir) / f"coordinate_variance_epoch_{epoch}.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Collect coordinates from occupied slots
    x_coords = []
    y_coords = []
    
    for slot in grid.slots:
        if slot.occupancy > 0 and slot.coordinate is not None:
            x_coords.append(slot.coordinate[0])
            y_coords.append(slot.coordinate[1])
    
    # Calculate variance
    if len(x_coords) > 1:
        var_x = float(np.var(x_coords, ddof=1)) # Sample variance
        var_y = float(np.var(y_coords, ddof=1))
    elif len(x_coords) == 1:
        var_x = 0.0
        var_y = 0.0
    else:
        var_x = float('nan')
        var_y = float('nan')
    
    # Write to CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "variance_x", "variance_y", "occupied_slots_count"])
        writer.writerow([epoch, var_x, var_y, len(x_coords)])
    
    return str(output_path)

def main():
    """
    Main entry point for metrics evaluation and logging.
    Demonstrates the usage of the coordinate variance logger.
    """
    # Setup dummy data for demonstration if run standalone
    # In the actual pipeline, this is called by the training loop
    output_dir = "artifacts/results"
    run_id = "demo_run"
    
    # Create a mock grid
    from models.memory_slot import MemoryGrid
    grid = MemoryGrid(rows=10, cols=10)
    
    # Simulate some occupancy for testing
    assigner = CoordinateAssigner(grid_size=(10, 10))
    for i in range(5):
        chunk = EpisodicChunk(content=f"sample_{i}", timestamp=f"2026-01-01")
        coord = assigner.assign_coordinate(chunk)
        grid.place_chunk_in_slot(chunk, coord)
    
    # Log variance
    log_coordinate_variance(grid, epoch=1, output_dir=output_dir, run_id=run_id)
    print(f"Coordinate variance logged to {output_dir}/coordinate_variance_epoch_1.csv")

if __name__ == "__main__":
    main()