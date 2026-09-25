"""
Probe intermediate layer representations with linear classifiers.

This module implements Task T025: Train linear classifiers on intermediate
layer representations for multiple random seeds to enable statistical analysis.
"""
import os
import sys
import argparse
import logging
import json
import csv
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SEEDS = [42, 123, 456, 789, 1011]
DEFAULT_EPOCHS = 10
DEFAULT_LR = 0.01
DEFAULT_BATCH_SIZE = 32
DEFAULT_PROB_THRESHOLD = 0.5

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def load_checkpoint(checkpoint_path: str) -> Dict[str, Any]:
    """Load a model checkpoint."""
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    logger.info(f"Loading checkpoint from {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    return checkpoint

def extract_layer_features(
    model: torch.nn.Module,
    dataloader: DataLoader,
    layer_indices: List[int],
    device: torch.device
) -> Dict[int, List[Tuple[np.ndarray, np.ndarray]]]:
    """
    Extract features from specified layers for all samples in the dataset.

    Args:
        model: The trained transformer model.
        dataloader: DataLoader containing the dataset.
        layer_indices: List of layer indices to extract features from.
        device: Device to run inference on.

    Returns:
        Dictionary mapping layer index to list of (features, labels) tuples.
    """
    model.eval()
    layer_features: Dict[int, List[Tuple[np.ndarray, np.ndarray]]] = {
        idx: [] for idx in layer_indices
    }

    # Hook to capture layer outputs
    hooks = []
    captured_outputs: Dict[int, torch.Tensor] = {}

    def get_layer_hook(layer_idx):
        def hook_fn(module, input, output):
            captured_outputs[layer_idx] = output[0] if isinstance(output, tuple) else output
        return hook_fn

    try:
        # Register hooks
        for idx in layer_indices:
            # Assuming model has a 'layers' or 'encoder' attribute with indexed layers
            # Adjust based on actual model structure
            try:
                layer = model.model.layers[idx]
            except (AttributeError, IndexError):
                try:
                    layer = model.encoder.layer[idx]
                except (AttributeError, IndexError):
                    logger.warning(f"Could not access layer {idx}, skipping")
                    continue
            hooks.append(layer.register_forward_hook(get_layer_hook(idx)))

        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['label'].to(device)

                # Forward pass
                try:
                    outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                except TypeError:
                    # Fallback for models that don't accept attention_mask
                    outputs = model(input_ids=input_ids)

                # Extract features for each layer
                for idx in layer_indices:
                    if idx in captured_outputs:
                        features = captured_outputs[idx].cpu().numpy()
                        # Mean pool over sequence dimension if necessary
                        if len(features.shape) > 2:
                            features = features.mean(axis=1)
                        layer_features[idx].append((features, labels.cpu().numpy()))
    finally:
        # Remove hooks
        for hook in hooks:
            hook.remove()

    # Flatten lists
    for idx in layer_indices:
        if layer_features[idx]:
            all_features, all_labels = zip(*layer_features[idx])
            layer_features[idx] = (
                np.vstack(all_features),
                np.concatenate(all_labels)
            )

    return layer_features

def train_linear_probe(
    features: np.ndarray,
    labels: np.ndarray,
    num_classes: int = 2,
    epochs: int = DEFAULT_EPOCHS,
    lr: float = DEFAULT_LR,
    batch_size: int = DEFAULT_BATCH_SIZE,
    seed: int = 42
) -> Tuple[float, float]:
    """
    Train a linear probe on the given features.

    Args:
        features: Feature matrix (N, D).
        labels: Labels (N,).
        num_classes: Number of output classes.
        epochs: Number of training epochs.
        lr: Learning rate.
        batch_size: Batch size.
        seed: Random seed.

    Returns:
        Tuple of (train_accuracy, val_accuracy).
    """
    set_seed(seed)
    device = torch.device('cpu')

    # Split data: 80% train, 20% val
    n_samples = len(features)
    indices = np.random.permutation(n_samples)
    split_idx = int(0.8 * n_samples)

    train_idx = indices[:split_idx]
    val_idx = indices[split_idx:]

    X_train, y_train = features[train_idx], labels[train_idx]
    X_val, y_val = features[val_idx], labels[val_idx]

    # Convert to tensors
    X_train_tensor = torch.FloatTensor(X_train).to(device)
    y_train_tensor = torch.LongTensor(y_train).to(device)
    X_val_tensor = torch.FloatTensor(X_val).to(device)
    y_val_tensor = torch.LongTensor(y_val).to(device)

    # Create data loaders
    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    val_dataset = TensorDataset(X_val_tensor, y_val_tensor)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    # Define linear probe
    input_dim = X_train.shape[1]
    probe = nn.Linear(input_dim, num_classes).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(probe.parameters(), lr=lr)

    # Training loop
    probe.train()
    for epoch in range(epochs):
        total_loss = 0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = probe(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

    # Evaluation
    probe.eval()
    correct_train = 0
    total_train = 0
    correct_val = 0
    total_val = 0

    with torch.no_grad():
        for batch_X, batch_y in train_loader:
            outputs = probe(batch_X)
            _, predicted = torch.max(outputs, 1)
            total_train += batch_y.size(0)
            correct_train += (predicted == batch_y).sum().item()

        for batch_X, batch_y in val_loader:
            outputs = probe(batch_y)
            _, predicted = torch.max(outputs, 1)
            total_val += batch_y.size(0)
            correct_val += (predicted == batch_y).sum().item()

    train_acc = correct_train / total_train
    val_acc = correct_val / total_val

    logger.info(f"Probe trained: Train Acc={train_acc:.4f}, Val Acc={val_acc:.4f}")
    return train_acc, val_acc

def load_sst2_data() -> Tuple[DataLoader, DataLoader, int]:
    """
    Load SST-2 dataset using the verified source from T006.
    Returns train and val dataloaders, and number of classes.
    """
    logger.info("Loading SST-2 dataset...")
    try:
        # Use the exact loading method from T006
        dataset = load_dataset('glue', 'sst2', trust_remote_code=True)
    except Exception as e:
        logger.error(f"Failed to load SST-2: {e}")
        raise

    # Preprocess
    def preprocess(examples):
        tokenizer = None
        try:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
        except ImportError:
            logger.warning("Transformers not installed, using simple tokenization")
            # Fallback: simple tokenization
            def simple_tokenize(text):
                return [ord(c) % 32 for c in text[:512]]
            return {
                'input_ids': [simple_tokenize(t) for t in examples['sentence']],
                'attention_mask': [[1]*len(t) for t in examples['sentence']],
                'label': examples['label']
            }

        encoded = tokenizer(
            examples['sentence'],
            truncation=True,
            padding='max_length',
            max_length=128
        )
        encoded['label'] = examples['label']
        return encoded

    # Apply preprocessing
    tokenized_datasets = dataset.map(
        preprocess,
        batched=True,
        remove_columns=['sentence', 'label'] if 'sentence' in dataset['train'].column_names else ['label']
    )

    # Create dataloaders
    train_dataset = tokenized_datasets['train']
    val_dataset = tokenized_datasets['validation']

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)

    return train_loader, val_loader, 2

def main():
    """Main entry point for probing experiments."""
    parser = argparse.ArgumentParser(description='Probe intermediate layer representations')
    parser.add_argument('--input-dir', type=str, default='data/experiments/',
                        help='Directory containing model checkpoints')
    parser.add_argument('--output-dir', type=str, default='artifacts/results/',
                        help='Directory to save probing results')
    parser.add_argument('--seeds', type=str, default=','.join(map(str, DEFAULT_SEEDS)),
                        help='Comma-separated list of random seeds')
    parser.add_argument('--layers', type=str, default='0,6,12',
                        help='Comma-separated list of layer indices to probe')
    parser.add_argument('--epochs', type=int, default=DEFAULT_EPOCHS,
                        help='Number of training epochs for probes')
    parser.add_argument('--lr', type=float, default=DEFAULT_LR,
                        help='Learning rate for probes')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE,
                        help='Batch size for probes')

    args = parser.parse_args()

    # Parse arguments
    seeds = [int(s) for s in args.seeds.split(',')]
    layers = [int(l) for l in args.layers.split(',')]

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Load SST-2 data
    train_loader, val_loader, num_classes = load_sst2_data()
    device = torch.device('cpu')

    # Find all checkpoints
    checkpoint_files = list(Path(args.input_dir).glob('*.pt')) + list(Path(args.input_dir).glob('*.pth'))
    if not checkpoint_files:
        logger.error(f"No checkpoints found in {args.input_dir}")
        sys.exit(1)

    logger.info(f"Found {len(checkpoint_files)} checkpoints")

    # Results storage
    all_results = []

    for checkpoint_path in checkpoint_files:
        checkpoint_name = checkpoint_path.stem
        logger.info(f"\nProcessing checkpoint: {checkpoint_name}")

        # Load checkpoint
        try:
            checkpoint = load_checkpoint(str(checkpoint_path))
            model = checkpoint.get('model')
            if model is None:
                logger.warning(f"No model found in {checkpoint_path}, skipping")
                continue
            model.eval()
            model.to(device)
        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_path}: {e}")
            continue

        # Extract features for each layer
        layer_features = extract_layer_features(model, val_loader, layers, device)

        # Train probes for each layer and each seed
        for layer_idx in layers:
            if layer_idx not in layer_features:
                logger.warning(f"Layer {layer_idx} not found in features, skipping")
                continue

            features, labels = layer_features[layer_idx]
            logger.info(f"  Layer {layer_idx}: {features.shape[0]} samples, {features.shape[1]} features")

            for seed in seeds:
                logger.info(f"    Training probe on layer {layer_idx} with seed {seed}")
                try:
                    train_acc, val_acc = train_linear_probe(
                        features, labels,
                        num_classes=num_classes,
                        epochs=args.epochs,
                        lr=args.lr,
                        batch_size=args.batch_size,
                        seed=seed
                    )

                    result = {
                        'checkpoint': checkpoint_name,
                        'layer': layer_idx,
                        'seed': seed,
                        'train_accuracy': train_acc,
                        'val_accuracy': val_acc
                    }
                    all_results.append(result)
                    logger.info(f"      Result: Train={train_acc:.4f}, Val={val_acc:.4f}")
                except Exception as e:
                    logger.error(f"    Failed to train probe on layer {layer_idx}, seed {seed}: {e}")
                    continue

    # Save results to CSV
    output_file = os.path.join(args.output_dir, 'probing_results.csv')
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=all_results[0].keys() if all_results else [])
        writer.writeheader()
        writer.writerows(all_results)

    logger.info(f"\nSaved results to {output_file}")
    logger.info(f"Total probes trained: {len(all_results)}")

    # Also save as JSON for easier parsing by analyze.py
    json_file = os.path.join(args.output_dir, 'probing_results.json')
    with open(json_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Saved JSON results to {json_file}")

if __name__ == '__main__':
    main()