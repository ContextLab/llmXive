"""
Main pipeline orchestration for training GCN models on Small-World graphs.

This script iterates over all generated graphs in `data/raw/graphs.jsonl`,
and for each graph, trains two models: one with Cross-Entropy loss and one
with InfoNCE loss.

Key constraints implemented:
- Uses `utils.SAMPLE_SIZE` to determine the number of graphs to process.
- Resets the random seed to a common value before training each loss type
  on the same graph to ensure fair comparison (controlling for weight init).
- Sequential execution: CE first, then InfoNCE (or vice versa, but sequentially).
- Delegates actual training logic to `train.py`.
"""
import json
import os
import sys
from pathlib import Path

# Add project root to path to ensure imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils import seed_all, SAMPLE_SIZE, MAX_EPOCHS, CONVERGENCE_THRESHOLD
from losses import cross_entropy_loss, info_nce_loss, LinearProbe, compute_accuracy
from models import build_gcn_model, create_normalized_adjacency
from train import train_ce, train_infonce

# Constants
DATA_DIR = project_root / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
TRAJECTORIES_DIR = PROCESSED_DIR / "trajectories"

# Ensure output directories exist
TRAJECTORIES_DIR.mkdir(parents=True, exist_ok=True)

# Common seed for fair comparison between loss functions on the same graph
COMMON_TRAINING_SEED = 42

def load_graphs(graphs_path: Path) -> list:
    """Load graphs from the JSONL file."""
    if not graphs_path.exists():
        raise FileNotFoundError(f"Graphs file not found: {graphs_path}")
    
    graphs = []
    with open(graphs_path, 'r') as f:
        for line in f:
            if line.strip():
                graphs.append(json.loads(line))
    
    # Filter to SAMPLE_SIZE if more exist (though generation should match exactly)
    return graphs[:SAMPLE_SIZE]

def main():
    """
    Main entry point for the training pipeline.
    
    Iterates over all graphs, resets seed, and trains both CE and InfoNCE models.
    """
    graphs_file = RAW_DIR / "graphs.jsonl"
    
    print(f"Loading graphs from {graphs_file}...")
    graphs = load_graphs(graphs_file)
    print(f"Loaded {len(graphs)} graphs. Processing up to {SAMPLE_SIZE}.")
    
    if len(graphs) == 0:
        print("Error: No graphs found to process. Please run data generation first.")
        sys.exit(1)
    
    if len(graphs) < SAMPLE_SIZE:
        print(f"Warning: Only {len(graphs)} graphs found, but SAMPLE_SIZE is {SAMPLE_SIZE}. "
              f"Proceeding with available data.")
    
    # Process each graph
    for idx, graph_data in enumerate(graphs):
        graph_id = graph_data.get("id", f"graph_{idx}")
        beta = graph_data.get("beta")
        node_count = graph_data.get("node_count")
        
        print(f"\n--- Processing Graph {idx+1}/{len(graphs)}: ID={graph_id}, Beta={beta} ---")
        
        # 1. Prepare Data
        # Reconstruct adjacency and features from graph_data
        # Assuming graph_data contains 'edge_list' and 'labels'
        edge_list = graph_data.get("edge_list", [])
        labels = graph_data.get("labels", [])
        num_nodes = len(labels)
        
        if num_nodes == 0:
            print(f"Warning: Graph {graph_id} has no nodes. Skipping.")
            continue
        
        # Create adjacency matrix (simple list of edges -> torch tensor)
        # We expect edge_list to be a list of [u, v] pairs
        import torch
        edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
        x = torch.eye(num_nodes) # Simple identity features if none provided
        y = torch.tensor(labels, dtype=torch.long)
        
        adj = create_normalized_adjacency(edge_index, num_nodes)
        
        # 2. Train Cross-Entropy Model
        print(f"  Training Cross-Entropy model for {graph_id}...")
        seed_all(COMMON_TRAINING_SEED) # Reset seed for fair comparison
        
        ce_output_path = TRAJECTORIES_DIR / f"training_run_{graph_id}_ce.json"
        
        try:
            ce_result = train_ce(
                adj=adj,
                x=x,
                y=y,
                model_id=graph_id,
                loss_fn=cross_entropy_loss,
                output_path=ce_output_path,
                max_epochs=MAX_EPOCHS,
                convergence_threshold=CONVERGENCE_THRESHOLD,
                beta=beta,
                node_count=node_count
            )
            print(f"    CE Training complete. Converged: {ce_result['convergence_status']}, Steps: {ce_result['steps_to_convergence']}")
        except Exception as e:
            print(f"    Error training CE model: {e}")
            # Continue to next graph or loss type? Spec implies robustness.
            # We log error but continue to InfoNCE to maximize data collection.
            ce_result = {
                "graph_id": graph_id,
                "loss_type": "CE",
                "convergence_status": "failed",
                "error": str(e),
                "beta": beta,
                "node_count": node_count
            }
        
        # 3. Train InfoNCE Model
        print(f"  Training InfoNCE model for {graph_id}...")
        seed_all(COMMON_TRAINING_SEED) # Reset seed again for fair comparison
        
        infonce_output_path = TRAJECTORIES_DIR / f"training_run_{graph_id}_infonce.json"
        
        try:
            infonce_result = train_infonce(
                adj=adj,
                x=x,
                y=y,
                model_id=graph_id,
                loss_fn=info_nce_loss,
                probe_fn=LinearProbe,
                output_path=infonce_output_path,
                max_epochs=MAX_EPOCHS,
                convergence_threshold=CONVERGENCE_THRESHOLD,
                beta=beta,
                node_count=node_count
            )
            print(f"    InfoNCE Training complete. Converged: {infonce_result['convergence_status']}, Steps: {infonce_result['steps_to_convergence']}")
        except Exception as e:
            print(f"    Error training InfoNCE model: {e}")
            infonce_result = {
                "graph_id": graph_id,
                "loss_type": "InfoNCE",
                "convergence_status": "failed",
                "error": str(e),
                "beta": beta,
                "node_count": node_count
            }
        
        print(f"  Saved results to {ce_output_path} and {infonce_output_path}")
    
    print("\n--- Pipeline Complete ---")

if __name__ == "__main__":
    main()