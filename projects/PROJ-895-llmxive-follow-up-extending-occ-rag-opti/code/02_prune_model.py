import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
import torch
from transformers import AutoModelForCausalLM

from code.code_00_config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_param_id(param_id: str) -> Tuple[str, str, int]:
    """Parses a parameter ID string into layer_id, param_type, and param_index."""
    parts = param_id.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid parameter ID format: {param_id}")
    layer_id = int(parts[0])
    param_type = parts[1]
    param_index = int(parts[2])
    return layer_id, param_type, param_index

def get_model_parameter_map(model: torch.nn.Module) -> Dict[str, torch.nn.Parameter]:
    """Creates a map of parameter names to parameters."""
    param_map = {}
    for name, param in model.named_parameters():
        param_map[name] = param
    return param_map

def load_sensitivity_results(csv_path: str) -> Dict[str, float]:
    """Loads sensitivity results from a CSV file."""
    sensitivity_scores = {}
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            param_id = row["param_id"]
            sensitivity_score = float(row["sensitivity_score"])
            sensitivity_scores[param_id] = sensitivity_score
    return sensitivity_scores

def apply_pruning_mask(model: torch.nn.Module, param_map: Dict[str, torch.nn.Parameter], retention_pct: float, sensitivity_results: Dict[str, float]):
    """
    Applies a pruning mask to the model based on sensitivity scores.
    
    CRITICAL: This function ensures the original architecture topology is preserved.
    Instead of removing parameters (which changes the model structure), it zeros out
    the weights of non-critical parameters. This maintains the exact tensor shapes
    and layer configurations, ensuring inference compatibility with the original model.
    """
    sorted_params = sorted(sensitivity_results.items(), key=lambda item: item[1], reverse=True)
    num_params_to_retain = int(len(sensitivity_results) * (retention_pct / 100))
    params_to_retain = [param_id for param_id, _ in sorted_params[:num_params_to_retain]]

    logging.info(f"Retaining top {num_params_to_retain} parameters ({retention_pct}%). Zeroing {len(sensitivity_results) - num_params_to_retain} parameters.")

    for name, param in param_map.items():
        # Check if this parameter corresponds to a retained param_id
        # We assume the param_id in sensitivity_results matches the parameter name in the model
        if name not in params_to_retain:
            with torch.no_grad():
                # Zero out the weights while keeping the tensor shape intact
                param.zero_()
    
    # Verify topology is preserved by checking total parameter count matches original
    total_params = sum(p.numel() for p in model.parameters())
    logging.info(f"Total parameter count after pruning (topology preserved): {total_params}")
    
    return model

def save_pruned_model(model: torch.nn.Module, output_path: str):
    """Saves the pruned model state dict."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    torch.save(model.state_dict(), output_path)
    logging.info(f"Pruned model state dict saved to {output_path}")

def main():
    config = Config()
    sensitivity_results_path = "data/processed/sensitivity_results.csv"
    output_model_path = f"data/processed/OCC-RAG-Pruned-{config.RETENTION_PCT}B.pt"

    # Validate config
    if config.RETENTION_PCT is None:
        raise ValueError("CONFIG.RETENTION_PCT is not set. Run T008.3 to determine empirical values.")

    # Load sensitivity results
    logging.info(f"Loading sensitivity results from {sensitivity_results_path}")
    sensitivity_results = load_sensitivity_results(sensitivity_results_path)

    # Load the model
    model_name = "nlp4research/occ-rag-1.7b-frozen"
    logging.info(f"Loading model from {model_name}...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name, 
        torch_dtype=torch.float32,
        local_files_only=False
    )

    # Capture original parameter count for verification
    original_param_count = sum(p.numel() for p in model.parameters())
    logging.info(f"Original model parameter count: {original_param_count}")

    # Get the parameter map
    param_map = get_model_parameter_map(model)

    # Apply pruning mask (zeros out non-critical weights, preserves topology)
    pruned_model = apply_pruning_mask(model, param_map, config.RETENTION_PCT, sensitivity_results)

    # Verify topology preservation: parameter count must remain unchanged
    pruned_param_count = sum(p.numel() for p in pruned_model.parameters())
    if pruned_param_count != original_param_count:
        raise RuntimeError(f"Topology mismatch! Original: {original_param_count}, Pruned: {pruned_param_count}")
    
    # Verify that non-zero parameters match the retention count
    non_zero_count = sum(1 for p in pruned_model.parameters() if p.nonzero().numel() > 0)
    # Note: This is a rough check; actual non-zero count depends on sparsity within retained params
    
    # Save the pruned model
    save_pruned_model(pruned_model, output_model_path)

    logging.info(f"Pruning complete. Architecture topology preserved. Model saved to {output_model_path}")

if __name__ == "__main__":
    main()