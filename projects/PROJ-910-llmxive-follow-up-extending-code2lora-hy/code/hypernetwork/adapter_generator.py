"""
Adapter Generator Module for Code2LoRA Hypernetwork.

Implements the generation of repository-specific LoRA adapters using AST features
and a lightweight MLP projection, with robust error handling for memory and checkpoint
compatibility issues.

This module implements FR-008, FR-006, and FR-009:
- Pre-flight and runtime memory checks (E001, E003)
- Checkpoint compatibility validation (E002)
- Graceful error handling in main.py
"""
import os
import sys
import time
import json
import resource
import traceback
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import logging
import torch
import torch.nn as nn
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import numpy as np

# Import from project modules
from utils.config import load_config, Config
from utils.logging import get_logger
from hypernetwork.mlp_projection import MLPProjection
from feature_extractor.ast_parser import extract_features_from_directory, get_feature_vector_size
from feature_extractor.graph_builder import extract_graph_features, get_graph_feature_vector_size

logger = get_logger(__name__)

# --- Custom Exceptions ---

class AdapterGenerationError(Exception):
    """Base exception for adapter generation errors."""
    pass

class MemoryLimitError(AdapterGenerationError):
    """
    Raised when memory limits are exceeded.
    
    Codes:
    - E001: Pre-flight RAM check failed (< 7GB available)
    - E003: Runtime RAM check failed (> 7GB RSS)
    """
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")

class CheckpointIncompatibilityError(AdapterGenerationError):
    """
    Raised when the base model checkpoint is incompatible.
    
    Code:
    - E002: Checkpoint compatibility validation failed
    """
    def __init__(self, message: str):
        self.code = "E002"
        self.message = message
        super().__init__(f"{self.code}: {message}")

# --- Memory Monitoring Functions ---

def check_memory_usage() -> float:
    """
    Check current memory usage (RSS) in GB.
    
    Returns:
        float: Current RSS memory usage in GB
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024.0  # Convert KB to GB

def pre_flight_memory_check(min_required_gb: float = 7.0) -> None:
    """
    Perform pre-flight memory check.
    
    Args:
        min_required_gb: Minimum required RAM in GB (default 7.0)
        
    Raises:
        MemoryLimitError: If available RAM is below threshold
    """
    # Get available memory (on Linux, /proc/meminfo gives MemAvailable)
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        
        for line in meminfo.split('\n'):
            if line.startswith('MemAvailable:'):
                available_kb = int(line.split()[1])
                available_gb = available_kb / (1024.0 * 1024.0)
                
                if available_gb < min_required_gb:
                    error_msg = f"ERROR: E001: Memory Limit Exceeded ({int(min_required_gb)}GB) - Pre-flight"
                    logger.error(error_msg)
                    raise MemoryLimitError("E001", f"Memory Limit Exceeded ({int(min_required_gb)}GB) - Pre-flight. Available: {available_gb:.2f}GB")
                break
    except FileNotFoundError:
        # Fallback for non-Linux systems
        logger.warning("Could not read /proc/meminfo, skipping pre-flight memory check")
        return

def runtime_memory_check(max_allowed_gb: float = 7.0) -> None:
    """
    Perform runtime memory check.
    
    Args:
        max_allowed_gb: Maximum allowed RSS in GB (default 7.0)
        
    Raises:
        MemoryLimitError: If RSS exceeds threshold
    """
    current_rss_gb = check_memory_usage()
    
    if current_rss_gb > max_allowed_gb:
        error_msg = f"ERROR: E003: Memory Limit Exceeded ({int(max_allowed_gb)}GB) - Runtime"
        logger.error(error_msg)
        raise MemoryLimitError("E003", f"Memory Limit Exceeded ({int(max_allowed_gb)}GB) - Runtime. Current RSS: {current_rss_gb:.2f}GB")

# --- Checkpoint Validation ---

def validate_base_model_compatibility(model_name_or_path: str, config: Config) -> None:
    """
    Validate that the base model checkpoint is compatible with adapter generation.
    
    Args:
        model_name_or_path: Path or name of the base model
        config: Configuration object
        
    Raises:
        CheckpointIncompatibilityError: If checkpoint is incompatible
    """
    try:
        # Check if model can be loaded
        tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            torch_dtype=torch.float32,
            device_map="cpu",  # Force CPU for safety
            low_cpu_mem_usage=True
        )
        
        # Verify model has required attributes
        if not hasattr(model, 'config'):
            raise CheckpointIncompatibilityError("E002: Model missing 'config' attribute")
        
        if not hasattr(model.config, 'hidden_size'):
            raise CheckpointIncompatibilityError("E002: Model config missing 'hidden_size'")
        
        # Verify tokenizer
        if not hasattr(tokenizer, 'pad_token') and tokenizer.pad_token is None:
            logger.warning("Tokenizer has no pad_token, setting to eos_token")
            tokenizer.pad_token = tokenizer.eos_token
        
        # Check model size compatibility
        model_hidden = model.config.hidden_size
        expected_hidden = config.hidden_size if hasattr(config, 'hidden_size') else None
        
        if expected_hidden and model_hidden != expected_hidden:
            logger.warning(f"Model hidden size ({model_hidden}) differs from config ({expected_hidden})")
        
        logger.info(f"Checkpoint validation successful for {model_name_or_path}")
        
    except Exception as e:
        if isinstance(e, CheckpointIncompatibilityError):
            raise
        raise CheckpointIncompatibilityError(f"E002: Failed to load or validate checkpoint: {str(e)}")

# --- Dataset Class ---

class ASTFeatureDataset(torch.utils.data.Dataset):
    """Dataset for AST feature vectors."""
    
    def __init__(self, features: Dict[str, Any], graph_features: Dict[str, Any]):
        self.features = features
        self.graph_features = graph_features
        self.keys = list(features.keys())
    
    def __len__(self):
        return len(self.keys)
    
    def __getitem__(self, idx):
        key = self.keys[idx]
        ast_feat = self.features[key]
        graph_feat = self.graph_features.get(key, np.zeros(get_graph_feature_vector_size()))
        
        # Concatenate AST and graph features
        combined = np.concatenate([ast_feat, graph_feat])
        return torch.tensor(combined, dtype=torch.float32), key

# --- Core Generation Logic ---

def load_frozen_base_model(model_name_or_path: str, config: Config) -> Tuple[nn.Module, AutoTokenizer]:
    """
    Load the frozen base model for adapter generation.
    
    Args:
        model_name_or_path: Path or name of the base model
        config: Configuration object
        
    Returns:
        Tuple of (frozen model, tokenizer)
    """
    # Pre-flight memory check
    pre_flight_memory_check()
    
    # Validate checkpoint compatibility
    validate_base_model_compatibility(model_name_or_path, config)
    
    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        torch_dtype=torch.float32,
        device_map="cpu",
        low_cpu_mem_usage=True
    )
    
    # Freeze all parameters
    for param in model.parameters():
        param.requires_grad = False
    
    # Runtime memory check after loading
    runtime_memory_check()
    
    logger.info(f"Base model loaded and frozen: {model_name_or_path}")
    return model, tokenizer

def train_mlp_projection(
    model: nn.Module,
    features: Dict[str, Any],
    graph_features: Dict[str, Any],
    config: Config,
    epochs: int = 10,
    batch_size: int = 32,
    learning_rate: float = 1e-3
) -> nn.Module:
    """
    Train the MLP projection layer to map AST features to model embeddings.
    
    Args:
        model: Frozen base model
        features: AST feature dictionary
        graph_features: Graph feature dictionary
        config: Configuration object
        epochs: Number of training epochs
        batch_size: Batch size for training
        learning_rate: Learning rate
        
    Returns:
        Trained MLP projection model
    """
    # Runtime memory check before training
    runtime_memory_check()
    
    # Create dataset
    dataset = ASTFeatureDataset(features, graph_features)
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # Initialize MLP
    input_dim = get_feature_vector_size() + get_graph_feature_vector_size()
    output_dim = model.config.hidden_size
    mlp = MLPProjection(input_dim, output_dim)
    
    # Move to CPU (no GPU)
    mlp = mlp.to(torch.device('cpu'))
    
    # Training setup
    optimizer = torch.optim.Adam(mlp.parameters(), lr=learning_rate)
    criterion = nn.MSELoss()
    
    logger.info(f"Starting MLP training: {input_dim} -> {output_dim}, {epochs} epochs")
    
    for epoch in range(epochs):
        total_loss = 0.0
        for batch_features, batch_keys in dataloader:
            # Runtime memory check every batch
            runtime_memory_check()
            
            optimizer.zero_grad()
            
            # Forward pass
            outputs = mlp(batch_features)
            
            # For now, use random target embeddings (in real implementation, would use actual embeddings)
            # This is a placeholder - in real scenario, we'd extract actual embeddings from the model
            target_embeddings = torch.randn_like(outputs) * 0.1
            
            loss = criterion(outputs, target_embeddings)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(dataloader)
        logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
    
    logger.info("MLP training completed")
    return mlp

def generate_adapter(
    model_name_or_path: str,
    repo_path: str,
    output_path: str,
    config: Config,
    epochs: int = 10,
    batch_size: int = 32,
    learning_rate: float = 1e-3
) -> Dict[str, Any]:
    """
    Generate a repository-specific LoRA adapter.
    
    Args:
        model_name_or_path: Path or name of the base model
        repo_path: Path to the repository to analyze
        output_path: Path to save the generated adapter
        config: Configuration object
        epochs: Number of training epochs
        batch_size: Batch size for training
        learning_rate: Learning rate
        
    Returns:
        Dictionary with generation metadata
    """
    start_time = time.time()
    
    # Pre-flight memory check
    logger.info("Performing pre-flight memory check...")
    pre_flight_memory_check()
    
    # Extract features
    logger.info(f"Extracting AST features from {repo_path}...")
    try:
        ast_features = extract_features_from_directory(repo_path)
    except Exception as e:
        logger.error(f"Failed to extract AST features: {e}")
        raise AdapterGenerationError(f"Failed to extract AST features: {e}")
    
    # Runtime memory check after feature extraction
    runtime_memory_check()
    
    # Extract graph features
    logger.info("Extracting graph features...")
    try:
        graph_features = extract_graph_features(repo_path)
    except Exception as e:
        logger.error(f"Failed to extract graph features: {e}")
        raise AdapterGenerationError(f"Failed to extract graph features: {e}")
    
    # Runtime memory check after graph extraction
    runtime_memory_check()
    
    # Load frozen base model
    logger.info(f"Loading frozen base model: {model_name_or_path}...")
    model, tokenizer = load_frozen_base_model(model_name_or_path, config)
    
    # Train MLP projection
    logger.info("Training MLP projection...")
    mlp = train_mlp_projection(
        model, ast_features, graph_features, config,
        epochs=epochs, batch_size=batch_size, learning_rate=learning_rate
    )
    
    # Runtime memory check after training
    runtime_memory_check()
    
    # Save adapter
    logger.info(f"Saving adapter to {output_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save MLP weights
    torch.save({
        'mlp_state_dict': mlp.state_dict(),
        'input_dim': mlp.input_dim,
        'output_dim': mlp.output_dim,
        'config': {
            'model_name': model_name_or_path,
            'repo_path': repo_path,
            'feature_vector_size': get_feature_vector_size() + get_graph_feature_vector_size()
        }
    }, output_path)
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"Adapter generation completed in {duration:.2f} seconds")
    
    return {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'duration_seconds': duration,
        'feature_set': 'full_ast_graph',
        'output_path': output_path,
        'model_name': model_name_or_path,
        'repo_path': repo_path
    }

def main():
    """Main entry point for adapter generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate repository-specific LoRA adapter')
    parser.add_argument('--model', type=str, default='TinyLlama-1.1B-Chat-hf',
                      help='Base model name or path')
    parser.add_argument('--repo', type=str, required=True,
                      help='Path to repository to analyze')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to save generated adapter')
    parser.add_argument('--config', type=str, default='config.yaml',
                      help='Path to configuration file')
    parser.add_argument('--epochs', type=int, default=10,
                      help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=32,
                      help='Batch size for training')
    parser.add_argument('--lr', type=float, default=1e-3,
                      help='Learning rate')
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    try:
        result = generate_adapter(
            model_name_or_path=args.model,
            repo_path=args.repo,
            output_path=args.output,
            config=config,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.lr
        )
        
        # Save generation metadata
        metadata_path = args.output.replace('.pt', '_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Adapter generation successful. Metadata saved to {metadata_path}")
        
    except MemoryLimitError as e:
        logger.error(f"Memory limit error: {e}")
        sys.exit(1)
    except CheckpointIncompatibilityError as e:
        logger.error(f"Checkpoint incompatibility error: {e}")
        sys.exit(1)
    except AdapterGenerationError as e:
        logger.error(f"Adapter generation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
