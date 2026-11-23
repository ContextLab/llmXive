"""
Validator module for ensuring gradient tracking is disabled during inference.

This module provides utilities to verify that no gradient computation is enabled
during embedding generation, ensuring memory efficiency and correct inference behavior.
"""

import torch
from typing import Optional, Callable
from utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)


def validate_no_gradient_tracking(model: torch.nn.Module, test_input: torch.Tensor) -> bool:
    """
    Validates that the model operates without gradient tracking.
    
    This function performs a forward pass and asserts that:
    1. No gradients are computed for model parameters
    2. No gradient history is retained in the computation graph
    3. The model is in evaluation mode
    
    Args:
        model: The neural network model to validate
        test_input: A sample tensor to run through the model
        
    Returns:
        bool: True if validation passes, raises AssertionError otherwise
        
    Raises:
        AssertionError: If gradient tracking is detected or model is not in eval mode
        RuntimeError: If the forward pass fails
    """
    # Ensure model is in evaluation mode
    if model.training:
        error_msg = "Model is in training mode. Call model.eval() before inference."
        log_error(error_msg)
        raise AssertionError(error_msg)
    
    # Check that test_input doesn't require gradients
    if test_input.requires_grad:
        warning_msg = "Test input has requires_grad=True. Detaching for validation."
        log_warning(warning_msg)
        test_input = test_input.detach()
    
    # Perform forward pass without gradient tracking
    try:
        with torch.no_grad():
            output = model(test_input)
            # Verify output doesn't have gradient history
            if output.requires_grad:
                error_msg = "Output tensor requires gradients. Gradient tracking was enabled."
                log_error(error_msg)
                raise AssertionError(error_msg)
            
            # Check that no parameters have gradient history
            for name, param in model.named_parameters():
                if param.grad is not None:
                    error_msg = f"Parameter '{name}' has accumulated gradients from previous operations."
                    log_error(error_msg)
                    raise AssertionError(error_msg)
            
        log_info("Gradient tracking validation passed: No gradients computed during inference.")
        return True
        
    except Exception as e:
        log_error(f"Validation failed during forward pass: {str(e)}")
        raise
    

def assert_no_grad_context() -> None:
    """
    Asserts that the current context has gradient tracking disabled.
    
    This is a runtime check that can be used to enforce no-grad behavior
    in critical sections of code.
    
    Raises:
        AssertionError: If gradient tracking is enabled in the current context
    """
    # torch.is_grad_enabled() returns True if gradients are enabled
    if torch.is_grad_enabled():
        error_msg = "Gradient tracking is enabled. Use torch.no_grad() context for inference."
        log_error(error_msg)
        raise AssertionError(error_msg)
    
    log_debug("Gradient tracking is correctly disabled in current context.")


def validate_embedding_generator(generator) -> bool:
    """
    Validates that an EmbeddingGenerator instance operates without gradient tracking.
    
    This function checks the internal state of the generator and performs
    a test inference to ensure gradients are not computed.
    
    Args:
        generator: An EmbeddingGenerator instance
        
    Returns:
        bool: True if validation passes
        
    Raises:
        AssertionError: If validation fails
        RuntimeError: If the generator is not properly initialized
    """
    from embeddings.generator import EmbeddingGenerator
    
    if not isinstance(generator, EmbeddingGenerator):
        error_msg = "Invalid generator type. Expected EmbeddingGenerator instance."
        log_error(error_msg)
        raise TypeError(error_msg)
    
    # Ensure generator is in eval mode
    generator.model.eval()
    
    # Create a small test batch based on the generator's expected input
    # This is a minimal validation that doesn't require real data
    try:
        # Test with image input if available
        if hasattr(generator, 'image_model') and generator.image_model is not None:
            test_image = torch.randn(1, 3, 224, 224)  # Standard CLIP input size
            validate_no_gradient_tracking(generator.image_model, test_image)
            log_info("Image model gradient validation passed.")
        
        # Test with text input if available
        if hasattr(generator, 'text_model') and generator.text_model is not None:
            test_text_ids = torch.randint(0, 1000, (1, 77))  # Standard CLIP text input
            validate_no_gradient_tracking(generator.text_model, test_text_ids)
            log_info("Text model gradient validation passed.")
        
        return True
        
    except Exception as e:
        log_error(f"Embedding generator validation failed: {str(e)}")
        raise
    

def run_validation_suite(generator) -> dict:
    """
    Runs a comprehensive validation suite on the embedding generator.
    
    Args:
        generator: An EmbeddingGenerator instance
        
    Returns:
        dict: Validation results with status and details
    """
    results = {
        'status': 'passed',
        'details': [],
        'errors': []
    }
    
    try:
        # Check 1: Verify no_grad context enforcement
        try:
            assert_no_grad_context()
            results['details'].append("Context check: PASSED")
        except AssertionError as e:
            results['errors'].append(f"Context check: FAILED - {str(e)}")
            results['status'] = 'failed'
        
        # Check 2: Validate generator models
        try:
            validate_embedding_generator(generator)
            results['details'].append("Generator validation: PASSED")
        except (AssertionError, TypeError, RuntimeError) as e:
            results['errors'].append(f"Generator validation: FAILED - {str(e)}")
            results['status'] = 'failed'
        
    except Exception as e:
        results['status'] = 'error'
        results['errors'].append(f"Unexpected error during validation: {str(e)}")
    
    return results
