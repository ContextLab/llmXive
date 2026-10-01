"""
Write Model Configuration

Generates and writes the model configuration YAML file.
"""

import os
import sys
import json
import logging
import argparse
import yaml
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_seed, ensure_directories

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_model_config():
    """Generate model configuration dictionary."""
    # Try to load existing regression results to extract model type/status
    reg_path = "data/processed/regression_results.json"
    config_path = "artifacts/model_config.yaml"
    
    model_type = "GLMM"
    convergence_status = "success"
    fallback_status = "none"
    fallback_reason = ""
    seed = get_seed()
    
    if Path(reg_path).exists():
        with open(reg_path, 'r') as f:
            results = json.load(f)
            if 'model_type' in results:
                model_type = results['model_type']
            if 'convergence_status' in results:
                convergence_status = results['convergence_status']
            if 'fallback_status' in results:
                fallback_status = results['fallback_status']
            if 'fallback_reason' in results:
                fallback_reason = results['fallback_reason']
    
    config = {
        'seed': seed,
        'model_type': model_type,
        'convergence_status': convergence_status,
        'fdr_threshold': 0.05,
        'fallback_status': fallback_status,
        'fallback_reason': fallback_reason,
        'generated_at': datetime.now().isoformat()
    }
    
    return config

def main(args):
    """Main entry point."""
    ensure_directories()
    output_path = "artifacts/model_config.yaml"
    
    try:
        config = generate_model_config()
        
        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Model configuration saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error generating model config: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Write model configuration to YAML.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    main(args)
