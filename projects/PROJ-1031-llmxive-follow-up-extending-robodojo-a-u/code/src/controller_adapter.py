import os
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Optional, Dict, Any, Tuple, List, Union, Iterator
import logging
import numpy as np
from pathlib import Path
from config import BASE_DIR, SEED, REAL_WORLD_SPLIT

# Re-exporting types to match API surface expectations
class ValidationFailedError(Exception):
    """Raised when adapter validation fails against the hold-out set."""
    pass

class SymbolicActionSequence:
    """Placeholder for the sequence type expected by the executor."""
    def __init__(self, actions: List[str]):
        self.actions = actions

class LinearProbe(nn.Module):
    """
    A simple linear probe (MLP) that maps visual embeddings to discrete
    controller action logits.
    
    Architecture:
    Input: [embedding_dim]
    Layer 1: Linear -> ReLU -> Dropout
    Layer 2: Linear -> Output (logits for action space)
    """
    def __init__(self, embedding_dim: int = 512, action_dim: int = 6):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.action_dim = action_dim
        
        self.probe = nn.Sequential(
            nn.Linear(embedding_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 3:  # Batch, Seq, Dim -> Batch, Dim
            x = x.mean(dim=1)
        elif x.dim() == 2 and x.shape[1] != self.embedding_dim:
            # Handle potential shape mismatch if not batched correctly
            pass
        return self.probe(x)

def load_adapter_weights(path: str) -> LinearProbe:
    """Loads a LinearProbe instance from a checkpoint."""
    # Determine embedding_dim and action_dim from checkpoint if possible, 
    # otherwise default to standard values. 
    # For robustness, we assume standard architecture here.
    model = LinearProbe(embedding_dim=512, action_dim=6)
    checkpoint = torch.load(path, map_location='cpu')
    if 'state_dict' in checkpoint:
        model.load_state_dict(checkpoint['state_dict'])
    else:
        model.load_state_dict(checkpoint)
    return model

def adapt_policy_for_real_world(embeddings: torch.Tensor, probe: LinearProbe) -> torch.Tensor:
    """
    Uses the LinearProbe to adapt raw embeddings to real-world action logits.
    """
    return probe(embeddings)

def execute_symbolic_sequence(sequence: SymbolicActionSequence) -> bool:
    """
    Placeholder for execution logic.
    Returns True if sequence is valid, False otherwise.
    """
    return len(sequence.actions) > 0

def _get_real_world_data_stream():
    """
    Retrieves the real-world video subset from the RoboDojo dataset.
    Uses streaming to avoid RAM overflow.
    """
    from data_loader import stream_robodojo_tasks
    
    # Ensure we are streaming the specific split
    # The data_loader function signature is assumed to be:
    # stream_robodojo_tasks(split="real_world", seed=SEED)
    # based on task description and existing API surface.
    
    try:
        stream = stream_robodojo_tasks(split=REAL_WORLD_SPLIT, seed=SEED)
        return stream
    except Exception as e:
        logging.error(f"Failed to initialize real-world data stream: {e}")
        raise

def _collate_batch(batch):
    """
    Simple collation for the streaming batch.
    Expects a list of dicts with 'embedding' and 'action' keys.
    """
    embeddings = torch.stack([b['embedding'] for b in batch])
    actions = torch.stack([b['action'] for b in batch])
    return embeddings, actions

def _train_epoch(probe: LinearProbe, loader: Iterator, optimizer: optim.Optimizer, criterion: nn.Module, device: str):
    probe.train()
    total_loss = 0.0
    count = 0
    
    for batch in loader:
        # batch is expected to be a list of dicts if using custom streaming
        # We need to handle the streaming iterator directly if it yields dicts
        if isinstance(batch, dict):
            # If the stream yields single items, we need to batch them externally
            # For this implementation, we assume the stream yields dicts.
            # We will implement a simple batching logic here or assume the 
            # data_loader yields batches. 
            # Given the streaming nature, let's assume the stream yields single items
            # and we accumulate them into a list of size 32 for the epoch loop.
            pass 
        
        # Fallback: If the stream yields single dicts, we need to batch manually.
        # However, to keep this clean, let's assume the `stream_robodojo_tasks` 
        # can return an iterator of batches or we handle it here.
        # Let's implement a manual batcher for the streaming iterator.
        pass

def run_adapter_pipeline(
    interim_path: str = "data/processed/adapter_weights_interim.pt",
    final_path: str = "data/processed/adapter_weights.pt",
    validation_threshold: float = 0.75,
    batch_size: int = 32
) -> LinearProbe:
    """
    Executes the atomic flow for T010:
    1. Split real-world data (train/val).
    2. Train probe on training set.
    3. Save interim weights.
    4. Validate on hold-out set.
    5. If pass, retrain on full set and save final weights.
    6. If fail, raise ValidationFailedError.
    """
    logger = logging.getLogger(__name__)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")

    # 1. Get Data
    logger.info("Initializing real-world data stream...")
    stream = _get_real_world_data_stream()
    
    # Collect data into memory for splitting (since we need train/val split)
    # We assume the stream yields dicts with 'embedding' and 'action'.
    # We will limit to a reasonable size for this training step if the dataset is huge,
    # but the task implies processing the subset.
    # To prevent OOM, we stream into a list but stop if it gets too big.
    # For the purpose of this task, we assume the 'real_world' split is manageable 
    # or we sample it. However, the task says "full dataset" later, so we must be careful.
    
    data_list = []
    logger.info("Collecting real-world samples...")
    count = 0
    for item in stream:
        # Transform item to tensor
        emb = item.get('embedding')
        act = item.get('action')
        if emb is not None and act is not None:
            # Ensure tensors
            if not isinstance(emb, torch.Tensor):
                emb = torch.tensor(emb, dtype=torch.float32)
            if not isinstance(act, torch.Tensor):
                act = torch.tensor(act, dtype=torch.long)
            data_list.append({'embedding': emb, 'action': act})
        count += 1
        if count % 1000 == 0:
            logger.info(f"Collected {count} samples...")
    
    logger.info(f"Total samples collected: {len(data_list)}")
    if len(data_list) == 0:
        raise RuntimeError("No data collected from real-world stream.")

    # Split: 80% Train, 20% Val
    torch.manual_seed(SEED)
    indices = torch.randperm(len(data_list)).tolist()
    split_idx = int(0.8 * len(data_list))
    train_indices = indices[:split_idx]
    val_indices = indices[split_idx:]

    train_data = [data_list[i] for i in train_indices]
    val_data = [data_list[i] for i in val_indices]

    logger.info(f"Train size: {len(train_data)}, Val size: {len(val_data)}")

    # Create DataLoaders
    # Simple custom dataset wrapper
    class SimpleDataset(torch.utils.data.Dataset):
        def __init__(self, data):
            self.data = data
        def __len__(self):
            return len(self.data)
        def __getitem__(self, idx):
            return self.data[idx]['embedding'], self.data[idx]['action']

    train_ds = SimpleDataset(train_data)
    val_ds = SimpleDataset(val_data)
    
    train_loader = torch.utils.data.DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = torch.utils.data.DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    # 2. Initialize Model
    probe = LinearProbe(embedding_dim=512, action_dim=6).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(probe.parameters(), lr=1e-3)

    # Training Loop
    epochs = 5
    logger.info("Starting training on training set...")
    for epoch in range(epochs):
        probe.train()
        total_loss = 0
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            logits = probe(batch_x)
            loss = criterion(logits, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(train_loader):.4f}")

    # 3. Save Interim Weights
    os.makedirs(os.path.dirname(interim_path), exist_ok=True)
    save_path_interim = os.path.join(BASE_DIR, interim_path)
    torch.save({'state_dict': probe.state_dict(), 'epoch': epochs}, save_path_interim)
    logger.info(f"Interim weights saved to {save_path_interim}")

    # 4. Validate on Hold-out Set
    probe.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for batch_x, batch_y in val_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            logits = probe(batch_x)
            preds = torch.argmax(logits, dim=1)
            correct += (preds == batch_y).sum().item()
            total += batch_y.size(0)
    
    val_acc = correct / total if total > 0 else 0.0
    logger.info(f"Validation Accuracy: {val_acc:.4f} (Threshold: {validation_threshold})")

    if val_acc < validation_threshold:
        raise ValidationFailedError(f"Validation accuracy {val_acc:.4f} is below threshold {validation_threshold}. Aborting full retrain.")

    # 5. Retrain on Full Dataset
    logger.info("Validation passed. Retraining on full dataset (Train + Val)...")
    full_data = data_list  # Combine train and val
    full_ds = SimpleDataset(full_data)
    full_loader = torch.utils.data.DataLoader(full_ds, batch_size=batch_size, shuffle=True)
    
    # Reset model or continue? Task says "retrain", usually implies starting fresh or continuing.
    # We'll continue from the good weights found.
    probe.train()
    for epoch in range(epochs):
        total_loss = 0
        for batch_x, batch_y in full_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            logits = probe(batch_x)
            loss = criterion(logits, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        logger.info(f"Full Retraining Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(full_loader):.4f}")

    # Save Final Weights
    save_path_final = os.path.join(BASE_DIR, final_path)
    torch.save({'state_dict': probe.state_dict(), 'epoch': epochs * 2}, save_path_final)
    logger.info(f"Final weights saved to {save_path_final}")

    return probe

def run_full_pipeline():
    """
    Orchestrator for the full adapter pipeline.
    """
    run_adapter_pipeline()

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        run_adapter_pipeline()
        logging.info("T010 Adapter Pipeline completed successfully.")
    except ValidationFailedError as e:
        logging.error(f"Pipeline failed: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
