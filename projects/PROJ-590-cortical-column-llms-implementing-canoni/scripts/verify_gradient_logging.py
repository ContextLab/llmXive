"""
Script to verify that gradient logging is working correctly.

This script runs a minimal training loop and checks that:
1. The gradient log file is created at data/logs/gradient_norms.json
2. The file contains valid JSON
3. The JSON structure matches the expected format

This is a standalone verification script that can be run independently
to ensure the gradient logging infrastructure is working.
"""
import os
import sys
import json
import logging
import torch
import torch.nn as nn
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models.baseline_transformer import create_baseline_transformer
from src.training.homeostasis import log_gradient_norms

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Main function to verify gradient logging.
    """
    # Ensure directories exist
    data_dir = project_root / "data"
    logs_dir = data_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    gradient_log_path = logs_dir / "gradient_norms.json"
    
    logger.info(f"Gradient log path: {gradient_log_path}")
    
    # Create a simple model
    logger.info("Creating baseline transformer model...")
    model = create_baseline_transformer(
        d_model=8,
        nhead=2,
        num_layers=2,
        dim_feedforward=16,
        dropout=0.1,
        input_dim=4,
        output_dim=1
    )
    
    # Create dummy data
    logger.info("Creating dummy data...")
    x = torch.randn(4, 4)
    y = torch.randn(4, 1)
    
    # Forward pass
    logger.info("Running forward pass...")
    output = model(x)
    loss = ((output - y) ** 2).mean()
    
    # Backward pass
    logger.info("Running backward pass...")
    loss.backward()
    
    # Log gradients
    logger.info("Logging gradient norms...")
    log_gradient_norms(model, step=1)
    
    # Verify the log file
    logger.info("Verifying gradient log file...")
    if not gradient_log_path.exists():
        logger.error(f"❌ Gradient log file not created at {gradient_log_path}")
        return 1
    
    try:
        with open(gradient_log_path, 'r') as f:
            log_data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"❌ Gradient log file contains invalid JSON: {e}")
        return 1
    
    if not isinstance(log_data, list):
        logger.error(f"❌ Gradient log should be a list, got {type(log_data)}")
        return 1
    
    if len(log_data) == 0:
        logger.error("❌ Gradient log is empty")
        return 1
    
    # Verify structure
    entry = log_data[-1]
    if "step" not in entry:
        logger.error("❌ Gradient log entry missing 'step' field")
        return 1
    
    if "norms" not in entry:
        logger.error("❌ Gradient log entry missing 'norms' field")
        return 1
    
    if not isinstance(entry["norms"], dict):
        logger.error("❌ Gradient log 'norms' field should be a dictionary")
        return 1
    
    if len(entry["norms"]) == 0:
        logger.error("❌ No gradient norms recorded")
        return 1
    
    # Check that norms are numeric and non-negative
    for param_name, norm_value in entry["norms"].items():
        if not isinstance(norm_value, (int, float)):
            logger.error(f"❌ Norm for {param_name} is not numeric: {type(norm_value)}")
            return 1
        if norm_value < 0:
            logger.error(f"❌ Norm for {param_name} is negative: {norm_value}")
            return 1
    
    logger.info("✅ Gradient logging verification successful!")
    logger.info(f"   - File created: {gradient_log_path}")
    logger.info(f"   - Entries logged: {len(log_data)}")
    logger.info(f"   - Parameters tracked: {len(entry['norms'])}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())