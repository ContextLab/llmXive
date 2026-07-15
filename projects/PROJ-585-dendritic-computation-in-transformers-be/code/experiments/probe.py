"""
Probe intermediate layer representations with linear classifiers.

This module trains linear classifiers on the hidden states of intermediate
transformer layers to probe the representational quality of the model at
different depths. It supports multiple random seeds for statistical power.
"""

import os
import sys
import argparse
import logging
import json
import csv
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler

# Add project root to path to resolve imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from experiments.train import load_sst2_data
from models.transformer_base import TransformerBaseline
from models.transformer_dendritic import TransformerDendritic
from config.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_checkpoint(checkpoint_path: str, model_type: str = "baseline") -> Tuple[Any, dict]:
    """
    Load a model checkpoint and return the model and its config.

    Args:
        checkpoint_path: Path to the checkpoint file (.pt)
        model_type: Either "baseline" or "dendritic"

    Returns:
        Tuple of (model, config_dict)
    """
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

    checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
    config = checkpoint.get('config', {})

    if model_type == "baseline":
        model = TransformerBaseline(config)
    elif model_type == "dendritic":
        model = TransformerDendritic(config)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    logger.info(f"Loaded checkpoint from {checkpoint_path} for {model_type} model")
    return model, config


def extract_layer_features(
    model: Any,
    dataloader: DataLoader,
    layer_indices: List[int],
    device: str = 'cpu'
) -> Dict[int, List[np.ndarray]]:
    """
    Extract hidden states from specified layers for all samples in the dataset.

    Args:
        model: The transformer model
        dataloader: DataLoader containing the input data
        layer_indices: List of layer indices to extract features from
        device: Device to run inference on

    Returns:
        Dict mapping layer index to list of feature arrays (one per sample)
    """
    model.to(device)
    model.eval()

    features_by_layer = {idx: [] for idx in layer_indices}

    with torch.no_grad():
        for batch in dataloader:
            # Handle different batch structures
            if isinstance(batch, dict):
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device) if 'labels' in batch else None
            else:
                # Assume tuple: (input_ids, attention_mask, labels)
                input_ids, attention_mask, labels = batch[0].to(device), batch[1].to(device), batch[2].to(device)

            # Forward pass with hook to capture intermediate features
            layer_outputs = {}

            def get_layer_output(layer_idx):
                def hook_fn(module, input, output):
                    # Output is typically (batch, seq_len, hidden_dim)
                    if isinstance(output, tuple):
                        output = output[0]
                    layer_outputs[layer_idx] = output.detach().cpu().numpy()
                return hook_fn

            hooks = []
            for idx in layer_indices:
                # Access the specific layer (assumes model has 'layers' or 'encoder.layer' attribute)
                try:
                    if hasattr(model, 'layers'):
                        layer = model.layers[idx]
                    elif hasattr(model, 'encoder') and hasattr(model.encoder, 'layer'):
                        layer = model.encoder.layer[idx]
                    else:
                        logger.warning(f"Could not access layer {idx} in model. Skipping.")
                        continue
                    hooks.append(layer.register_forward_hook(get_layer_output(idx)))
                except (IndexError, AttributeError) as e:
                    logger.warning(f"Could not register hook for layer {idx}: {e}")
                    continue

            try:
                _ = model(input_ids=input_ids, attention_mask=attention_mask)
            except Exception as e:
                logger.error(f"Forward pass failed: {e}")
                raise

            # Remove hooks
            for hook in hooks:
                hook.remove()

            # Process batch outputs
            batch_size = input_ids.size(0)
            for idx in layer_indices:
                if idx in layer_outputs:
                    out = layer_outputs[idx]
                    # out shape: (batch, seq_len, hidden) -> pool to (batch, hidden)
                    # Use mean pooling over sequence length
                    pooled = out.mean(axis=1)  # (batch, hidden)
                    for i in range(batch_size):
                        features_by_layer[idx].append(pooled[i])

    return features_by_layer


def train_linear_probe(
    train_features: np.ndarray,
    train_labels: np.ndarray,
    test_features: np.ndarray,
    test_labels: np.ndarray,
    seed: int = 42
) -> Tuple[float, LogisticRegression]:
    """
    Train a linear probe (Logistic Regression) on features.

    Args:
        train_features: Training features (n_samples, n_features)
        train_labels: Training labels
        test_features: Test features
        test_labels: Test labels
        seed: Random seed

    Returns:
        Tuple of (accuracy, trained_model)
    """
    set_seed(seed)

    # Standardize features
    scaler = StandardScaler()
    train_features_scaled = scaler.fit_transform(train_features)
    test_features_scaled = scaler.transform(test_features)

    # Train logistic regression
    clf = LogisticRegression(
        max_iter=1000,
        random_state=seed,
        solver='lbfgs',
        multi_class='auto'
    )
    clf.fit(train_features_scaled, train_labels)

    # Evaluate
    train_pred = clf.predict(train_features_scaled)
    test_pred = clf.predict(test_features_scaled)

    train_acc = accuracy_score(train_labels, train_pred)
    test_acc = accuracy_score(test_labels, test_pred)

    logger.info(f"Linear Probe - Train Acc: {train_acc:.4f}, Test Acc: {test_acc:.4f}")

    return test_acc, clf


def main():
    parser = argparse.ArgumentParser(description="Probe intermediate layer representations")
    parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="Directory containing model checkpoints"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="artifacts/results",
        help="Directory to save probe results"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config/config.yaml",
        help="Path to config file"
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs='+',
        default=[42, 123, 456],
        help="List of random seeds for probing"
    )
    parser.add_argument(
        "--layers",
        type=int,
        nargs='+',
        default=None,
        help="Specific layers to probe (default: all layers)"
    )
    parser.add_argument(
        "--model-type",
        type=str,
        choices=["baseline", "dendritic", "both"],
        default="both",
        help="Which model type to probe"
    )

    args = parser.parse_args()

    # Setup
    config = load_config(args.config)
    os.makedirs(args.output_dir, exist_ok=True)

    # Load SST-2 data (using the same loader as training)
    logger.info("Loading SST-2 data...")
    dataset = load_sst2_data()
    # Assume dataset is a dict with 'train', 'validation', 'test' keys
    # We'll use train for training probe, validation for testing
    if 'train' in dataset and 'validation' in dataset:
        train_data = dataset['train']
        test_data = dataset['validation']
    else:
        # Fallback if structure is different
        train_data = dataset['train']
        test_data = dataset['test'] if 'test' in dataset else dataset['validation']

    # Prepare dataloaders
    # We need to extract features, so we'll create a simple tensor dataset
    # Note: This assumes the data loader returns (input_ids, attention_mask, labels)
    # For probing, we need to run inference on the model to get features
    
    # Since we can't easily batch the feature extraction with the model in the loop,
    # we'll iterate through the dataset and collect features
    
    # For efficiency, we'll use a small subset for probing if the dataset is huge
    # But for SST-2, it's small enough to process all
    
    train_inputs = []
    train_labels = []
    test_inputs = []
    test_labels = []

    # Assuming dataset items are dicts with 'input_ids', 'attention_mask', 'label'
    for item in train_data:
        train_inputs.append({
            'input_ids': item['input_ids'],
            'attention_mask': item['attention_mask']
        })
        train_labels.append(item['label'])

    for item in test_data:
        test_inputs.append({
            'input_ids': item['input_ids'],
            'attention_mask': item['attention_mask']
        })
        test_labels.append(item['label'])

    train_labels = np.array(train_labels)
    test_labels = np.array(test_labels)

    # Create a simple loader for feature extraction
    # We'll process one by one to avoid memory issues
    
    # Determine layers to probe
    # Default: probe all layers (assuming 12 layers for BERT-base)
    if args.layers is None:
        # We'll try to infer from config or default to common values
        num_layers = config.get('num_layers', 12)
        layer_indices = list(range(num_layers))
    else:
        layer_indices = args.layers

    logger.info(f"Probing layers: {layer_indices}")

    # Find checkpoints
    checkpoint_files = []
    for pattern in ["*.pt", "*.pth"]:
        checkpoint_files.extend(Path(args.input_dir).glob(pattern))
    
    if not checkpoint_files:
        logger.error(f"No checkpoints found in {args.input_dir}")
        sys.exit(1)

    results = []

    for ckpt_path in checkpoint_files:
        model_name = ckpt_path.stem
        # Infer model type from filename or config
        if "dendritic" in model_name.lower():
            model_type = "dendritic"
        elif "baseline" in model_name.lower():
            model_type = "baseline"
        else:
            # Try to load config from checkpoint to determine
            checkpoint = torch.load(ckpt_path, map_location='cpu', weights_only=False)
            cfg = checkpoint.get('config', {})
            if cfg.get('model_type', '').lower() == 'dendritic':
                model_type = "dendritic"
            else:
                model_type = "baseline"

        if args.model_type != "both" and args.model_type != model_type:
            continue

        logger.info(f"Processing checkpoint: {ckpt_path} (type: {model_type})")

        try:
            model, _ = load_checkpoint(str(ckpt_path), model_type)
            device = 'cpu'
            model.to(device)

            # Extract features for train and test sets
            # We need to pass data through the model in a way that captures layer outputs
            # Since our extract_layer_features expects a DataLoader, we'll create one
            
            # Create a simple dataset wrapper
            class FeatureDataset(torch.utils.data.Dataset):
                def __init__(self, inputs, labels):
                    self.inputs = inputs
                    self.labels = labels

                def __len__(self):
                    return len(self.inputs)

                def __getitem__(self, idx):
                    item = self.inputs[idx]
                    return (
                        torch.tensor(item['input_ids'], dtype=torch.long),
                        torch.tensor(item['attention_mask'], dtype=torch.long),
                        torch.tensor(self.labels[idx], dtype=torch.long)
                    )

            train_dataset = FeatureDataset(train_inputs, train_labels)
            test_dataset = FeatureDataset(test_inputs, test_labels)

            train_loader = DataLoader(train_dataset, batch_size=16, shuffle=False)
            test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)

            # Extract features
            logger.info("Extracting features from model...")
            train_features_by_layer = extract_layer_features(model, train_loader, layer_indices, device)
            test_features_by_layer = extract_layer_features(model, test_loader, layer_indices, device)

            # Train probes for each layer and each seed
            for layer_idx in layer_indices:
                if layer_idx not in train_features_by_layer or layer_idx not in test_features_by_layer:
                    logger.warning(f"Features not extracted for layer {layer_idx}")
                    continue

                train_feats = np.array(train_features_by_layer[layer_idx])
                test_feats = np.array(test_features_by_layer[layer_idx])

                for seed in args.seeds:
                    acc, _ = train_linear_probe(
                        train_feats, train_labels,
                        test_feats, test_labels,
                        seed=seed
                    )

                    results.append({
                        'checkpoint': model_name,
                        'model_type': model_type,
                        'layer': layer_idx,
                        'seed': seed,
                        'accuracy': acc
                    })

        except Exception as e:
            logger.error(f"Failed to process checkpoint {ckpt_path}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Save results
    output_file = os.path.join(args.output_dir, "probe_results.csv")
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys() if results else [])
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Probe results saved to {output_file}")

    # Also save as JSON for easier parsing
    json_file = os.path.join(args.output_dir, "probe_results.json")
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Probe results saved to {json_file}")


if __name__ == "__main__":
    main()