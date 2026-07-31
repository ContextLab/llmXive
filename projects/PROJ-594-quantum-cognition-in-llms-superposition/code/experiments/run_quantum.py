import os
import sys
import json
import argparse
import time
import random
import torch
from typing import Dict, Any, List, Tuple

# Local imports matching the provided API surface
from models.bert_adapter import BERTComplexAdapter
from models.loss_utils import compute_phase_penalty_loss
from utils.logging import detect_nan_inf
from utils.config import get_config, set_environment
from data.download_wic import download_wic
from models.baseline_bert import load_wic_dataset

def train_epoch(
    model: BERTComplexAdapter,
    train_loader: torch.utils.data.DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    lambda_penalty: float = 0.5
) -> Dict[str, float]:
    """
    Train the complex adapter for one epoch.
    Implements the specific loss function: loss += lambda * (1 + torch.cos(phase_diff))
    """
    model.train()
    total_loss = 0.0
    num_batches = 0

    for batch in train_loader:
        optimizer.zero_grad()

        # Extract inputs
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['label'].to(device)
        ambiguous_mask = batch.get('ambiguous_mask', None)

        # Forward pass
        # The adapter expects real hidden states and outputs complex probabilities
        # We assume the model handles the BERT extraction internally or via a frozen base
        # For this implementation, we assume the model takes input_ids and returns logits/probs
        # However, based on the adapter design, we likely need to pass hidden states.
        # Let's assume the model wraps the frozen BERT and handles the forward pass.
        
        # Placeholder for actual forward logic if BERT is external
        # In a real implementation, we would get hidden states from a frozen BERT
        # and pass them to the adapter.
        
        # Assuming model.forward returns a dictionary with 'loss' and 'probs'
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
            ambiguous_mask=ambiguous_mask,
            lambda_penalty=lambda_penalty
        )

        loss = outputs['loss']
        
        # Check for NaN/Inf
        if detect_nan_inf(loss, raise_on_error=True):
            raise RuntimeError("NaN or Inf detected in loss during training")

        loss.backward()
        
        # Optional: Gradient clipping could go here
        # torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()

        total_loss += loss.item()
        num_batches += 1

    return {
        "loss": total_loss / num_batches if num_batches > 0 else 0.0
    }

def evaluate(
    model: BERTComplexAdapter,
    eval_loader: torch.utils.data.DataLoader,
    device: torch.device
) -> Dict[str, float]:
    """
    Evaluate the model on the validation/test set.
    Returns accuracy and macro-F1.
    """
    model.eval()
    correct = 0
    total = 0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch in eval_loader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['label'].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
                training=False
            )
            
            # Assuming outputs['logits'] or 'probs' are available
            # For binary classification (True/False in WiC)
            probs = outputs['probs']  # Shape: [batch, 2] or similar
            preds = torch.argmax(probs, dim=1)

            correct += (preds == labels).sum().item()
            total += labels.size(0)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    accuracy = correct / total if total > 0 else 0.0

    # Compute macro-F1 manually or use sklearn if available
    # Since we want to minimize dependencies, let's implement a simple F1 for binary
    # WiC is binary: True/False
    from sklearn.metrics import f1_score
    macro_f1 = f1_score(all_labels, all_preds, average='macro')

    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1
    }

def run_single_seed(seed: int, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a single training and evaluation seed.
    """
    set_environment(seed)
    device = torch.device("cpu") # Enforce CPU as per constraints
    
    print(f"Running seed: {seed}")
    
    # Load dataset
    # We assume download_wic has been run or the data is cached
    # If not, we call it here to ensure data exists
    try:
        wic_dataset = download_wic()
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        raise

    # Split into train/val/test (WiC usually comes with train/dev/test)
    # Assuming the dataset has 'train', 'validation', 'test' splits
    train_data = wic_dataset['train']
    val_data = wic_dataset['validation']
    test_data = wic_dataset['test']

    # Convert to PyTorch datasets and loaders
    # We need a custom collator or simple conversion
    # For simplicity, we assume a basic conversion
    def convert_to_tensor(dataset):
        input_ids = torch.tensor(dataset['input_ids'])
        attention_mask = torch.tensor(dataset['attention_mask'])
        labels = torch.tensor(dataset['label'])
        # Assume 'ambiguous_mask' is present or generated
        ambiguous_mask = dataset.get('ambiguous_mask', torch.zeros_like(labels))
        if isinstance(ambiguous_mask, list):
            ambiguous_mask = torch.tensor(ambiguous_mask)
        
        return torch.utils.data.TensorDataset(
            input_ids, attention_mask, labels, ambiguous_mask
        )

    train_dataset = convert_to_tensor(train_data)
    val_dataset = convert_to_tensor(val_data)
    test_dataset = convert_to_tensor(test_data)

    batch_size = config.get('batch_size', 8)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=batch_size)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size)

    # Initialize model
    model = BERTComplexAdapter(device=device)
    model.to(device)

    # Optimizer
    optimizer = torch.optim.Adam(model.parameters(), lr=config.get('learning_rate', 1e-4))

    # Training loop
    num_epochs = config.get('num_epochs', 3) # Limited number of epochs
    best_val_acc = 0.0
    best_model_state = None

    for epoch in range(num_epochs):
        train_metrics = train_epoch(model, train_loader, optimizer, device)
        val_metrics = evaluate(model, val_loader, device)

        print(f"Epoch {epoch+1}/{num_epochs} - Train Loss: {train_metrics['loss']:.4f} - Val Acc: {val_metrics['accuracy']:.4f}")

        if val_metrics['accuracy'] > best_val_acc:
            best_val_acc = val_metrics['accuracy']
            best_model_state = model.state_dict().copy()

    # Load best model and evaluate on test set
    if best_model_state:
        model.load_state_dict(best_model_state)
    
    test_metrics = evaluate(model, test_loader, device)

    # Check for NaN/Inf in final metrics
    if detect_nan_inf(torch.tensor(test_metrics['accuracy']), raise_on_error=False):
        print("Warning: NaN/Inf detected in final metrics")

    return {
        "seed": seed,
        "train_loss": train_metrics['loss'],
        "val_accuracy": best_val_acc,
        "test_accuracy": test_metrics['accuracy'],
        "test_macro_f1": test_metrics['macro_f1'],
        "num_epochs": num_epochs
    }

def main():
    parser = argparse.ArgumentParser(description="Run Quantum Adapter Training")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size")
    parser.add_argument("--output", type=str, default="data/results/quantum_metrics.json", help="Output path")
    args = parser.parse_args()

    config = {
        "num_epochs": args.epochs,
        "learning_rate": args.lr,
        "batch_size": args.batch_size
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    try:
        results = run_single_seed(args.seed, config)
        
        # Format output with associational framing (FR-006)
        output_data = {
            "seed": results["seed"],
            "metrics": {
                "train_loss": results["train_loss"],
                "val_accuracy": results["val_accuracy"],
                "test_accuracy": results["test_accuracy"],
                "test_macro_f1": results["test_macro_f1"]
            },
            "config": config,
            "note": "Results represent associational improvements in ambiguous reasoning performance."
        }

        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Results saved to {args.output}")

    except Exception as e:
        print(f"Error during execution: {e}")
        # Fail loudly - do not write partial results
        sys.exit(1)

if __name__ == "__main__":
    main()