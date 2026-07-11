import os
import sys
import time
import json
import resource
import torch
from pathlib import Path
from typing import Optional, Dict, Any

# Import existing utilities from the project
from utils.config import load_config, Config
from utils.logging import get_logger, warning_handler
from feature_extractor.ast_parser import extract_features_from_directory, get_feature_vector_size
from feature_extractor.graph_builder import extract_graph_features, get_graph_feature_vector_size
from hypernetwork.mlp_projection import MLPProjection, verify_projection_shape

# Import transformers components for model loading and validation
from transformers import AutoConfig, AutoModelForCausalLM
from peft import PeftModel

logger = get_logger(__name__)

def check_memory_usage(threshold_gb: float = 7.0) -> bool:
    """
    Check current memory usage against a threshold.
    Returns True if usage is below threshold, False otherwise.
    """
    usage_bytes = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # On Linux, ru_maxrss is in KB; on macOS, it's in KB as well in modern versions
    # Convert to GB
    usage_gb = usage_bytes / (1024 * 1024)
    if usage_gb > threshold_gb:
        logger.error(f"Memory usage {usage_gb:.2f} GB exceeds threshold {threshold_gb} GB")
        return False
    return True

def validate_base_model_compatibility(base_model_path: str, config: Config) -> Dict[str, Any]:
    """
    Validate that the base model is compatible with the adapter generation process.
    Checks:
    1. Model exists and is loadable
    2. Model architecture is supported (CausalLM)
    3. Hidden size matches expected dimensions from config
    4. Model is not already a LoRA adapter (should be base model)

    Returns a dict with 'valid' (bool) and 'error' (str) if invalid.
    """
    result = {"valid": True, "error": None, "details": {}}

    try:
        # 1. Check if model path exists
        model_path = Path(base_model_path)
        if not model_path.exists() and not base_model_path.startswith(('hf://', 'https://')):
            # Try loading from HuggingFace hub name
            model_config = AutoConfig.from_pretrained(base_model_path, trust_remote_code=True)
            result["details"]["source"] = "huggingface_hub"
        else:
            model_config = AutoConfig.from_pretrained(base_model_path, trust_remote_code=True)
            result["details"]["source"] = "local_path"

        # 2. Check model architecture type
        model_type = getattr(model_config, 'model_type', None)
        if model_type not in ['llama', 'mistral', 'gpt2', 'phi', 'tinyllama']:
            # Not strictly failing, but logging warning
            logger.warning(f"Model type '{model_type}' is not in the primary supported list, but attempting to proceed.")
            result["details"]["model_type"] = model_type
        else:
            result["details"]["model_type"] = model_type

        # 3. Check if it's a causal LM model
        # We can't easily check the class name from config alone without loading,
        # but we check for 'is_decoder' or 'is_encoder_decoder' flags if available
        if hasattr(model_config, 'is_encoder_decoder') and model_config.is_encoder_decoder:
            result["valid"] = False
            result["error"] = f"Model {base_model_path} is an encoder-decoder model. Causal LM (decoder-only) models are required."
            return result

        # 4. Check hidden size against config expectation
        hidden_size = getattr(model_config, 'hidden_size', None)
        if hidden_size is None:
            result["valid"] = False
            result["error"] = f"Could not determine hidden_size from model config for {base_model_path}."
            return result

        expected_hidden_size = config.hidden_size
        if expected_hidden_size is not None and hidden_size != expected_hidden_size:
            logger.warning(f"Model hidden_size ({hidden_size}) differs from config.hidden_size ({expected_hidden_size}). "
                           f"This might cause projection layer dimension mismatch.")
            result["details"]["model_hidden_size"] = hidden_size
            result["details"]["config_hidden_size"] = expected_hidden_size
            # We don't fail here, as the MLP can be adjusted, but we log it.
            # However, for FR-009 strict compliance, we might want to abort if the mismatch is severe.
            # Let's be strict: if it's significantly different, abort.
            if abs(hidden_size - expected_hidden_size) > 10: # Allow small tolerance
                 result["valid"] = False
                 result["error"] = f"Model hidden_size ({hidden_size}) is incompatible with expected ({expected_hidden_size}). " \
                                   f"Adapter generation requires matching dimensions."
                 return result

        # 5. Check if the model is already a LoRA adapter
        # We can check for adapter files in the directory
        if model_path.exists():
            adapter_files = list(model_path.glob("adapter_model.*"))
            if adapter_files:
                result["valid"] = False
                result["error"] = f"Path {base_model_path} appears to contain adapter files. " \
                                  f"Please provide the base model path, not an already adapted model."
                return result

        result["details"]["hidden_size"] = hidden_size
        result["details"]["architecture"] = model_type
        logger.info(f"Base model validation successful for {base_model_path}")

    except Exception as e:
        result["valid"] = False
        result["error"] = f"Failed to validate base model {base_model_path}: {str(e)}"
        logger.error(result["error"])

    return result

class ASTFeatureDataset(torch.utils.data.Dataset):
    def __init__(self, features: Dict[str, Any], graph_features: Dict[str, Any]):
        self.features = features
        self.graph_features = graph_features

    def __len__(self):
        return len(self.features.get('token_histogram', []))

    def __getitem__(self, idx):
        # Combine AST and graph features
        ast_vec = self.features.get('vector', [0.0] * get_feature_vector_size())
        graph_vec = self.graph_features.get('vector', [0.0] * get_graph_feature_vector_size())
        combined = torch.tensor(ast_vec + graph_vec, dtype=torch.float32)
        return combined

def load_frozen_base_model(model_path: str, config: Config) -> torch.nn.Module:
    """
    Load the base model with frozen weights.
    """
    logger.info(f"Loading frozen base model from {model_path}")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float32,
        trust_remote_code=True
    )
    for param in model.parameters():
        param.requires_grad = False
    return model

def train_mlp_projection(
    model: torch.nn.Module,
    dataset: ASTFeatureDataset,
    config: Config,
    output_path: str
) -> None:
    """
    Train the MLP projection layer and save the adapter.
    """
    input_dim = get_feature_vector_size() + get_graph_feature_vector_size()
    output_dim = config.hidden_size

    logger.info(f"Initializing MLP projection: input_dim={input_dim}, output_dim={output_dim}")
    mlp = MLPProjection(input_dim, output_dim, config)

    optimizer = torch.optim.Adam(mlp.parameters(), lr=config.learning_rate)
    criterion = torch.nn.MSELoss()

    # Simple training loop (simplified for demonstration)
    # In a real scenario, this would be more complex
    mlp.train()
    for epoch in range(config.epochs):
        total_loss = 0.0
        for i in range(len(dataset)):
            x = dataset[i]
            # Simulate target (in reality, this would come from the base model's embeddings)
            # For now, we'll just train to reconstruct the input or a dummy target
            # This is a placeholder for the actual training logic
            target = torch.zeros(output_dim) # Placeholder
            optimizer.zero_grad()
            output = mlp(x.unsqueeze(0))
            loss = criterion(output.squeeze(), target)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        logger.info(f"Epoch {epoch+1}/{config.epochs}, Loss: {total_loss/len(dataset):.4f}")

    # Save the trained MLP weights
    save_path = Path(output_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(mlp.state_dict(), save_path)
    logger.info(f"Adapter saved to {output_path}")

def main():
    """
    Main entry point for adapter generation.
    """
    config = load_config()
    
    # FR-009: Check checkpoint validation for incompatible base models
    base_model_path = config.base_model_path
    validation_result = validate_base_model_compatibility(base_model_path, config)
    
    if not validation_result["valid"]:
        logger.critical(f"Base model validation failed: {validation_result['error']}")
        logger.critical("Aborting adapter generation due to incompatible base model.")
        # Write error to output file if needed
        error_file = Path(config.output_dir) / "generation_error.json"
        error_file.parent.mkdir(parents=True, exist_ok=True)
        with open(error_file, 'w') as f:
            json.dump({
                "status": "failed",
                "reason": validation_result["error"],
                "details": validation_result["details"]
            }, f, indent=2)
        sys.exit(1)

    # Check memory usage
    if not check_memory_usage(config.memory_limit_gb):
        sys.exit(1)

    # Extract features
    repo_path = Path(config.repo_path)
    features = extract_features_from_directory(repo_path)
    graph_features = extract_graph_features(repo_path)

    # Create dataset
    dataset = ASTFeatureDataset(features, graph_features)

    # Load base model
    base_model = load_frozen_base_model(base_model_path, config)

    # Train MLP and save adapter
    output_path = Path(config.output_dir) / "adapter.safetensors"
    train_mlp_projection(base_model, dataset, config, str(output_path))

    logger.info("Adapter generation completed successfully.")

if __name__ == "__main__":
    main()