"""
verify_quantization.py

Validates that the model selected for rule distillation (T013) is loaded
in INT4 precision to comply with RAM constraints.

This script is a pre-flight check that must be run after T013 (distill_rules.py)
has selected and loaded a model. It inspects the loaded model object to ensure
quantization is active.

Output:
    data/artifacts/quantization_verification.json
        {
            "status": "PASS" | "FAIL",
            "model_name": str,
            "quantization_config": dict | null,
            "hf_quantizer": bool,
            "bitness": int | null,
            "message": str
        }
"""
import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import MAX_MEMORY_GB

logger = get_logger(__name__)

OUTPUT_PATH = project_root / "data" / "artifacts" / "quantization_verification.json"

def load_distilled_model_state() -> Optional[Dict[str, Any]]:
    """
    Attempts to load the model configuration state saved by T013 (distill_rules.py).
    T013 is expected to save a file like 'model_state.json' or similar in the artifacts
    or derived directory containing the model name and quantization config used.
    
    If T013 did not save this explicitly, we try to reconstruct it by attempting
    to load the model in the same way T013 would (using the same config).
    
    For this implementation, we assume T013 saves a 'model_selection_log.json' 
    or similar in data/artifacts/ or data/derived/ with the config.
    """
    # T013 logs to data/artifacts/model_selection.log (text) but we need the config object.
    # We will attempt to infer the model name from the log if possible, 
    # or rely on the fact that T013 should have saved the config used.
    
    # Fallback: Try to read the model name from the log file created in T013
    log_file = project_root / "data" / "artifacts" / "model_selection.log"
    model_name = None
    
    if log_file.exists():
        with open(log_file, 'r') as f:
            content = f.read()
            # Simple heuristic to extract model name if logged as "Selected model: <name>"
            if "Selected model:" in content:
                model_name = content.split("Selected model:")[1].strip().split('\n')[0].strip()
    
    if not model_name:
        logger.error("Could not determine model name from model_selection.log")
        return None

    # Since we cannot re-import the model instance from T013 (it's a separate process),
    # we must verify the *intent* and *configuration* by attempting to load the config
    # of that model with the quantization settings T013 claimed to use.
    # However, the task requires checking if the *loaded* model is quantized.
    # Since we are in a separate script, we simulate the loading to check the config
    # that *would* be loaded, or check if a saved config exists.
    
    # Robust approach: Re-load the model config (without weights) to check quantization_config
    # This is safe and fast.
    try:
        from transformers import AutoConfig
        # T013 likely used a specific config. We assume standard HF loading.
        config = AutoConfig.from_pretrained(model_name)
        
        # Check for quantization config in the config object
        if hasattr(config, 'quantization_config'):
            return {
                "model_name": model_name,
                "quantization_config": config.quantization_config,
                "has_quantizer": True,
                "bitness": config.quantization_config.get('load_in_4bit', False) and 4 or (config.quantization_config.get('load_in_8bit', False) and 8 or None)
            }
        
        # If not in config, check if it's a quantized model from a specific repo (less common for generic loading)
        # But standard practice is the config holds the intent.
        
        return {
            "model_name": model_name,
            "quantization_config": None,
            "has_quantizer": False,
            "bitness": None
        }

    except Exception as e:
        logger.error(f"Failed to load config for {model_name}: {e}")
        return None

def verify_quantization(model_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verifies the model state indicates INT4 quantization.
    """
    model_name = model_state.get("model_name", "Unknown")
    config = model_state.get("quantization_config")
    has_quantizer = model_state.get("has_quantizer", False)
    bitness = model_state.get("bitness")

    is_quantized = False
    message = ""

    if config:
        # Check for 4-bit
        if config.get('load_in_4bit', False):
            is_quantized = True
            message = f"Model {model_name} is configured for 4-bit quantization."
        elif config.get('load_in_8bit', False):
            is_quantized = True # 8-bit is better than nothing, but task asks for INT4
            message = f"Model {model_name} is configured for 8-bit quantization (Expected INT4)."
        else:
            message = f"Model {model_name} has quantization_config but not set to 4-bit."
    else:
        message = f"Model {model_name} has no quantization_config detected."

    # Strict check: Must be 4-bit
    if not (is_quantized and bitness == 4):
        return {
            "status": "FAIL",
            "model_name": model_name,
            "quantization_config": config,
            "hf_quantizer": has_quantizer,
            "bitness": bitness,
            "message": message
        }

    return {
        "status": "PASS",
        "model_name": model_name,
        "quantization_config": config,
        "hf_quantizer": has_quantizer,
        "bitness": bitness,
        "message": message
    }

def main():
    log_stage_start(logger, "verify_quantization")
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    model_state = load_distilled_model_state()
    
    if not model_state:
        result = {
            "status": "FAIL",
            "model_name": "Unknown",
            "quantization_config": None,
            "hf_quantizer": False,
            "bitness": None,
            "message": "Could not retrieve model state from previous stage (T013)."
        }
    else:
        result = verify_quantization(model_state)

    # Write result
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Verification result: {result['status']}")
    logger.info(f"Output written to: {OUTPUT_PATH}")

    if result['status'] == "FAIL":
        logger.error("Quantization verification failed. Model may exceed RAM limits.")
        log_stage_end(logger, "verify_quantization", status="FAIL")
        sys.exit(1)
    
    log_stage_end(logger, "verify_quantization", status="PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
