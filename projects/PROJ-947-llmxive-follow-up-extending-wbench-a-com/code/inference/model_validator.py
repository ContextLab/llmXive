"""
Model Validator for Inference Pipeline.

Ensures at least 3 valid CPU-optimized models are loaded and available
before proceeding with inference tasks. Raises ResourceLimitError if
fewer than 3 valid models are found.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from inference.models import (
    get_registered_models,
    validate_model_safety,
    ModelSpec
)
from utils.errors import ResourceLimitError, fail_loudly
from utils.logging import get_logger, log_info, log_error

logger = get_logger(__name__)

REQUIRED_VALID_MODEL_COUNT = 3

def validate_models_for_inference() -> List[ModelSpec]:
    """
    Validates that at least 3 CPU-compatible models are registered and safe.
    
    Returns:
        List[ModelSpec]: List of valid, registered models ready for inference.
        
    Raises:
        ResourceLimitError: If fewer than REQUIRED_VALID_MODEL_COUNT valid models are found.
    """
    logger.info("Starting model validation for inference pipeline...")
    
    # Load registered models
    models = get_registered_models()
    
    if not models:
        log_error("No models registered in the system.")
        raise ResourceLimitError(
            f"No models registered. Cannot proceed with inference. "
            f"Required minimum: {REQUIRED_VALID_MODEL_COUNT}"
        )
    
    log_info(f"Found {len(models)} registered models to validate.")
    
    valid_models: List[ModelSpec] = []
    
    for model_name, model_spec in models.items():
        try:
            # Validate model safety and CPU compatibility
            is_valid, reason = validate_model_safety(model_spec)
            
            if is_valid:
                valid_models.append(model_spec)
                log_info(f"Model '{model_name}' is valid and CPU-compatible.")
            else:
                log_error(f"Model '{model_name}' failed validation: {reason}")
                
        except Exception as e:
            log_error(f"Error validating model '{model_name}': {e}")
            # Continue to next model rather than failing the whole pipeline
            continue
    
    log_info(f"Validation complete. Found {len(valid_models)} valid models.")
    
    if len(valid_models) < REQUIRED_VALID_MODEL_COUNT:
        error_msg = (
            f"Insufficient valid models for inference. "
            f"Found {len(valid_models)}, but required at least {REQUIRED_VALID_MODEL_COUNT}. "
            f"Valid models: {[m.model_id for m in valid_models] if valid_models else 'None'}"
        )
        log_error(error_msg)
        fail_loudly(error_msg)
        raise ResourceLimitError(error_msg)
    
    return valid_models

def main():
    """
    Entry point for model validation script.
    Validates models and exits with appropriate status code.
    """
    try:
        valid_models = validate_models_for_inference()
        log_info(f"SUCCESS: {len(valid_models)} valid models available for inference.")
        for model in valid_models:
            log_info(f"  - {model.model_id}: {model.name}")
        return 0
    except ResourceLimitError as e:
        log_error(f"VALIDATION FAILED: {e}")
        return 1
    except Exception as e:
        log_error(f"UNEXPECTED ERROR during validation: {e}")
        import traceback
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    sys.exit(main())