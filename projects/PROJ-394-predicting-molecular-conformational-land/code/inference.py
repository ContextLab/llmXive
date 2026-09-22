"""
Inference script to encode held-out SMILES using the trained VAE.

This script implements FR-003: "The model must be able to encode unseen
molecular graphs into the latent space for downstream tasks."

It loads a trained checkpoint, processes a set of held-out SMILES strings,
and outputs their latent vectors to a JSON file.
"""
import os
import json
import argparse
import torch
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports
from config import get_config, get_paths, get_hyperparams, reset_config
from utils.logging import get_project_logger, log_event
from utils.seeds import set_global_seed
from data.preprocess import smiles_to_graph
from models.vae import MolecularVAE, create_vae_model


def load_checkpoint(checkpoint_path: str, device: torch.device) -> Dict[str, Any]:
    """
    Load a VAE checkpoint file.
    """
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    
    logger = get_project_logger("inference")
    logger.info(f"Loading checkpoint from {checkpoint_path}")
    
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    logger.info(f"Checkpoint loaded. Epoch: {checkpoint.get('epoch', 'N/A')}, Loss: {checkpoint.get('loss', 'N/A')}")
    
    return checkpoint


def encode_smiles_batch(
    model: MolecularVAE,
    smiles_list: List[str],
    device: torch.device,
    batch_size: int = 32
) -> List[Dict[str, Any]]:
    """
    Encode a list of SMILES strings into latent vectors.
    
    Returns a list of dictionaries containing:
    - smiles: original string
    - latent_vector: list of floats (latent_dim)
    - success: boolean
    - error: optional error message
    """
    logger = get_project_logger("inference")
    model.eval()
    results = []
    
    with torch.no_grad():
        for i in range(0, len(smiles_list), batch_size):
            batch_smiles = smiles_list[i : i + batch_size]
            batch_data = []
            valid_indices = []
            
            # Pre-process batch
            for idx, smi in enumerate(batch_smiles):
                try:
                    graph_data = smiles_to_graph(smi)
                    if graph_data is None:
                        logger.warning(f"Skipping invalid SMILES at index {i+idx}: {smi}")
                        results.append({
                            "smiles": smi,
                            "latent_vector": None,
                            "success": False,
                            "error": "Invalid SMILES or graph conversion failure"
                        })
                        continue
                    
                    batch_data.append(graph_data)
                    valid_indices.append(len(results)) # Map back to results index if needed, but here we append directly
                    results.append({
                        "smiles": smi,
                        "latent_vector": None, # Placeholder
                        "success": False,
                        "error": None
                    })
                except Exception as e:
                    logger.error(f"Error processing SMILES '{smi}': {e}")
                    results.append({
                        "smiles": smi,
                        "latent_vector": None,
                        "success": False,
                        "error": str(e)
                    })
            
            if not batch_data:
                continue

            # Prepare tensors for the model
            # The model expects specific keys based on the training loop in train.py
            # Assuming graph_data has: 'node_features', 'edge_index', 'edge_features', 'num_nodes'
            batch_node_features = torch.stack([d['node_features'] for d in batch_data]).to(device)
            batch_edge_index = torch.stack([d['edge_index'] for d in batch_data]).to(device)
            # Handle edge_features if present and required by the specific MPNN implementation
            # If the model expects a single edge_feature tensor or list, adapt accordingly.
            # Based on typical MPNN implementations in this context:
            if 'edge_features' in batch_data[0]:
                batch_edge_features = torch.stack([d['edge_features'] for d in batch_data]).to(device)
            else:
                batch_edge_features = None

            batch_num_nodes = torch.tensor([d['num_nodes'] for d in batch_data]).to(device)

            # Forward pass
            try:
                # The model's encode method or forward pass usually returns (mu, logvar) or just mu
                # We assume create_vae_model returns a MolecularVAE instance with an encode method
                # or we call forward and extract mu.
                # Let's assume a method `encode` exists as per FR-003 requirement for inference.
                # If not, we might need to call model(x) and extract mu from the return tuple.
                # Looking at typical VAE patterns: model(x) -> (recon, mu, logvar)
                
                # Attempting to call encode if available, else forward
                if hasattr(model, 'encode'):
                    mu, _ = model.encode(batch_node_features, batch_edge_index, batch_num_nodes, 
                                         edge_features=batch_edge_features)
                else:
                    # Fallback: forward pass returns (recon, mu, logvar)
                    _, mu, _ = model(batch_node_features, batch_edge_index, batch_num_nodes,
                                   edge_features=batch_edge_features)
                
                # mu shape: [batch_size, latent_dim]
                latent_vectors = mu.cpu().numpy().tolist()
                
                # Update results for valid indices
                valid_count = 0
                for j, res_idx in enumerate(range(len(results))):
                    # We need to map back to the specific result entry for this batch
                    # Since we appended in order, we can iterate the batch_data length
                    pass
                
                # Re-iterating to update specific results
                current_result_idx = 0
                # We need to track which result entries correspond to this batch
                # Let's rebuild the logic to update in place more cleanly
                
                # Actually, simpler: iterate through batch_data and update the corresponding result
                # We need to know the index in `results` for each item in `batch_data`
                # Since we appended sequentially, the indices are contiguous for the valid ones in this batch.
                
                # Let's find the start index in `results` for this batch
                # This is tricky because we appended failures too.
                # Better approach: build a list of (smiles, success, error) first, then fill latent vectors.
                pass 
                
            except Exception as e:
                logger.error(f"Encoding failed for batch starting at index {i}: {e}")
                # Mark all in this batch as failed
                for _ in range(len(batch_data)):
                    # This is messy. Let's refactor the loop structure.
                    pass
                continue

            # Refactored logic for updating results:
            # We will rebuild the loop to be cleaner.
            pass

    # Clean implementation of the loop
    results = []
    model.eval()
    
    with torch.no_grad():
        for i in range(0, len(smiles_list), batch_size):
            batch_smiles = smiles_list[i : i + batch_size]
            processed_batch = []
            
            # 1. Pre-process and validate
            for smi in batch_smiles:
                try:
                    graph = smiles_to_graph(smi)
                    if graph is None:
                        raise ValueError("Graph conversion returned None")
                    processed_batch.append((smi, graph, None))
                except Exception as e:
                    results.append({
                        "smiles": smi,
                        "latent_vector": None,
                        "success": False,
                        "error": str(e)
                    })
            
            if not processed_batch:
                continue
            
            # 2. Tensor conversion
            try:
                node_feats = torch.stack([g['node_features'] for _, g, _ in processed_batch]).to(device)
                edge_idx = torch.stack([g['edge_index'] for _, g, _ in processed_batch]).to(device)
                num_nodes = torch.tensor([g['num_nodes'] for _, g, _ in processed_batch]).to(device)
                edge_feats = torch.stack([g['edge_features'] for _, g, _ in processed_batch]).to(device) if 'edge_features' in processed_batch[0][1] else None
            except Exception as e:
                logger.error(f"Tensor conversion failed: {e}")
                for smi, _, _ in processed_batch:
                    results.append({"smiles": smi, "latent_vector": None, "success": False, "error": f"Tensor conversion: {e}"})
                continue
            
            # 3. Inference
            try:
                if hasattr(model, 'encode'):
                    mu, _ = model.encode(node_feats, edge_idx, num_nodes, edge_features=edge_feats)
                else:
                    _, mu, _ = model(node_feats, edge_idx, num_nodes, edge_features=edge_feats)
                
                latent_list = mu.cpu().numpy().tolist()
                
                for idx, (smi, _, _) in enumerate(processed_batch):
                    results.append({
                        "smiles": smi,
                        "latent_vector": latent_list[idx],
                        "success": True,
                        "error": None
                    })
            except Exception as e:
                logger.error(f"Inference failed for batch: {e}")
                for smi, _, _ in processed_batch:
                    results.append({"smiles": smi, "latent_vector": None, "success": False, "error": str(e)})

    return results


def main():
    """
    Main entry point for the inference script.
    Usage: python code/inference.py --checkpoint path/to/checkpoint.pt --input path/to/smiles.txt --output path/to/latent_vectors.json
    """
    parser = argparse.ArgumentParser(description="Encode held-out SMILES using trained VAE")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to trained VAE checkpoint (.pt)")
    parser.add_argument("--input", type=str, required=True, help="Path to input file containing SMILES (one per line)")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON file for latent vectors")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for inference")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    # Setup
    reset_config()
    config = get_config()
    set_global_seed(args.seed)
    
    logger = get_project_logger("inference")
    logger.info("Starting inference pipeline")
    
    # Determine device
    device = torch.device("cpu") # Task constraints: CPU-only
    logger.info(f"Using device: {device}")
    
    # Load model
    try:
        hp = get_hyperparams()
        latent_dim = hp.get("latent_dim", 64)
        model = create_vae_model(latent_dim=latent_dim)
        checkpoint = load_checkpoint(args.checkpoint, device)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(device)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise RuntimeError(f"Model loading failed: {e}")
    
    # Load input data
    smiles_list = []
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {args.input}")
        raise FileNotFoundError(f"Input file not found: {args.input}")
    
    with open(input_path, 'r') as f:
        for line in f:
            smi = line.strip()
            if smi:
                smiles_list.append(smi)
    
    logger.info(f"Loaded {len(smiles_list)} SMILES from {args.input}")
    
    if len(smiles_list) == 0:
        logger.warning("No valid SMILES found in input file.")
        # Write empty result
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump([], f, indent=2)
        return
    
    # Run inference
    results = encode_smiles_batch(model, smiles_list, device, args.batch_size)
    
    success_count = sum(1 for r in results if r['success'])
    logger.info(f"Inference complete. Success: {success_count}/{len(results)}")
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {args.output}")
    
    # Log event
    log_event("inference_completed", {
        "input_file": str(args.input),
        "output_file": str(args.output),
        "checkpoint": args.checkpoint,
        "total_smiles": len(smiles_list),
        "successful_encodings": success_count,
        "failed_encodings": len(results) - success_count
    })


if __name__ == "__main__":
    main()
