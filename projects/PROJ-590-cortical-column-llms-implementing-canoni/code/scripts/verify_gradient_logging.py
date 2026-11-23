import os
import sys
import json
import logging
import torch
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.baseline_transformer import create_baseline_transformer
from src.training.homeostasis import log_gradient_norms

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Script to verify gradient logging functionality.
    Creates a model, runs a dummy forward/backward pass, and logs gradients.
    """
    logger.info("Starting gradient logging verification...")

    # 1. Create a simple model
    model = create_baseline_transformer(
        d_model=64,
        nhead=4,
        num_layers=2,
        dim_feedforward=128,
        dropout=0.1
    )
    model.train()
    logger.info(f"Model created with {sum(p.numel() for p in model.parameters())} parameters.")

    # 2. Create dummy input and target
    batch_size = 4
    seq_len = 16
    d_model = 64
    
    x = torch.randn(batch_size, seq_len, d_model)
    y = torch.randn(batch_size, seq_len, d_model)

    # 3. Forward pass
    output = model(x)
    loss = ((output - y) ** 2).mean()

    # 4. Backward pass
    loss.backward()

    # 5. Log gradient norms
    step = 1
    log_gradient_norms(model, step)

    # 6. Verify file creation and content
    log_path = "data/logs/gradient_norms.json"
    if os.path.exists(log_path):
        logger.info(f"SUCCESS: {log_path} created.")
        with open(log_path, 'r') as f:
            data = json.load(f)
        if len(data) > 0 and data[0]["step"] == step:
            logger.info("SUCCESS: Gradient norms logged correctly.")
            logger.info(f"Logged norms for {len(data[0]['norms'])} parameters.")
            return 0
        else:
            logger.error("ERROR: Log file exists but content is invalid.")
            return 1
    else:
        logger.error(f"ERROR: {log_path} was not created.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
