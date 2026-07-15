"""
Training script for Dendritic vs Baseline Transformers on GLUE SST-2.
Implements SIGALRM timeout handler and real data loading.
"""
import signal
import sys
import os
import time
import logging
import argparse
import yaml
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from datasets import load_dataset
from transformers import AutoTokenizer
from pathlib import Path

# Ensure imports work relative to project root
# The execution environment runs from project root, so we add code/ to path if needed
# However, standard practice in this project is relative imports from code/
# We assume this script is run as: python code/experiments/train.py
# So we need to handle the import path carefully.
try:
    from models.transformer_base import TransformerBaseline
    from models.transformer_dendritic import TransformerDendritic
except ImportError:
    # Fallback for running from project root
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from models.transformer_base import TransformerBaseline
    from models.transformer_dendritic import TransformerDendritic

# --- Signal Handler for Timeout ---
class TimeoutError(Exception):
    pass

def signal_handler(signum, frame):
    raise TimeoutError("Training timed out!")

def setup_timeout_handler(seconds: int):
    """
    Sets up a SIGALRM handler to raise TimeoutError after `seconds`.
    Note: SIGALRM only works on Unix-like systems.
    """
    if os.name != 'posix':
        logging.warning("SIGALRM not supported on this OS. Timeout mechanism disabled.")
        return

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    logging.info(f"Training timeout set to {seconds} seconds (SIGALRM).")

# --- Data Loading ---
def load_sst2_data(config_path: str):
    """
    Loads SST-2 dataset from HuggingFace.
    Uses the canonical 'glue/sst2' dataset.
    """
    config = yaml.safe_load(open(config_path))
    dataset_name = config['data']['dataset_name']
    dataset_config = config['data']['dataset_config']
    max_length = config['data']['max_length']

    logging.info(f"Loading dataset: {dataset_name} ({dataset_config})")
    
    # Load dataset
    dataset = load_dataset(dataset_name, dataset_config, split=['train', 'validation'])
    train_data = dataset[0]
    val_data = dataset[1]

    # Tokenize
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    
    def preprocess_function(examples):
        return tokenizer(
            examples["sentence"],
            truncation=True,
            padding="max_length",
            max_length=max_length
        )

    train_encodings = preprocess_function(train_data)
    val_encodings = preprocess_function(val_data)

    class GLUEDataset(Dataset):
        def __init__(self, encodings, labels):
            self.encodings = encodings
            self.labels = labels

        def __getitem__(self, idx):
            item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
            item['labels'] = torch.tensor(self.labels[idx])
            return item

        def __len__(self):
            return len(self.labels)

    train_dataset = GLUEDataset(train_encodings, train_data['label'])
    val_dataset = GLUEDataset(val_encodings, val_data['label'])

    return train_dataset, val_dataset, tokenizer

# --- Model Selection ---
def get_model(model_type: str, config: dict):
    """Instantiates the model based on type and config."""
    model_cfg = config['model']
    hidden_dim = model_cfg['hidden_dim']
    num_layers = model_cfg['num_layers']
    num_heads = model_cfg['num_heads']
    dropout = model_cfg['dropout']

    if model_type == 'baseline':
        model = TransformerBaseline(
            hidden_dim=hidden_dim,
            num_layers=num_layers,
            num_heads=num_heads,
            dropout=dropout,
            num_classes=2
        )
    elif model_type == 'dendritic':
        model = TransformerDendritic(
            hidden_dim=hidden_dim,
            num_layers=num_layers,
            num_heads=num_heads,
            dropout=dropout,
            num_classes=2
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    return model

# --- Training Loop ---
def train_epoch(model, dataloader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for batch in dataloader:
        optimizer.zero_grad()
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)

        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        loss = criterion(outputs, labels)
        loss.backward()
        
        # Gradient clipping (T019 requirement)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()

        total_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

    return total_loss / len(dataloader), correct / total

def evaluate(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0
    correct = 0
    total = 0

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            loss = criterion(outputs, labels)

            total_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    return total_loss / len(dataloader), correct / total

def main():
    parser = argparse.ArgumentParser(description="Train Dendritic/Baseline Transformers")
    parser.add_argument("--config", type=str, required=True, help="Path to config.yaml")
    parser.add_argument("--model", type=str, default="baseline", choices=["baseline", "dendritic"])
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    # Setup logging
    log_dir = "artifacts/logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"train_{args.model}_{int(time.time())}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Load config
    config = yaml.safe_load(open(args.config))
    lr = config['learning_rate']
    batch_size = config['batch_size']
    cpu_timeout = config['cpu_timeout']
    model_cfg = config['model']
    paths = config['paths']

    # Setup directories
    os.makedirs(paths['checkpoint_dir'], exist_ok=True)
    os.makedirs(paths['results_dir'], exist_ok=True)

    # Setup Timeout
    setup_timeout_handler(cpu_timeout)

    try:
        logging.info(f"Starting training for model: {args.model}")
        logging.info(f"CPU Timeout: {cpu_timeout} seconds")

        # Load Data
        train_dataset, val_dataset, tokenizer = load_sst2_data(args.config)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)

        # Setup Model
        device = torch.device("cpu") # Enforce CPU as per constraints
        model = get_model(args.model, config).to(device)
        
        optimizer = optim.AdamW(model.parameters(), lr=lr)
        criterion = nn.CrossEntropyLoss()

        # Training Loop
        history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}

        for epoch in range(args.epochs):
            logging.info(f"Epoch {epoch+1}/{args.epochs}")
            
            train_loss, train_acc = train_epoch(model, train_loader, optimizer, criterion, device)
            val_loss, val_acc = evaluate(model, val_loader, criterion, device)

            history['train_loss'].append(train_loss)
            history['train_acc'].append(train_acc)
            history['val_loss'].append(val_loss)
            history['val_acc'].append(val_acc)

            logging.info(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}")
            logging.info(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")

            # Save checkpoint (T021)
            checkpoint_path = os.path.join(paths['checkpoint_dir'], f"{args.model}_epoch{epoch+1}.pt")
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'train_acc': train_acc,
                'val_acc': val_acc
            }, checkpoint_path)
            logging.info(f"Checkpoint saved to {checkpoint_path}")

        # Save final results
        results_path = os.path.join(paths['results_dir'], f"{args.model}_results.json")
        import json
        with open(results_path, 'w') as f:
            json.dump(history, f, indent=2)
        logging.info(f"Results saved to {results_path}")

        logging.info("Training completed successfully.")

    except TimeoutError as e:
        logging.error(f"Training interrupted: {e}")
        # Save partial results if possible
        if 'history' in locals():
            results_path = os.path.join(paths['results_dir'], f"{args.model}_timeout_results.json")
            import json
            with open(results_path, 'w') as f:
                json.dump(history, f, indent=2)
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise
    finally:
        if os.name == 'posix':
            signal.alarm(0) # Cancel the alarm

if __name__ == "__main__":
    main()