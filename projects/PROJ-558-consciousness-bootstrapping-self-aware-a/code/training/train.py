"""
Training script for Consciousness Bootstrapping project.
Implements training of recursive and baseline models with validation for recursion depth.
"""

import os
import sys
import json
import hashlib
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import LlamaConfig, LlamaForCausalLM

# Project imports
from config import get_config, validate_config
from utils.logging import get_logger, log_training_start, log_training_end, log_exception, RecursionDepthError
from models.recursive_llama import create_recursive_model, RecursiveLlamaWrapper
from models.base_llama import BaseLlamaWrapper
from models.checkpoint import ModelCheckpoint
from evaluation.loss_functions import compute_joint_loss

logger = get_logger(__name__)

class PileDataset(Dataset):
    """Dataset wrapper for the truncated Pile dataset."""
    
    def __init__(self, data_path: str, max_length: int = 100000):
        super().__init__()
        self.data_path = data_path
        self.max_length = max_length
        self.data = []
        
        logger.info(f"Loading dataset from {data_path}")
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Dataset file not found: {data_path}")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                self.data.append(json.loads(line))
        
        logger.info(f"Loaded {len(self.data)} samples")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        # Assume 'text' or 'content' field exists
        text = item.get('text', item.get('content', ''))
        # Tokenization would happen here in a real implementation
        # For now, we return the raw text and let the model handle it
        return text

def validate_recursion_depth(model: nn.Module, max_depth: int = 2) -> bool:
    """
    Validate that the model's recursion depth does not exceed the specified limit.
    
    Args:
        model: The model to validate
        max_depth: Maximum allowed recursion depth (default: 2)
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        RecursionDepthError: If recursion depth exceeds limit or OOM is detected
    """
    try:
        # Check if model has recursion depth attribute
        if hasattr(model, 'recursion_depth'):
            current_depth = model.recursion_depth
            if current_depth > max_depth:
                error_msg = f"Recursion depth {current_depth} exceeds maximum allowed {max_depth}"
                logger.error(error_msg)
                raise RecursionDepthError(error_msg)
            logger.info(f"Recursion depth validated: {current_depth} <= {max_depth}")
            return True
        
        # Check for recursive attention modules
        if hasattr(model, 'recursive_attention'):
            if hasattr(model.recursive_attention, 'max_depth'):
                if model.recursive_attention.max_depth > max_depth:
                    error_msg = f"Recursive attention max_depth {model.recursive_attention.max_depth} exceeds limit {max_depth}"
                    logger.error(error_msg)
                    raise RecursionDepthError(error_msg)
        
        logger.info("Recursion depth validation passed")
        return True
        
    except RecursionDepthError:
        raise
    except Exception as e:
        logger.error(f"Error during recursion depth validation: {str(e)}")
        raise

def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: str,
    epoch: int,
    config: Dict[str, Any]
) -> float:
    """
    Train the model for one epoch.
    
    Args:
        model: The model to train
        dataloader: Data loader for training data
        optimizer: Optimizer for model parameters
        device: Device to train on ('cpu' or 'cuda')
        epoch: Current epoch number
        config: Configuration dictionary
        
    Returns:
        Average loss for the epoch
    """
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for batch_idx, batch in enumerate(dataloader):
        try:
            # Validate recursion depth before each batch
            validate_recursion_depth(model, max_depth=config.get('recursion_depth', 2))
            
            # Forward pass
            if isinstance(batch, dict):
                inputs = batch
            else:
                # Simple text handling
                inputs = {'input_ids': batch}
                
            outputs = model(**inputs)
            loss = outputs.loss
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
            
            if batch_idx % 10 == 0:
                logger.info(f"Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}")
                
        except RecursionDepthError:
            logger.error(f"Recursion depth violation at batch {batch_idx}")
            raise
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.error(f"OOM detected at batch {batch_idx}: {str(e)}")
                # Hard fail - do not attempt to recover
                raise RecursionDepthError(f"OOM detected during training: {str(e)}")
            raise
        
    return total_loss / num_batches if num_batches > 0 else 0.0

def save_checkpoint(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    loss: float,
    config: Dict[str, Any],
    checkpoint_path: str
) -> ModelCheckpoint:
    """
    Save a model checkpoint.
    
    Args:
        model: The model to save
        optimizer: The optimizer state
        epoch: Current epoch
        loss: Current loss
        config: Configuration dictionary
        checkpoint_path: Path to save checkpoint
        
    Returns:
        ModelCheckpoint object
    """
    checkpoint = ModelCheckpoint(
        model_state=model.state_dict(),
        optimizer_state=optimizer.state_dict(),
        epoch=epoch,
        loss=loss,
        config=config,
        created_at=datetime.now().isoformat(),
        path=checkpoint_path
    )
    
    # Save the checkpoint
    torch.save({
        'model_state_dict': checkpoint.model_state,
        'optimizer_state_dict': checkpoint.optimizer_state,
        'epoch': checkpoint.epoch,
        'loss': checkpoint.loss,
        'config': checkpoint.config,
        'created_at': checkpoint.created_at
    }, checkpoint_path)
    
    logger.info(f"Checkpoint saved to {checkpoint_path}")
    return checkpoint

def run_training(
    config: Optional[Dict[str, Any]] = None,
    data_path: Optional[str] = None,
    output_dir: Optional[str] = None
) -> Tuple[ModelCheckpoint, ModelCheckpoint]:
    """
    Run the full training pipeline for both recursive and baseline models.
    
    Args:
        config: Configuration dictionary (optional, will use defaults if None)
        data_path: Path to training data (optional)
        output_dir: Directory to save checkpoints (optional)
        
    Returns:
        Tuple of (recursive_checkpoint, baseline_checkpoint)
        
    Raises:
        RecursionDepthError: If recursion depth validation fails
        RuntimeError: If OOM occurs
    """
    # Load or create config
    if config is None:
        config = get_config()
    else:
        config = validate_config(config)
    
    # Set up paths
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'artifacts', 'checkpoints')
    os.makedirs(output_dir, exist_ok=True)
    
    if data_path is None:
        data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw', 'pile_arxiv_truncated.json')
    
    # Log training start
    log_training_start(config)
    
    try:
        # Initialize devices
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Using device: {device}")
        
        # Load dataset
        dataset = PileDataset(data_path, max_length=config.get('token_limit', 100000))
        dataloader = DataLoader(
            dataset, 
            batch_size=config.get('batch_size', 4),
            shuffle=True,
            num_workers=0  # CPU-only constraint
        )
        
        # Create recursive model
        logger.info("Creating recursive model...")
        recursive_model = create_recursive_model(config)
        recursive_model = recursive_model.to(device)
        
        # Validate recursion depth for recursive model
        validate_recursion_depth(recursive_model, max_depth=config.get('recursion_depth', 2))
        
        # Create baseline model
        logger.info("Creating baseline model...")
        baseline_model = BaseLlamaWrapper(config)
        baseline_model = baseline_model.to(device)
        
        # Setup optimizers
        recursive_optimizer = torch.optim.AdamW(
            recursive_model.parameters(),
            lr=config.get('learning_rate', 1e-4)
        )
        
        baseline_optimizer = torch.optim.AdamW(
            baseline_model.parameters(),
            lr=config.get('learning_rate', 1e-4)
        )
        
        # Training loop
        num_epochs = config.get('num_epochs', 1)
        recursive_checkpoint = None
        baseline_checkpoint = None
        
        for epoch in range(num_epochs):
            logger.info(f"Starting epoch {epoch + 1}/{num_epochs}")
            
            # Train recursive model
            try:
                recursive_loss = train_epoch(
                    recursive_model,
                    dataloader,
                    recursive_optimizer,
                    device,
                    epoch + 1,
                    config
                )
                logger.info(f"Recursive model epoch {epoch + 1} loss: {recursive_loss:.4f}")
                
                # Save checkpoint
                recursive_path = os.path.join(output_dir, f"recursive_epoch{epoch+1}.pt")
                recursive_checkpoint = save_checkpoint(
                    recursive_model,
                    recursive_optimizer,
                    epoch + 1,
                    recursive_loss,
                    config,
                    recursive_path
                )
                
            except RecursionDepthError as e:
                logger.error(f"Recursion depth error in recursive model training: {str(e)}")
                raise
            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    logger.error(f"OOM in recursive model training: {str(e)}")
                    raise RecursionDepthError(f"OOM during recursive model training: {str(e)}")
                raise
            
            # Train baseline model
            try:
                baseline_loss = train_epoch(
                    baseline_model,
                    dataloader,
                    baseline_optimizer,
                    device,
                    epoch + 1,
                    config
                )
                logger.info(f"Baseline model epoch {epoch + 1} loss: {baseline_loss:.4f}")
                
                # Save checkpoint
                baseline_path = os.path.join(output_dir, f"baseline_epoch{epoch+1}.pt")
                baseline_checkpoint = save_checkpoint(
                    baseline_model,
                    baseline_optimizer,
                    epoch + 1,
                    baseline_loss,
                    config,
                    baseline_path
                )
                
            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    logger.error(f"OOM in baseline model training: {str(e)}")
                    raise
                raise
        
        logger.info("Training completed successfully")
        return recursive_checkpoint, baseline_checkpoint
        
    except RecursionDepthError:
        logger.error("Training failed due to recursion depth violation")
        raise
    except Exception as e:
        logger.error(f"Training failed with error: {str(e)}")
        log_exception(e)
        raise
    finally:
        log_training_end()

def main():
    """Main entry point for training script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train recursive and baseline models')
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--data', type=str, help='Path to training data')
    parser.add_argument('--output', type=str, help='Output directory for checkpoints')
    parser.add_argument('--validate-depth', action='store_true', help='Validate recursion depth')
    
    args = parser.parse_args()
    
    try:
        # Load config
        config = get_config()
        if args.config and os.path.exists(args.config):
            with open(args.config, 'r') as f:
                custom_config = json.load(f)
                config.update(custom_config)
        
        # Run training
        recursive_checkpoint, baseline_checkpoint = run_training(
            config=config,
            data_path=args.data,
            output_dir=args.output
        )
        
        logger.info(f"Training completed. Checkpoints saved:")
        logger.info(f"  Recursive: {recursive_checkpoint.path}")
        logger.info(f"  Baseline: {baseline_checkpoint.path}")
        
    except RecursionDepthError as e:
        logger.error(f"CRITICAL: Recursion depth violation detected: {str(e)}")
        sys.exit(1)
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            logger.error(f"CRITICAL: Out of memory error: {str(e)}")
            sys.exit(1)
        raise
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        log_exception(e)
        sys.exit(1)

if __name__ == '__main__':
    main()