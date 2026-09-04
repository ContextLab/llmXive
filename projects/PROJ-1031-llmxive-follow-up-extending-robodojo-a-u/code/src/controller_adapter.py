"""
Controller Adapter Module for RoboDojo Symbolic Abstractions.

Implements the Linear Probe architecture for sim-to-real adaptation.
Handles training, validation, weight discarding, and final retraining on all tasks.
"""
import os
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Optional, Dict, Any, Tuple, List, Union, Iterator
import logging
import numpy as np
from dataclasses import dataclass
import time

from .data_loader import stream_robodojo_tasks, load_task_by_id, get_dataset_info
from .config import DATA_PROCESSED_PATH, DATA_INTERIM_PATH, RANDOM_SEED, DEVICE
from .vision_encoder import VisionEncoder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SymbolicActionSequence:
    """Represents a sequence of symbolic actions for execution."""
    actions: List[str]
    task_id: str
    metadata: Dict[str, Any] = None

class LinearProbe(nn.Module):
    """
    Linear Probe architecture for adapting RoboDojo policy to real-world execution.
    
    Takes frozen visual features (from MobileViT) and maps them to low-level
    controller actions via a simple linear layer.
    """
    def __init__(self, input_dim: int = 512, output_dim: int = 6):
        """
        Initialize the Linear Probe.
        
        Args:
            input_dim: Dimension of the input feature vector (from vision encoder)
            output_dim: Dimension of the output action vector
        """
        super(LinearProbe, self).__init__()
        self.linear = nn.Linear(input_dim, output_dim)
        self.relu = nn.ReLU()
        
        # Initialize weights
        nn.init.xavier_uniform_(self.linear.weight)
        nn.init.zeros_(self.linear.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the linear probe.
        
        Args:
            x: Input feature tensor of shape (batch_size, input_dim)
        
        Returns:
            Output action tensor of shape (batch_size, output_dim)
        """
        return self.linear(self.relu(x))

def load_adapter_weights(
    model: nn.Module, 
    path: str, 
    strict: bool = True
) -> Dict[str, torch.Tensor]:
    """
    Load adapter weights from a saved checkpoint.
    
    Args:
        model: The model to load weights into
        path: Path to the checkpoint file
        strict: Whether to strictly enforce state dict keys matching
        
    Returns:
        The loaded state dictionary
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Adapter weights not found at {path}")
    
    logger.info(f"Loading adapter weights from {path}")
    checkpoint = torch.load(path, map_location=DEVICE, weights_only=True)
    model.load_state_dict(checkpoint['model_state_dict'], strict=strict)
    logger.info("Weights loaded successfully")
    return checkpoint

def adapt_policy_for_real_world(
    policy_weights: Dict[str, torch.Tensor],
    adapter_weights: Dict[str, torch.Tensor]
) -> Dict[str, torch.Tensor]:
    """
    Adapt the pre-trained RoboDojo weights with the trained adapter.
    
    Args:
        policy_weights: Original RoboDojo policy weights
        adapter_weights: Trained adapter weights
        
    Returns:
        Combined weights ready for real-world execution
    """
    logger.info("Adapting policy for real-world execution")
    # In a full implementation, this would merge the policy and adapter weights
    # For now, we return the adapter weights as the adaptation layer
    return adapter_weights

def execute_symbolic_sequence(
    sequence: SymbolicActionSequence,
    adapter_model: LinearProbe
) -> bool:
    """
    Execute a symbolic action sequence using the adapted controller.
    
    Args:
        sequence: The symbolic action sequence to execute
        adapter_model: The trained adapter model
        
    Returns:
        True if execution succeeded, False otherwise
    """
    logger.info(f"Executing symbolic sequence for task {sequence.task_id}")
    # Placeholder for actual execution logic
    # In reality, this would convert symbolic actions to low-level commands
    return True

def run_full_pipeline(
    tasks: List[Dict[str, Any]],
    adapter_model: LinearProbe,
    vision_encoder: VisionEncoder
) -> List[bool]:
    """
    Run the full adaptation and execution pipeline.
    
    Args:
        tasks: List of task specifications
        adapter_model: The trained adapter model
        vision_encoder: The frozen vision encoder
        
    Returns:
        List of execution success flags
    """
    results = []
    for task in tasks:
        # Extract features
        features = vision_encoder.encode(task['frames'])
        
        # Generate actions
        actions = adapter_model(features)
        
        # Create symbolic sequence
        sequence = SymbolicActionSequence(
            actions=[f"action_{i}" for i in range(actions.shape[1])],
            task_id=task['id']
        )
        
        # Execute
        success = execute_symbolic_sequence(sequence, adapter_model)
        results.append(success)
    
    return results

def run_adapter_pipeline(
    output_path: Optional[str] = None,
    train_split: float = 0.77,  # 14/18 for training
    validation_split: float = 0.23,  # 4/18 for validation
    num_epochs: int = 50,
    learning_rate: float = 1e-3,
    batch_size: int = 32,
    input_dim: int = 512,
    output_dim: int = 6
) -> Tuple[LinearProbe, Dict[str, Any]]:
    """
    Execute the full adapter training pipeline as specified in T010:
    1. Split tasks into training and validation sets
    2. Train the probe on training tasks
    3. Validate on hold-out tasks
    4. Discard split weights
    5. Retrain on ALL 18 tasks
    6. Save final weights
    
    Args:
        output_path: Path to save final weights (default: data/processed/adapter_weights.pt)
        train_split: Fraction of tasks for initial training
        validation_split: Fraction of tasks for validation
        num_epochs: Number of epochs for training
        learning_rate: Learning rate for optimizer
        batch_size: Batch size for training
        input_dim: Input feature dimension
        output_dim: Output action dimension
        
    Returns:
        Tuple of (final_model, training_metrics)
    """
    if output_path is None:
        output_path = os.path.join(DATA_PROCESSED_PATH, "adapter_weights.pt")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    logger.info(f"Starting adapter pipeline with output: {output_path}")
    
    # Step 1: Load and split tasks
    logger.info("Loading RoboDojo tasks...")
    all_tasks = list(stream_robodojo_tasks())
    logger.info(f"Loaded {len(all_tasks)} tasks")
    
    if len(all_tasks) < 18:
        logger.warning(f"Expected 18 tasks, got {len(all_tasks)}. Proceeding with available tasks.")
    
    # Set seed for reproducibility
    torch.manual_seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    
    # Shuffle and split
    indices = np.random.permutation(len(all_tasks))
    train_end = int(len(all_tasks) * train_split)
    val_end = int(len(all_tasks) * (train_split + validation_split))
    
    train_indices = indices[:train_end]
    val_indices = indices[train_end:val_end]
    test_indices = indices[val_end:]  # Remaining tasks (if any)
    
    train_tasks = [all_tasks[i] for i in train_indices]
    val_tasks = [all_tasks[i] for i in val_indices]
    
    logger.info(f"Training set: {len(train_tasks)} tasks")
    logger.info(f"Validation set: {len(val_tasks)} tasks")
    
    # Initialize vision encoder (frozen) and adapter
    vision_encoder = VisionEncoder(pretrained=True, freeze=True)
    adapter = LinearProbe(input_dim=input_dim, output_dim=output_dim).to(DEVICE)
    
    # Training setup
    criterion = nn.MSELoss()
    optimizer = optim.Adam(adapter.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.1)
    
    # Metrics storage
    training_metrics = {
        'train_losses': [],
        'val_losses': [],
        'train_accuracies': [],
        'val_accuracies': []
    }
    
    # Step 2: Train on training set
    logger.info(f"Training adapter on {len(train_tasks)} tasks...")
    adapter.train()
    
    for epoch in range(num_epochs):
        epoch_loss = 0.0
        epoch_acc = 0.0
        num_batches = 0
        
        for i in range(0, len(train_tasks), batch_size):
            batch_tasks = train_tasks[i:i+batch_size]
            
            # Prepare batch data
            inputs = []
            targets = []
            
            for task in batch_tasks:
                # Extract features using frozen vision encoder
                with torch.no_grad():
                    features = vision_encoder.encode(task['frames'])
                inputs.append(features)
                targets.append(torch.tensor(task['target_actions'], dtype=torch.float32))
            
            if not inputs:
                continue
                
            batch_x = torch.cat(inputs, dim=0).to(DEVICE)
            batch_y = torch.cat(targets, dim=0).to(DEVICE)
            
            # Forward pass
            optimizer.zero_grad()
            outputs = adapter(batch_x)
            loss = criterion(outputs, batch_y)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            num_batches += 1
            
            # Simple accuracy metric (placeholder)
            acc = (outputs.detach() == batch_y.detach()).float().mean().item()
            epoch_acc += acc
        
        avg_loss = epoch_loss / max(num_batches, 1)
        avg_acc = epoch_acc / max(num_batches, 1)
        training_metrics['train_losses'].append(avg_loss)
        training_metrics['train_accuracies'].append(avg_acc)
        
        scheduler.step()
        
        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}, Acc: {avg_acc:.4f}")
    
    # Step 3: Validate on hold-out tasks
    logger.info(f"Validating on {len(val_tasks)} tasks...")
    adapter.eval()
    val_loss = 0.0
    val_acc = 0.0
    num_batches = 0
    
    with torch.no_grad():
        for i in range(0, len(val_tasks), batch_size):
            batch_tasks = val_tasks[i:i+batch_size]
            
            inputs = []
            targets = []
            
            for task in batch_tasks:
                features = vision_encoder.encode(task['frames'])
                inputs.append(features)
                targets.append(torch.tensor(task['target_actions'], dtype=torch.float32))
            
            if not inputs:
                continue
                
            batch_x = torch.cat(inputs, dim=0).to(DEVICE)
            batch_y = torch.cat(targets, dim=0).to(DEVICE)
            
            outputs = adapter(batch_x)
            loss = criterion(outputs, batch_y)
            
            val_loss += loss.item()
            acc = (outputs == batch_y).float().mean().item()
            val_acc += acc
            num_batches += 1
    
    avg_val_loss = val_loss / max(num_batches, 1)
    avg_val_acc = val_acc / max(num_batches, 1)
    training_metrics['val_losses'].append(avg_val_loss)
    training_metrics['val_accuracies'].append(avg_val_acc)
    
    logger.info(f"Validation Loss: {avg_val_loss:.4f}, Validation Acc: {avg_val_acc:.4f}")
    
    # Step 4: Discard split weights
    logger.info("Discarding split weights (reinitializing for full training)...")
    # Reinitialize the model for full training
    adapter = LinearProbe(input_dim=input_dim, output_dim=output_dim).to(DEVICE)
    optimizer = optim.Adam(adapter.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.1)
    
    # Step 5: Retrain on ALL tasks
    logger.info(f"Retraining adapter on ALL {len(all_tasks)} tasks...")
    adapter.train()
    
    for epoch in range(num_epochs):
        epoch_loss = 0.0
        epoch_acc = 0.0
        num_batches = 0
        
        for i in range(0, len(all_tasks), batch_size):
            batch_tasks = all_tasks[i:i+batch_size]
            
            inputs = []
            targets = []
            
            for task in batch_tasks:
                with torch.no_grad():
                    features = vision_encoder.encode(task['frames'])
                inputs.append(features)
                targets.append(torch.tensor(task['target_actions'], dtype=torch.float32))
            
            if not inputs:
                continue
                
            batch_x = torch.cat(inputs, dim=0).to(DEVICE)
            batch_y = torch.cat(targets, dim=0).to(DEVICE)
            
            optimizer.zero_grad()
            outputs = adapter(batch_x)
            loss = criterion(outputs, batch_y)
            
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            num_batches += 1
            
            acc = (outputs.detach() == batch_y.detach()).float().mean().item()
            epoch_acc += acc
        
        avg_loss = epoch_loss / max(num_batches, 1)
        avg_acc = epoch_acc / max(num_batches, 1)
        
        scheduler.step()
        
        if (epoch + 1) % 10 == 0:
            logger.info(f"Full Training Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}, Acc: {avg_acc:.4f}")
    
    # Step 6: Save final weights
    logger.info(f"Saving final adapter weights to {output_path}")
    torch.save({
        'model_state_dict': adapter.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'epoch': num_epochs,
        'training_metrics': training_metrics,
        'input_dim': input_dim,
        'output_dim': output_dim
    }, output_path)
    
    logger.info("Adapter pipeline completed successfully")
    
    return adapter, training_metrics

def main():
    """Entry point for running the adapter pipeline."""
    logger.info("Starting controller adapter pipeline...")
    
    try:
        adapter, metrics = run_adapter_pipeline()
        logger.info("Pipeline completed. Check data/processed/adapter_weights.pt for results.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
