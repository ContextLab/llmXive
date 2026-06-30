"""
Inference engine with support for quantized KV-cache generation.
Implements CustomGenerateLoop for quantization-aware inference.
"""
import torch
import torch.nn as nn
from typing import Optional, Dict, Any, List, Callable
from transformers import PreTrainedModel, GenerationConfig, LogitsProcessorList, AutoModelForCausalLM, AutoTokenizer
from src.quantization.kvarn import KVarNQuantizer
from src.quantization.uniform import UniformQuantizer
from src.inference.hooks import KVCacheInterceptor
from src.inference.logging_hooks import create_mse_interceptor, MSELogger
from src.benchmarks.size_tracker import KVCacheSizeTracker, create_size_tracker

class CustomGenerateLoop:
    """
    Custom generation loop that supports quantized KV-cache management.
    
    This class wraps the transformers generation process to inject
    quantization logic into the KV-cache storage.
    """

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: AutoTokenizer,
        quantizer: Optional[Quantizer] = None,
        log_mse: bool = False,
        track_size: bool = True
    ):
        """
        Initialize the custom generate loop.
        
        Args:
            model: The transformer model to use
            tokenizer: The tokenizer for the model
            quantizer: Optional quantizer instance (KVarN or Uniform)
            log_mse: Whether to log mean squared error
            track_size: Whether to track KV-cache size reduction (FR-007)
        """
        self.model = model
        self.tokenizer = tokenizer
        self.quantizer = quantizer
        self.log_mse = log_mse
        self.track_size = track_size
        
        self.mse_logger: Optional[MSELogger] = None
        self.size_tracker: Optional[KVCacheSizeTracker] = None
        self.cache_interceptor: Optional[KVCacheInterceptor] = None

    def _setup_hooks(self, input_ids: torch.Tensor):
        """
        Setup necessary hooks for quantization and logging.
        
        Args:
            input_ids: Input tensor to determine batch size
        """
        # Setup size tracker if requested (FR-007)
        if self.track_size:
            self.size_tracker = create_size_tracker()
        
        # Setup MSE logger if requested
        if self.log_mse:
            self.mse_logger = MSELogger()
            self.mse_logger.start()
        
        # Setup KV cache interceptor for quantization
        if self.quantizer is not None:
            self.cache_interceptor = KVCacheInterceptor(
                quantizer=self.quantizer,
                size_tracker=self.size_tracker,
                mse_logger=self.mse_logger
            )
            self.cache_interceptor.register(self.model)

    def _cleanup_hooks(self):
        """Remove all registered hooks."""
        if self.cache_interceptor is not None:
            self.cache_interceptor.unregister()
            self.cache_interceptor = None
        
        if self.mse_logger is not None:
            self.mse_logger.finalize()
            self.mse_logger = None

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 100,
        temperature: float = 1.0,
        top_p: float = 0.9,
        do_sample: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text with optional quantization and tracking.
        
        Args:
            prompt: Input prompt string
            max_new_tokens: Maximum number of new tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            do_sample: Whether to use sampling
            **kwargs: Additional arguments for generation config
        
        Returns:
            Dict containing generated text and metadata
        """
        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt")
        input_ids = inputs["input_ids"]
        attention_mask = inputs["attention_mask"]
        
        # Setup hooks
        self._setup_hooks(input_ids)
        
        try:
            # Configure generation
            gen_config = GenerationConfig(
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                **kwargs
            )
            
            # Run generation
            with torch.no_grad():
                output_ids = self.model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    generation_config=gen_config,
                    logits_processor=LogitsProcessorList()
                )
            
            # Decode output
            generated_text = self.tokenizer.decode(
                output_ids[0][input_ids.shape[1]:],
                skip_special_tokens=True
            )
            
            # Collect results
            result = {
                "prompt": prompt,
                "generated_text": generated_text,
                "input_length": input_ids.shape[1],
                "output_length": output_ids.shape[1] - input_ids.shape[1],
                "quantizer_type": self.quantizer.__class__.__name__ if self.quantizer else "None"
            }
            
            # Add size reduction stats if tracked (FR-007)
            if self.size_tracker is not None:
                stats = self.size_tracker.get_stats()
                result["kv_cache_reduction_percentage"] = stats["reduction_percentage"]
                result["kv_cache_original_bytes"] = stats["total_original_bytes"]
                result["kv_cache_quantized_bytes"] = stats["total_quantized_bytes"]
            
            # Add MSE summary if logged
            if self.mse_logger is not None:
                result["mse_summary"] = self.mse_logger.get_summary()
            
            return result
            
        finally:
            # Always cleanup hooks
            self._cleanup_hooks()

def create_quantized_generator(
    model_name: str,
    quantizer_type: str = "uniform",
    log_mse: bool = False,
    track_size: bool = True
) -> CustomGenerateLoop:
    """
    Factory function to create a quantized generator.
    
    Args:
        model_name: Name of the model to load
        quantizer_type: Type of quantizer ("uniform" or "kvarn")
        log_mse: Whether to log MSE
        track_size: Whether to track size reduction (FR-007)
    
    Returns:
        CustomGenerateLoop instance
    """
    # Load model and tokenizer
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto" if torch.cuda.is_available() else None
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # Create quantizer
    quantizer = None
    if quantizer_type == "uniform":
        quantizer = UniformQuantizer(bits=8)
    elif quantizer_type == "kvarn":
        quantizer = KVarNQuantizer(bits=8)
    
    return CustomGenerateLoop(
        model=model,
        tokenizer=tokenizer,
        quantizer=quantizer,
        log_mse=log_mse,
        track_size=track_size
    )
