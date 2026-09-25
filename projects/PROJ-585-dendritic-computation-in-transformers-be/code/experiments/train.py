"""
Training script for Dendritic Transformers on GLUE SST-2.
Implements SIGALRM-based hard timeout and gradient clipping.
"""
import signal
import sys
import os
import time
import logging
import argparse
import yaml
import torch
from torch.utils.data import DataLoader
from datasets import load_dataset
from transformers import get_linear_schedule_with_warmup

# Ensure code/ is in path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.transformer_base import TransformerBaseline
from models.transformer_dendritic import TransformerDendritic
from data.loaders import load_sst2 as load_sst2_data

# --- Timeout Mechanism ---

class TimeoutError(Exception):
    """Custom exception raised when the training timeout is exceeded."""
    pass

def signal_handler(signum, frame):
    """Signal handler for SIGALRM."""
    raise TimeoutError("Training timed out after configured duration.")

def setup_timeout_handler(seconds: int):
    """
    Sets up a SIGALRM handler that will raise TimeoutError after `seconds`.
    Only works on Unix-like systems.
    """
    if not hasattr(signal, 'SIGALRM'):
        logging.warning("SIGALRM not available on this platform. Timeout disabled.")
        return
    
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    logging.info(f"Timeout handler set to {seconds} seconds.")

def cancel_timeout_handler():
    """Cancels the active alarm."""
    if hasattr(signal, 'SIGALRM'):
        signal.alarm(0)

# --- Model & Data Helpers ---

def get_model(model_name: str, config: dict):
    """Instantiates the requested model."""
    if model_name == "baseline":
        return TransformerBaseline(config)
    elif model_name == "dendritic":
        return TransformerDendritic(config)
    else:
        raise ValueError(f"Unknown model type: {model_name}")

# --- Training Loop ---

def train_epoch(model, dataloader, optimizer, scheduler, device, clip_norm: float = 1.0):
    model.train()
    total_loss = 0.0
    steps = 0
    
    for batch in dataloader:
        # Extract inputs
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['label'].to(device)

        optimizer.zero_grad()

        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        loss = outputs.loss
        loss.backward()

        # Gradient Clipping (T019)
        torch.nn.utils.clip_grad_norm_(model.parameters(), clip_norm)

        optimizer.step()
        scheduler.step()

        total_loss += loss.item()
        steps += 1

        if steps % 10 == 0:
            logging.info(f"Step {steps}, Loss: {loss.item():.4f}")

    return total_loss / steps if steps > 0 else 0.0

def evaluate(model, dataloader, device):
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['label'].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            logits = outputs.logits

            total_loss += loss.item()
            predictions = torch.argmax(logits, dim=-1)
            
            correct += (predictions == labels).sum().item()
            total += labels.size(0)

    accuracy = correct / total if total > 0 else 0.0
    avg_loss = total_loss / len(dataloader) if len(dataloader) > 0 else 0.0
    return avg_loss, accuracy

def main():
    parser = argparse.ArgumentParser(description="Train Dendritic Transformer")
    parser.add_argument("--config", type=str, default="code/config/config.yaml", help="Path to config file")
    parser.add_argument("--model", type=str, choices=["baseline", "dendritic"], default="dendritic", help="Model type")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("artifacts/logs/train.log")
        ]
    )

    # Load Config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    # Setup Timeout (T018 Core Requirement)
    cpu_timeout = config.get('cpu_timeout', 21600)
    setup_timeout_handler(cpu_timeout)

    try:
        # Setup Device
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logging.info(f"Using device: {device}")

        # Set Seed
        torch.manual_seed(args.seed)
        if device.type == 'cuda':
            torch.cuda.manual_seed_all(args.seed)

        # Load Data (T006/T022: Real SST-2)
        logging.info("Loading SST-2 dataset...")
        train_dataset, eval_dataset = load_sst2_data(
            config['data']['dataset_name'],
            config['data']['dataset_config'],
            max_length=config['data']['max_length']
        )

        train_loader = DataLoader(train_dataset, batch_size=config['batch_size'], shuffle=True)
        eval_loader = DataLoader(eval_dataset, batch_size=config['batch_size'], shuffle=False)

        # Initialize Model
        model_cfg = config['model']
        model = get_model(args.model, model_cfg).to(device)
        logging.info(f"Initialized {args.model} model with {sum(p.numel() for p in model.parameters())} params")

        # Optimizer & Scheduler
        optimizer = torch.optim.AdamW(model.parameters(), lr=config['learning_rate'])
        num_training_steps = len(train_loader) * args.epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer, 
            num_warmup_steps=0, 
            num_training_steps=num_training_steps
        )

        # Training Loop
        logging.info(f"Starting training for {args.epochs} epochs with timeout {cpu_timeout}s")
        for epoch in range(args.epochs):
            start_time = time.time()
            train_loss = train_epoch(
                model, train_loader, optimizer, scheduler, device, 
                clip_norm=1.0 # T019: Gradient clipping threshold
            )
            eval_loss, eval_acc = evaluate(model, eval_loader, device)
            
            epoch_time = time.time() - start_time
            logging.info(f"Epoch {epoch+1}/{args.epochs} | Loss: {train_loss:.4f} | Acc: {eval_acc:.4f} | Time: {epoch_time:.2f}s")

            # Save Checkpoint (T021)
            checkpoint_path = os.path.join(config['paths']['checkpoint_dir'], f"{args.model}_epoch{epoch+1}.pt")
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': train_loss,
                'accuracy': eval_acc
            }, checkpoint_path)
            logging.info(f"Saved checkpoint to {checkpoint_path}")

        logging.info("Training completed successfully.")

    except TimeoutError as e:
        logging.error(f"TIMEOUT: {e}")
        # Save partial state if possible before exit
        try:
            checkpoint_path = os.path.join(config['paths']['checkpoint_dir'], f"{args.model}_timeout.pt")
            torch.save({
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict()
            }, checkpoint_path)
            logging.info(f"Saved partial checkpoint to {checkpoint_path}")
        except:
            pass
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise
    finally:
        cancel_timeout_handler()

if __name__ == "__main__":
    main()