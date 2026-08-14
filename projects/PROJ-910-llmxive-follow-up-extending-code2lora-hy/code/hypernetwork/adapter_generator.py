"""
Adapter Generator Module for Code2LoRA Hypernetwork.

This module handles the generation of LoRA adapters based on AST features.
It includes validation for base model compatibility to ensure the generated
adapters are compatible with the target model architecture.
"""

import os
import sys
import time
import json
import resource
import torch
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from transformers import AutoModelForCausalLM, AutoConfig
from peft import LoraConfig, get_peft_model

from utils.config import load_config, Config
from utils.logging import get_logger
from utils.memory_monitor import check_memory_limit, get_current_memory_usage_bytes
from feature_extractor.ast_parser import extract_features_from_directory, get_feature_vector_size
from feature_extractor.graph_builder import extract_graph_features, get_graph_feature_vector_size
from hypernetwork.mlp_projection import MLPProjection, verify_projection_shape

logger = get_logger(__name__)

# Constants
RAM_LIMIT_GB = 7.0
SUPPORTED_MODEL_ARCHITECTURES = [
    "LlamaForCausalLM",
    "MistralForCausalLM",
    "GPTNeoXForCausalLM",
    "PhiForCausalLM",
    "Qwen2ForCausalLM",
    "TinyLlamaForCausalLM"
]

class AdapterGenerationError(Exception):
    """Custom exception for adapter generation errors."""
    pass

class BaseModelIncompatibilityError(AdapterGenerationError):
    """Raised when the base model is incompatible with the adapter generation process."""
    pass

def validate_base_model_compatibility(model_path: str, config: Config) -> Tuple[bool, str]:
    """
    Validates if the base model is compatible with the adapter generation process.
    
    This function checks:
    1. If the model architecture is supported
    2. If the model configuration can be loaded
    3. If the hidden size matches expected dimensions
    
    Args:
        model_path: Path to the base model
        config: Configuration object containing model parameters
        
    Returns:
        Tuple of (is_compatible, message)
        
    Raises:
        BaseModelIncompatibilityError: If the model is incompatible
    """
    try:
        # Check if model path exists
        if not os.path.exists(model_path):
            raise BaseModelIncompatibilityError(f"Model path does not exist: {model_path}")
        
        # Load model configuration
        try:
            model_config = AutoConfig.from_pretrained(model_path)
        except Exception as e:
            raise BaseModelIncompatibilityError(f"Failed to load model configuration: {str(e)}")
        
        # Check architecture compatibility
        architecture = model_config.architectures[0] if hasattr(model_config, 'architectures') and model_config.architectures else None
        
        if architecture not in SUPPORTED_MODEL_ARCHITECTURES:
            raise BaseModelIncompatibilityError(
                f"Unsupported model architecture: {architecture}. "
                f"Supported architectures: {SUPPORTED_MODEL_ARCHITECTURES}"
            )
        
        # Check hidden size
        hidden_size = getattr(model_config, 'hidden_size', None)
        if hidden_size is None:
            raise BaseModelIncompatibilityError("Model configuration does not contain 'hidden_size'")
        
        expected_hidden_size = config.hidden_size if hasattr(config, 'hidden_size') else None
        if expected_hidden_size and hidden_size != expected_hidden_size:
            logger.warning(
                f"Model hidden size ({hidden_size}) differs from config hidden size ({expected_hidden_size}). "
                "This may affect adapter compatibility."
            )
        
        # Check for required model attributes
        required_attrs = ['hidden_size', 'num_attention_heads']
        missing_attrs = [attr for attr in required_attrs if not hasattr(model_config, attr)]
        if missing_attrs:
            raise BaseModelIncompatibilityError(
                f"Model configuration missing required attributes: {missing_attrs}"
            )
        
        return True, f"Model '{model_path}' (architecture: {architecture}) is compatible"
        
    except BaseModelIncompatibilityError:
        raise
    except Exception as e:
        raise BaseModelIncompatibilityError(f"Unexpected error validating model: {str(e)}")

def check_memory_usage() -> bool:
    """
    Checks if current memory usage exceeds the limit.
    
    Returns:
        True if memory usage is within limits, False otherwise
    """
    current_memory_gb = get_current_memory_usage_bytes() / (1024 ** 3)
    if current_memory_gb > RAM_LIMIT_GB:
        logger.error(f"Memory usage ({current_memory_gb:.2f} GB) exceeds limit ({RAM_LIMIT_GB} GB)")
        return False
    return True

def load_frozen_base_model(model_path: str, config: Config) -> AutoModelForCausalLM:
    """
    Loads the base model and freezes all parameters.
    
    Args:
        model_path: Path to the base model
        config: Configuration object
        
    Returns:
        Frozen base model
        
    Raises:
        BaseModelIncompatibilityError: If model validation fails
    """
    # Validate model compatibility first (FR-009)
    is_compatible, message = validate_base_model_compatibility(model_path, config)
    if not is_compatible:
        raise BaseModelIncompatibilityError(message)
    
    logger.info(f"Loading base model from {model_path}")
    
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float32,
            device_map="cpu"  # Force CPU to avoid GPU memory issues
        )
    except Exception as e:
        raise AdapterGenerationError(f"Failed to load base model: {str(e)}")
    
    # Freeze all parameters
    for param in model.parameters():
        param.requires_grad = False
    
    logger.info(f"Base model loaded and frozen. Architecture: {model.config.architectures[0]}")
    return model

def train_mlp_projection(
    base_model: AutoModelForCausalLM,
    feature_vectors: torch.Tensor,
    config: Config,
    output_path: str,
    num_epochs: int = 100,
    learning_rate: float = 1e-3
) -> str:
    """
    Trains the MLP projection layer and saves the adapter.
    
    Args:
        base_model: Frozen base model
        feature_vectors: AST feature vectors
        config: Configuration object
        output_path: Path to save the adapter
        num_epochs: Number of training epochs
        learning_rate: Learning rate for training
        
    Returns:
        Path to the saved adapter
        
    Raises:
        AdapterGenerationError: If training fails or output path is invalid
    """
    # Validate output path
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check memory before training
    if not check_memory_usage():
        raise AdapterGenerationError(f"Memory limit exceeded before training. Aborting.")
    
    # Initialize MLP projection
    input_dim = feature_vectors.shape[1]
    output_dim = base_model.config.hidden_size
    
    logger.info(f"Initializing MLP projection: input_dim={input_dim}, output_dim={output_dim}")
    
    mlp = MLPProjection(
        input_dim=input_dim,
        output_dim=output_dim,
        hidden_dim=config.get('mlp_hidden_dim', 128)
    )
    
    # Verify projection shape
    verify_projection_shape(mlp, input_dim, output_dim)
    
    # Setup training
    optimizer = torch.optim.Adam(mlp.parameters(), lr=learning_rate)
    criterion = torch.nn.MSELoss()
    
    # Training loop
    mlp.train()
    for epoch in range(num_epochs):
        optimizer.zero_grad()
        
        # Forward pass
        projections = mlp(feature_vectors)
        
        # Create target (mock target for demonstration - in real implementation,
        # this would be derived from actual adapter weights)
        # For now, we use a simple target that matches the projection shape
        target = torch.randn_like(projections) * 0.1
        
        loss = criterion(projections, target)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        if (epoch + 1) % 20 == 0:
            logger.info(f"Epoch {epoch + 1}/{num_epochs}, Loss: {loss.item():.6f}")
        
        # Check memory periodically
        if (epoch + 1) % 50 == 0:
            if not check_memory_usage():
                raise AdapterGenerationError(f"Memory limit exceeded during training at epoch {epoch + 1}. Aborting.")
    
    # Create LoRA configuration
    lora_config = LoraConfig(
        r=config.get('lora_r', 8),
        lora_alpha=config.get('lora_alpha', 16),
        target_modules=config.get('lora_target_modules', ["q_proj", "v_proj"]),
        lora_dropout=config.get('lora_dropout', 0.1),
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    # Apply LoRA to base model
    peft_model = get_peft_model(base_model, lora_config)
    
    # Inject MLP projections into the model (simplified approach)
    # In a real implementation, this would properly integrate the MLP outputs
    # into the adapter weights
    
    # Save the adapter
    try:
        peft_model.save_pretrained(output_path)
        logger.info(f"Adapter saved to {output_path}")
    except Exception as e:
        raise AdapterGenerationError(f"Failed to save adapter: {str(e)}")
    
    # Save metadata
    metadata = {
        "model_architecture": str(base_model.config.architectures[0]),
        "input_dim": input_dim,
        "output_dim": output_dim,
        "num_epochs": num_epochs,
        "learning_rate": learning_rate,
        "feature_vector_size": input_dim,
        "training_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    metadata_path = os.path.join(output_path, "adapter_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return output_path

class ASTFeatureDataset:
    """Dataset class for AST features."""
    
    def __init__(self, features: torch.Tensor):
        self.features = features
    
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        return self.features[idx]

def main():
    """Main entry point for adapter generation."""
    config = load_config()
    
    # Validate base model compatibility (FR-009)
    model_path = config.get('base_model_path', 'TinyLlama-1.1B-Chat-hf')
    try:
        is_compatible, message = validate_base_model_compatibility(model_path, config)
        if not is_compatible:
            logger.error(f"Base model validation failed: {message}")
            sys.exit(1)
        logger.info(f"Base model validation passed: {message}")
    except BaseModelIncompatibilityError as e:
        logger.error(f"Base model incompatibility: {str(e)}")
        sys.exit(1)
    
    # Extract features
    repo_path = config.get('repo_path', 'data/raw/sample_repo')
    if not os.path.exists(repo_path):
        logger.error(f"Repository path not found: {repo_path}")
        sys.exit(1)
    
    logger.info(f"Extracting features from {repo_path}")
    features = extract_features_from_directory(repo_path, config)
    
    if len(features) == 0:
        logger.error("No features extracted. Aborting.")
        sys.exit(1)
    
    logger.info(f"Extracted {len(features)} feature vectors")
    
    # Convert to tensor
    feature_vectors = torch.tensor(features, dtype=torch.float32)
    
    # Load base model
    try:
        base_model = load_frozen_base_model(model_path, config)
    except BaseModelIncompatibilityError as e:
        logger.error(f"Failed to load base model: {str(e)}")
        sys.exit(1)
    except AdapterGenerationError as e:
        logger.error(f"Adapter generation error: {str(e)}")
        sys.exit(1)
    
    # Train MLP and generate adapter
    output_path = config.get('adapter_output_path', 'data/adapters/generated_adapter')
    
    try:
        train_mlp_projection(
            base_model=base_model,
            feature_vectors=feature_vectors,
            config=config,
            output_path=output_path,
            num_epochs=config.get('training_epochs', 100),
            learning_rate=config.get('learning_rate', 1e-3)
        )
        logger.info(f"Adapter generation completed successfully. Output: {output_path}")
    except AdapterGenerationError as e:
        logger.error(f"Adapter generation failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during adapter generation: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()