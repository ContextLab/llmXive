"""
Model selection with conditional fallback logic.

Implements conditional model selection fallback:
- Unavailable: model load failure OR size > 1GB
- Trigger: config flag in settings.py (USE_FALLBACK_MODEL)
- Fallback: StarCoder for both languages with warning logged
"""

import os
import sys
import logging
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

# Import existing model interfaces
from models.jacotext_cpu import get_model_size_mb as jacotext_get_size, load_model as jacotext_load, run_inference as jacotext_inference
from models.starcoder_cpu import get_model_size_mb as starcoder_get_size, load_model as starcoder_load, run_inference as starcoder_inference
from config.settings import get_config

logger = logging.getLogger(__name__)

# Constants
MAX_MODEL_SIZE_MB = 1024  # 1GB threshold

class ModelSelectionError(Exception):
    """Custom exception for model selection failures."""
    pass

class ModelSelector:
    """
    Handles conditional model selection with fallback logic.
    
    Fallback trigger: USE_FALLBACK_MODEL config flag
    Fallback behavior: Use StarCoder for both Java and Python if primary model fails
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self._jacotext_model = None
        self._starcoder_model = None
        self._use_fallback = self.config.get('models', {}).get('USE_FALLBACK_MODEL', False)
        self._model_cache: Dict[str, Any] = {}
        
        logger.info(f"ModelSelector initialized with USE_FALLBACK_MODEL={self._use_fallback}")

    def _check_model_size(self, model_name: str, get_size_func) -> Tuple[bool, float]:
        """
        Check if model size is within acceptable limits.
        
        Returns:
            Tuple of (is_valid, size_mb)
        """
        try:
            size_mb = get_size_func()
            is_valid = size_mb <= MAX_MODEL_SIZE_MB
            logger.info(f"Model {model_name} size: {size_mb:.2f} MB (valid: {is_valid})")
            return is_valid, size_mb
        except Exception as e:
            logger.warning(f"Failed to check size for {model_name}: {e}")
            return False, 0.0

    def _load_model(self, model_name: str, load_func) -> Any:
        """
        Attempt to load a model with error handling.
        
        Returns:
            Loaded model or None if failed
        """
        try:
            logger.info(f"Attempting to load model: {model_name}")
            model = load_func()
            logger.info(f"Successfully loaded model: {model_name}")
            return model
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            return None

    def _get_model(self, model_name: str, load_func, get_size_func) -> Optional[Any]:
        """
        Get a model instance with size and load checks.
        
        Returns:
            Model instance or None if unavailable
        """
        # Check cache first
        if model_name in self._model_cache:
            return self._model_cache[model_name]

        # Check size
        is_valid_size, size_mb = self._check_model_size(model_name, get_size_func)
        if not is_valid_size:
            logger.warning(f"Model {model_name} exceeds size limit ({size_mb:.2f} MB > {MAX_MODEL_SIZE_MB} MB)")
            return None

        # Load model
        model = self._load_model(model_name, load_func)
        if model is not None:
            self._model_cache[model_name] = model

        return model

    def get_available_model(self, language: str) -> Tuple[Optional[str], bool]:
        """
        Determine which model to use based on language and availability.
        
        Args:
            language: 'java' or 'python'
            
        Returns:
            Tuple of (model_name, is_fallback)
        """
        if language.lower() == 'java':
            primary_name = 'jacotext'
            primary_load = jacotext_load
            primary_size = jacotext_get_size
        elif language.lower() == 'python':
            primary_name = 'starcoder'
            primary_load = starcoder_load
            primary_size = starcoder_get_size
        else:
            raise ModelSelectionError(f"Unsupported language: {language}")

        # Check primary model availability
        primary_model = self._get_model(primary_name, primary_load, primary_size)
        
        if primary_model is not None:
            logger.info(f"Using primary model: {primary_name} for {language}")
            return primary_name, False

        # Primary model unavailable
        if self._use_fallback:
            logger.warning(f"Primary model {primary_name} unavailable, triggering fallback to StarCoder")
            return 'starcoder', True
        else:
            logger.error(f"No fallback configured and primary model {primary_name} unavailable")
            return None, False

    def run_inference(self, language: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Run inference with automatic model selection and fallback.
        
        Args:
            language: 'java' or 'python'
            prompt: Input prompt for code generation
            **kwargs: Additional arguments for inference
            
        Returns:
            Inference result dictionary
        """
        model_name, is_fallback = self.get_available_model(language)
        
        if model_name is None:
            raise ModelSelectionError(f"No available model for language {language}")

        if is_fallback:
            logger.warning(f"Running inference with fallback model: {model_name}")

        # Select appropriate inference function
        if model_name == 'jacotext':
            inference_func = jacotext_inference
        elif model_name == 'starcoder':
            inference_func = starcoder_inference
        else:
            raise ModelSelectionError(f"Unknown model: {model_name}")

        try:
            result = inference_func(prompt, **kwargs)
            result['model_used'] = model_name
            result['is_fallback'] = is_fallback
            return result
        except Exception as e:
            logger.error(f"Inference failed with model {model_name}: {e}")
            if is_fallback:
                raise ModelSelectionError(f"Fallback model {model_name} also failed: {e}")
            else:
                # Try fallback if primary failed during inference
                if self._use_fallback:
                    logger.info("Attempting fallback model due to inference failure")
                    return self.run_inference(language, prompt, **kwargs)
                raise

    def get_model_status(self) -> Dict[str, Any]:
        """
        Get status of all registered models.
        
        Returns:
            Dictionary with model availability and size information
        """
        status = {
            'jacotext': {
                'available': False,
                'size_mb': 0.0,
                'loaded': False
            },
            'starcoder': {
                'available': False,
                'size_mb': 0.0,
                'loaded': False
            },
            'fallback_enabled': self._use_fallback
        }

        # Check JaCoText
        try:
            size_mb = jacotext_get_size()
            status['jacotext']['size_mb'] = size_mb
            status['jacotext']['available'] = size_mb <= MAX_MODEL_SIZE_MB
            status['jacotext']['loaded'] = self._jacotext_model is not None
        except Exception as e:
            logger.warning(f"JaCoText status check failed: {e}")

        # Check StarCoder
        try:
            size_mb = starcoder_get_size()
            status['starcoder']['size_mb'] = size_mb
            status['starcoder']['available'] = size_mb <= MAX_MODEL_SIZE_MB
            status['starcoder']['loaded'] = self._starcoder_model is not None
        except Exception as e:
            logger.warning(f"StarCoder status check failed: {e}")

        return status


def create_selector(use_fallback: bool = None) -> ModelSelector:
    """
    Factory function to create a ModelSelector instance.
    
    Args:
        use_fallback: Override config setting for fallback behavior
        
    Returns:
        Configured ModelSelector instance
    """
    config = get_config()
    if use_fallback is not None:
        if 'models' not in config:
            config['models'] = {}
        config['models']['USE_FALLBACK_MODEL'] = use_fallback
    
    return ModelSelector(config)


def main():
    """Main entry point for testing model selector."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Create selector with fallback enabled
        selector = create_selector(use_fallback=True)
        
        # Get status
        status = selector.get_model_status()
        print("Model Status:")
        for model, info in status.items():
            print(f"  {model}: {info}")

        # Test Java inference (should use fallback if JaCoText unavailable)
        print("\nTesting Java code generation...")
        try:
            java_prompt = "public class HelloWorld { public static void main(String[] args) { System.out.println(\"Hello\"); } }"
            result = selector.run_inference('java', java_prompt)
            print(f"Java result model: {result.get('model_used')}, fallback: {result.get('is_fallback')}")
        except ModelSelectionError as e:
            print(f"Java inference failed: {e}")

        # Test Python inference
        print("\nTesting Python code generation...")
        try:
            python_prompt = "def hello(): print('Hello')"
            result = selector.run_inference('python', python_prompt)
            print(f"Python result model: {result.get('model_used')}, fallback: {result.get('is_fallback')}")
        except ModelSelectionError as e:
            print(f"Python inference failed: {e}")

    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()