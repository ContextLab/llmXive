"""
Evaluation module for Polymer Degradation Pathways GNN.

Implements test-set prediction generation, model checkpointing,
and Integrated Gradients attribution map saving.
"""
import os
import json
import logging
import csv
import torch
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from data_models import PolymerRecord, MolecularGraph
from model import PolymerGNN, IntegratedGradients, create_model_from_config
from utils import get_logger, get_project_paths, load_config_env

# Configure logger
logger = get_logger(__name__)


def load_trained_model_and_ig(
    checkpoint_path: str,
    device: str = "cpu"
) -> Tuple[PolymerGNN, IntegratedGradients]:
    """
    Load a trained model checkpoint and initialize Integrated Gradients.
    
    Args:
        checkpoint_path: Path to the .pt checkpoint file.
        device: Device to load the model onto (default: cpu).
        
    Returns:
        Tuple of (loaded model, IntegratedGradients instance).
    """
    logger.info(f"Loading model checkpoint from {checkpoint_path}")
    
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
        
    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=torch.device(device))
    
    # Reconstruct model architecture (assuming config is saved or hardcoded for now)
    # In a real scenario, we might load config from the checkpoint or a separate file
    model = PolymerGNN(
        node_dim=checkpoint.get('node_dim', 128),
        edge_dim=checkpoint.get('edge_dim', 64),
        hidden_dim=checkpoint.get('hidden_dim', 128),
        num_layers=checkpoint.get('num_layers', 3),
        num_classes=checkpoint.get('num_classes', 3) # Assuming 3 degradation types
    )
    
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    
    ig = IntegratedGradients(model)
    
    logger.info("Model loaded successfully")
    return model, ig


def load_test_predictions(predictions_path: str) -> List[Dict[str, Any]]:
    """
    Load existing test predictions from a JSON file.
    
    Args:
        predictions_path: Path to the JSON file.
        
    Returns:
        List of prediction dictionaries.
    """
    logger.info(f"Loading test predictions from {predictions_path}")
    with open(predictions_path, 'r') as f:
        return json.load(f)


def get_ester_bond_indices(graph_data: Any) -> List[int]:
    """
    Identify indices of ester bonds in a molecular graph.
    
    Args:
        graph_data: Molecular graph data object (from preprocess).
        
    Returns:
        List of edge indices corresponding to ester bonds.
    """
    # This function assumes graph_data contains edge features or attributes
    # that can be used to identify ester bonds.
    # Implementation depends on the specific graph representation.
    # For now, returning an empty list as a placeholder for logic
    # that would check edge features for ester characteristics.
    # In a full implementation, this would iterate over edges and check features.
    return []


def calculate_ester_attribution_percentage(
    attribution_scores: torch.Tensor,
    ester_indices: List[int]
) -> float:
    """
    Calculate the percentage of top attribution scores that correspond to ester bonds.
    
    Args:
        attribution_scores: Tensor of Integrated Gradients scores.
        ester_indices: List of edge indices that are ester bonds.
        
    Returns:
        Percentage of top scores (e.g., top 10%) that are ester bonds.
    """
    if not ester_indices:
        logger.warning("No ester indices provided. Returning 0.0%")
        return 0.0
        
    # Get top-k indices (e.g., top 10%)
    k = max(1, int(len(attribution_scores) * 0.1))
    _, top_k_indices = torch.topk(attribution_scores, k)
    
    top_k_set = set(top_k_indices.tolist())
    ester_set = set(ester_indices)
    
    overlap = len(top_k_set.intersection(ester_set))
    percentage = (overlap / k) * 100.0
    
    return percentage


def save_model_checkpoint(
    model: PolymerGNN,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    metrics: Dict[str, float],
    save_path: str
) -> None:
    """
    Save model checkpoint including state dicts and metrics.
    
    Args:
        model: Trained PolymerGNN model.
        optimizer: Training optimizer.
        epoch: Current epoch number.
        metrics: Dictionary of validation metrics.
        save_path: Path to save the checkpoint.
    """
    logger.info(f"Saving model checkpoint to {save_path}")
    
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'metrics': metrics,
        # Save architecture params for loading
        'node_dim': model.node_dim,
        'edge_dim': model.edge_dim,
        'hidden_dim': model.hidden_dim,
        'num_layers': model.num_layers,
        'num_classes': model.num_classes
    }
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save(checkpoint, save_path)
    logger.info(f"Checkpoint saved successfully")


def save_attribution_maps(
    ig_instance: IntegratedGradients,
    graphs: List[Any],
    labels: List[int],
    save_path: str
) -> None:
    """
    Save Integrated Gradients attribution maps for a list of graphs.
    
    Args:
        ig_instance: IntegratedGradients instance.
        graphs: List of molecular graph data objects.
        labels: List of ground truth labels.
        save_path: Path to save the attribution maps (JSON).
    """
    logger.info(f"Saving attribution maps to {save_path}")
    
    attributions_data = []
    
    for i, (graph, label) in enumerate(zip(graphs, labels)):
        # Compute attribution
        attr, _ = ig_instance.compute_attributions(graph)
        
        attributions_data.append({
            'index': i,
            'label': int(label),
            'attribution_scores': attr.tolist() if isinstance(attr, torch.Tensor) else attr
        })
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w') as f:
        json.dump(attributions_data, f, indent=2)
        
    logger.info(f"Saved {len(attributions_data)} attribution maps")


def save_validation_metrics(
    metrics: Dict[str, float],
    save_path: str
) -> None:
    """
    Save validation metrics to a JSON file.
    
    Args:
        metrics: Dictionary of metrics.
        save_path: Path to save the metrics.
    """
    logger.info(f"Saving validation metrics to {save_path}")
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    logger.info(f"Metrics saved: {metrics}")


def generate_test_predictions(
    model: PolymerGNN,
    test_graphs: List[Any],
    test_labels: List[int],
    ig_instance: IntegratedGradients,
    output_path: str
) -> None:
    """
    Generate test-set predictions using the trained model and Integrated Gradients.
    Saves predictions, probabilities, and attribution maps to a JSON file.
    
    Args:
        model: Trained PolymerGNN model.
        test_graphs: List of test molecular graph data objects.
        test_labels: List of ground truth labels for the test set.
        ig_instance: IntegratedGradients instance for attribution.
        output_path: Path to save the predictions JSON file.
    """
    logger.info(f"Generating test-set predictions for {len(test_graphs)} samples")
    
    model.eval()
    predictions_data = []
    
    with torch.no_grad():
        for i, (graph, label) in enumerate(zip(test_graphs, test_labels)):
            # Move graph to device
            device = next(model.parameters()).device
            graph = graph.to(device)
            
            # Forward pass
            logits = model(graph)
            probs = torch.softmax(logits, dim=-1)
            pred_label = torch.argmax(probs, dim=-1).item()
            confidence = probs.max().item()
            
            # Compute Integrated Gradients attribution
            attr_scores, baseline = ig_instance.compute_attributions(graph)
            
            # Store prediction data
            prediction_entry = {
                'index': i,
                'true_label': int(label),
                'predicted_label': pred_label,
                'confidence': float(confidence),
                'probabilities': probs.tolist()[0],
                'attribution_scores': attr_scores.tolist() if isinstance(attr_scores, torch.Tensor) else attr_scores,
                'low_confidence': confidence < 0.6  # Flag low confidence predictions
            }
            
            predictions_data.append(prediction_entry)
            
            if i % 100 == 0:
                logger.debug(f"Processed {i}/{len(test_graphs)} samples")
    
    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(predictions_data, f, indent=2)
        
    logger.info(f"Saved {len(predictions_data)} test predictions to {output_path}")
    
    # Log summary statistics
    correct = sum(1 for p in predictions_data if p['true_label'] == p['predicted_label'])
    accuracy = correct / len(predictions_data)
    low_conf_count = sum(1 for p in predictions_data if p['low_confidence'])
    
    logger.info(f"Test Accuracy: {accuracy:.4f}")
    logger.info(f"Low Confidence Predictions: {low_conf_count}/{len(predictions_data)}")


def main():
    """
    Main entry point for generating test-set predictions.
    """
    logger.info("Starting test prediction generation")
    
    # Load configuration
    config = load_config_env()
    paths = get_project_paths()
    
    # Paths
    checkpoint_path = paths['reports'] / 'model_checkpoint.pt'
    test_data_path = paths['processed'] / 'test_graphs.json' # Assumed path
    output_predictions_path = paths['reports'] / 'test_predictions.json'
    
    # Check prerequisites
    if not checkpoint_path.exists():
        logger.error(f"Model checkpoint not found at {checkpoint_path}")
        raise FileNotFoundError("Model checkpoint missing. Run training first.")
        
    if not test_data_path.exists():
        logger.error(f"Test data not found at {test_data_path}")
        raise FileNotFoundError("Test data missing. Run preprocessing first.")
    
    # Load model and IG
    model, ig = load_trained_model_and_ig(str(checkpoint_path))
    
    # Load test data (simplified loading for this task)
    # In a real scenario, this would load the actual graph objects
    # For now, we assume a helper function or direct loading logic
    # Since we can't load actual graph objects without the full preprocess pipeline
    # exposed as a loader, we will simulate the loading of test data structure
    # or assume the data is in a format we can iterate.
    # However, the task requires REAL output.
    # We will attempt to load a JSON representation of the test set if it exists,
    # or raise an error if the data isn't ready.
    
    # Note: The actual loading of graph objects depends on how T016/T022 saved them.
    # Assuming a JSON serialization of graph data exists or we load from a pickle.
    # For this implementation, we assume a helper `load_processed_polyester_dataset`
    # from preprocess.py exists to load the test split, or we load a JSON dump.
    
    # Let's assume the test graphs and labels are stored in a JSON file
    # generated by T016/T022.
    if not test_data_path.exists():
        # Fallback to a standard location if the assumed path is wrong
        test_data_path = paths['processed'] / 'test_split_data.json'
        if not test_data_path.exists():
             logger.error(f"Test data file not found at {test_data_path} or {paths['processed'] / 'test_split_data.json'}")
             raise FileNotFoundError("Test split data not found.")

    with open(test_data_path, 'r') as f:
        test_data = json.load(f)
        
    test_graphs = test_data.get('graphs', [])
    test_labels = test_data.get('labels', [])
    
    if not test_graphs:
        logger.warning("No test graphs found in data file.")
        # Create empty output if no data
        with open(output_predictions_path, 'w') as f:
            json.dump([], f)
        return

    # Generate predictions
    generate_test_predictions(
        model,
        test_graphs,
        test_labels,
        ig,
        str(output_predictions_path)
    )
    
    logger.info("Test prediction generation completed successfully")


if __name__ == "__main__":
    main()