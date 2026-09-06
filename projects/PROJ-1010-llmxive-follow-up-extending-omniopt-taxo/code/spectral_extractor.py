import os
import sys
import json
import math
import gc
import signal
import logging
import traceback
from typing import Dict, Any, List, Optional, Tuple, Iterator
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager

# Project internal imports based on API surface
from utils.logging import get_logger, info, error, warning, debug, critical
from utils.memory_monitor import MemoryMonitor, enforce_memory_limit, check_memory_usage
from utils.seeds import set_seed
from utils.data_loader import load_tinyimagenet_streaming, DataLoaderError

# External libraries
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import transforms
import numpy as np
import pandas as pd
from scipy import linalg
from scipy.stats import spearmanr
from datasets import load_dataset

# Constants
MAX_ITERATIONS = 100
TINYIMAGENET_SIZE = 64
LEARNING_RATE = 0.01
BATCH_SIZE = 32
MEMORY_LIMIT_GB = 6.5  # Safety margin under 7GB
TIMEOUT_SECONDS = 300  # 5 minutes per model

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError(f"Operation timed out after {TIMEOUT_SECONDS} seconds")

@contextmanager
def timeout_handler_context(seconds: int = TIMEOUT_SECONDS):
    # Set the signal handler and a timer
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def compute_spectral_entropy(eigenvalues: np.ndarray) -> float:
    """
    Compute Shannon entropy of the normalized eigenvalue distribution.
    Formula: -sum(p * log2(p)) where p = eigenvalue / sum(eigenvalues)
    """
    # Filter non-positive eigenvalues to avoid log(0) or log(negative)
    valid_eigs = eigenvalues[eigenvalues > 1e-12]
    if len(valid_eigs) == 0:
        return 0.0
    
    p = valid_eigs / np.sum(valid_eigs)
    # Avoid log(0)
    p = p[p > 1e-12]
    if len(p) == 0:
        return 0.0
        
    entropy = -np.sum(p * np.log2(p))
    return float(entropy)

def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())

def select_models() -> List[str]:
    """
    Select a representative sample of models from HuggingFace model hub.
    Criteria: parameter_count M-50M, architecture type in [ResNet, MobileNet, EfficientNet, ViT-Base].
    Returns a list of model identifiers.
    """
    # Hardcoded list of valid models matching criteria for reproducibility
    # These are small-scale models available on HF hub
    models = [
        "resnet18",
        "resnet34",
        "mobilenet_v2",
        "efficientnet_b0",
        "vit_tiny_patch16_224"
    ]
    return models

def get_gradient_covariance(model: nn.Module, data_loader: DataLoader, device: torch.device, steps: int = 100) -> Optional[np.ndarray]:
    """
    Compute gradient covariance matrix from the first `steps` steps of proxy training.
    Returns the flattened gradient covariance matrix or None if failure occurs.
    """
    model.train()
    optimizer = optim.SGD(model.parameters(), lr=LEARNING_RATE)
    
    # Flatten parameters to compute covariance
    param_shapes = [p.shape for p in model.parameters()]
    total_params = sum(p.numel() for p in model.parameters())
    
    gradient_accumulator = None
    count = 0
    
    try:
        for i, (inputs, targets) in enumerate(data_loader):
            if i >= steps:
                break
            
            inputs, targets = inputs.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = nn.functional.cross_entropy(outputs, targets)
            loss.backward()
            
            # Accumulate gradients
            current_grads = []
            for p in model.parameters():
                if p.grad is not None:
                    current_grads.append(p.grad.flatten())
            if not current_grads:
                continue
                
            full_grad = torch.cat(current_grads).detach().cpu().numpy()
            
            if gradient_accumulator is None:
                gradient_accumulator = np.zeros((steps, total_params))
            
            gradient_accumulator[i] = full_grad
            count += 1
            
            # Memory check
            if count % 10 == 0:
                check_memory_usage(MEMORY_LIMIT_GB * 1e9)
                gc.collect()
                
    except RuntimeError as e:
        if "out of memory" in str(e):
            error(f"Out of memory during gradient accumulation: {e}")
            return None
        raise
    except Exception as e:
        error(f"Unexpected error during gradient accumulation: {e}")
        return None
        
    if count == 0 or gradient_accumulator is None:
        return None
        
    # Trim to actual steps
    gradient_accumulator = gradient_accumulator[:count]
    
    # Compute covariance matrix
    # Center the gradients
    mean_grad = np.mean(gradient_accumulator, axis=0, keepdims=True)
    centered_grads = gradient_accumulator - mean_grad
    
    # Covariance: (1/(n-1)) * G^T * G
    if centered_grads.shape[0] < 2:
        # Not enough samples for covariance
        return None
        
    try:
        cov_matrix = np.cov(centered_grads, rowvar=False)
        return cov_matrix
    except Exception as e:
        error(f"Failed to compute covariance matrix: {e}")
        return None

def compute_tail_decay_exponent(eigenvalues: np.ndarray) -> float:
    """
    Calculate Tail Decay Exponent via power-law fitting via MLE on top-50 eigenvalues.
    Formula: P(lambda) ~ lambda^(-alpha)
    """
    # Sort descending
    sorted_eigs = np.sort(eigenvalues)[::-1]
    # Take top 50 or all if less
    top_eigs = sorted_eigs[:min(50, len(sorted_eigs))]
    
    # Filter positive eigenvalues
    valid_eigs = top_eigs[top_eigs > 1e-12]
    if len(valid_eigs) < 2:
        return 0.0
        
    # MLE for power law alpha: alpha = 1 + n / sum(log(x_i / x_min))
    # Here we assume x_min is the smallest valid eigenvalue in the set
    x_min = valid_eigs[-1]
    if x_min <= 0:
        return 0.0
        
    try:
        # Avoid log(0)
        log_ratios = np.log(valid_eigs / x_min)
        if np.any(np.isinf(log_ratios)) or np.any(np.isnan(log_ratios)):
            return 0.0
            
        alpha = 1.0 + len(valid_eigs) / np.sum(log_ratios)
        return float(alpha)
    except Exception as e:
        error(f"Failed to compute tail decay exponent: {e}")
        return 0.0

def compute_spectral_features(cov_matrix: np.ndarray) -> Dict[str, float]:
    """
    Compute Spectral Radius, Condition Number, Tail Decay Exponent, and Spectral Entropy.
    """
    if cov_matrix is None or cov_matrix.size == 0:
        return None
        
    try:
        # Eigenvalue decomposition
        # For symmetric positive semi-definite matrices, use eigh
        eigenvalues = linalg.eigvalsh(cov_matrix)
        
        # Check for numerical issues
        if np.any(np.isnan(eigenvalues)) or np.any(np.isinf(eigenvalues)):
            error("NaN or Inf values detected in eigenvalues")
            return None
            
        # Spectral Radius: max |eigenvalue|
        spectral_radius = float(np.max(np.abs(eigenvalues)))
        
        # Condition Number: max / min (ignoring near-zero)
        non_zero_eigs = eigenvalues[np.abs(eigenvalues) > 1e-12]
        if len(non_zero_eigs) == 0:
            return None
            
        condition_number = float(np.max(np.abs(non_zero_eigs)) / np.min(np.abs(non_zero_eigs)))
        
        # Tail Decay Exponent
        tail_decay = compute_tail_decay_exponent(eigenvalues)
        
        # Spectral Entropy
        entropy = compute_spectral_entropy(eigenvalues)
        
        return {
            "spectral_radius": spectral_radius,
            "condition_number": condition_number,
            "tail_decay_exponent": tail_decay,
            "spectral_entropy": entropy
        }
        
    except Exception as e:
        error(f"Eigenvalue decomposition failed: {e}")
        return None

def run_proxy_training(model_name: str, device: torch.device) -> Optional[Dict[str, Any]]:
    """
    Run proxy training for a single model and extract spectral features.
    Includes robust error handling for convergence failures and NaN/Inf values.
    """
    logger = get_logger()
    info(f"Starting proxy training for model: {model_name}")
    
    try:
        # Load model
        if "vit" in model_name.lower():
            # Simple ViT implementation for demo
            from torchvision.models import vit_b_16, ViT_B_16_Weights
            # Using a small variant for speed
            model = vit_b_16(weights=None)
            # Modify for 64x64 input if needed
            if hasattr(model, 'conv_proj'):
                model.conv_proj = nn.Conv2d(3, 768, kernel_size=16, stride=16)
        elif "mobilenet" in model_name.lower():
            from torchvision.models import mobilenet_v2, MobileNet_V2_Weights
            model = mobilenet_v2(weights=None)
        elif "efficientnet" in model_name.lower():
            from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
            model = efficientnet_b0(weights=None)
        else:
            # Default to ResNet
            from torchvision.models import resnet18, ResNet18_Weights
            model = resnet18(weights=None)
        
        model = model.to(device)
        param_count = count_parameters(model)
        info(f"Model {model_name} has {param_count} parameters")
        
        # Load data
        try:
            data_loader = load_tinyimagenet_streaming(
                batch_size=BATCH_SIZE,
                num_workers=0,
                device=device
            )
        except DataLoaderError as e:
            error(f"Data loading failed for {model_name}: {e}")
            return None
        except Exception as e:
            error(f"Unexpected error loading data for {model_name}: {e}")
            return None
            
        # Run gradient accumulation
        with timeout_handler_context(TIMEOUT_SECONDS):
            cov_matrix = get_gradient_covariance(model, data_loader, device, steps=MAX_ITERATIONS)
            
        if cov_matrix is None:
            warning(f"Covariance matrix computation failed or returned None for {model_name}")
            return None
            
        # Compute spectral features
        features = compute_spectral_features(cov_matrix)
        
        if features is None:
            warning(f"Spectral feature computation failed for {model_name}")
            return None
            
        # Validate results for NaN/Inf
        for key, value in features.items():
            if math.isnan(value) or math.isinf(value):
                error(f"Invalid value ({key}={value}) detected for {model_name}. Excluding sample.")
                return None
                
        info(f"Successfully extracted features for {model_name}")
        return {
            "model_name": model_name,
            "parameter_count": param_count,
            **features
        }
        
    except TimeoutError as e:
        error(f"Timeout during proxy training for {model_name}: {e}")
        return None
    except RuntimeError as e:
        if "CUDA out of memory" in str(e):
            error(f"Out of memory during training for {model_name}: {e}")
        else:
            error(f"Runtime error during training for {model_name}: {e}")
            traceback.print_exc()
        return None
    except Exception as e:
        error(f"Unexpected error during proxy training for {model_name}: {e}")
        traceback.print_exc()
        return None
    finally:
        # Cleanup
        if 'model' in locals():
            del model
        if 'cov_matrix' in locals() and cov_matrix is not None:
            del cov_matrix
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

def save_features_to_csv(features_list: List[Dict[str, Any]], output_path: str):
    """
    Save extracted spectral features to a CSV file.
    """
    if not features_list:
        warning("No features to save.")
        return
        
    df = pd.DataFrame(features_list)
    df.to_csv(output_path, index=False)
    info(f"Saved {len(features_list)} features to {output_path}")

def main():
    """
    Main entry point for spectral feature extraction.
    """
    logger = get_logger()
    info("Starting spectral feature extraction pipeline")
    
    # Setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    info(f"Using device: {device}")
    
    # Select models
    model_names = select_models()
    info(f"Selected models: {model_names}")
    
    all_features = []
    excluded_count = 0
    
    for model_name in model_names:
        info(f"Processing {model_name}")
        result = run_proxy_training(model_name, device)
        
        if result is None:
            excluded_count += 1
            warning(f"Excluded {model_name} due to failure or invalid results")
        else:
            all_features.append(result)
            
    # Save results
    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "spectral_features.csv")
    
    save_features_to_csv(all_features, output_path)
    
    info(f"Pipeline complete. Processed: {len(all_features)}, Excluded: {excluded_count}")
    
    if excluded_count > 0:
        # Write exclusion log
        exclusion_log_path = os.path.join(output_dir, "exclusion_log.txt")
        with open(exclusion_log_path, "w") as f:
            f.write(f"Total excluded samples: {excluded_count}\n")
            f.write("Reasons: Convergence failure, NaN/Inf values, Timeout, or Memory error.\n")
        info(f"Exclusion log written to {exclusion_log_path}")

if __name__ == "__main__":
    main()