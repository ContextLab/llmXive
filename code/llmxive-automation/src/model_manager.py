"""Model management for llmXive automation"""

import os
import random
import logging
from typing import Tuple, Optional, Dict, List
import torch
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    BitsAndBytesConfig,
    PreTrainedModel,
    PreTrainedTokenizer
)
from huggingface_hub import HfApi

logger = logging.getLogger(__name__)


class ModelManager:
    """Dynamically queries and loads trending instruct models from HuggingFace"""
    
    def __init__(self, max_size_gb: float = 3.5, cache_dir: str = None):
        """
        Initialize model manager
        
        Args:
            max_size_gb: Maximum model size in GB (default 3.5 for GitHub Actions)
            cache_dir: Directory for model cache (default: ~/.cache/huggingface)
        """
        self.max_size = max_size_gb * 1e9
        self.max_model_size_gb = max_size_gb
        self.cache_dir = cache_dir or os.path.expanduser("~/.cache/huggingface")
        self.hf_api = HfApi()
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Known good fallback models (ordered by size/capability)
        # For now, stick with TinyLlama which works reliably
        self.fallback_models = [
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0",  # Most stable and accessible
            "Qwen/Qwen1.5-0.5B-Chat",  # Very small alternative
        ]
        
    def get_suitable_model(self) -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
        """
        Query HuggingFace for current most popular small instruct models
        
        Returns:
            Tuple of (model, tokenizer)
        """
        logger.info("Searching for suitable models on HuggingFace...")
        
        try:
            # Query for trending instruct models
            models = self.hf_api.list_models(
                task="text-generation",
                library="transformers",
                tags=["instruct"],
                sort="downloads",
                direction=-1,
                limit=50
            )
            
            suitable_models = []
            
            for model in models:
                try:
                    # Get detailed model info
                    info = self.hf_api.model_info(model.modelId)
                    
                    # Estimate size
                    total_size = self._estimate_model_size(info)
                    
                    size_gb = total_size / 1e9
                    
                    if total_size > 0 and total_size < self.max_size and self._validate_model_capabilities(info):
                        logger.debug(f"Found suitable model: {model.modelId} (size: {size_gb:.2f}GB)")
                        suitable_models.append({
                            "id": model.modelId,
                            "size": total_size,
                            "size_gb": size_gb,
                            "downloads": getattr(info, 'downloads', 0),
                            "likes": getattr(info, 'likes', 0)
                        })
                    else:
                        if total_size >= self.max_size:
                            logger.debug(f"Model too large: {model.modelId} ({size_gb:.2f}GB > {self.max_model_size_gb}GB)")
                        
                except Exception as e:
                    logger.debug(f"Error checking model {model.modelId}: {e}")
                    continue
                    
            if suitable_models:
                # Sort by downloads and likes
                suitable_models.sort(
                    key=lambda x: (x['downloads'] * 0.7 + x['likes'] * 0.3),
                    reverse=True
                )
                
                # Select randomly from top 5
                top_models = suitable_models[:5]
                selected = random.choice(top_models)
                
                logger.info(f"Selected model: {selected['id']} (size: {selected['size']/1e9:.2f}GB)")
                return self._load_model(selected['id'])
                
        except Exception as e:
            logger.warning(f"Error querying HuggingFace: {e}")
            
        # Fallback to known good models
        logger.info("Using fallback model selection")
        return self._load_fallback_model()
        
    def _estimate_model_size(self, model_info) -> float:
        """Estimate model size from file information"""
        total_size = 0
        
        # Check siblings (files in the model repo)
        if hasattr(model_info, 'siblings'):
            for file in model_info.siblings:
                if hasattr(file, 'rfilename') and hasattr(file, 'size'):
                    filename = getattr(file, 'rfilename', '')
                    size = getattr(file, 'size', 0)
                    if filename.endswith(('.safetensors', '.bin', '.pt', '.pth')):
                        total_size += size
                        
        # If no size info, estimate from config
        if total_size == 0 and hasattr(model_info, 'config') and model_info.config:
            config = model_info.config
            
            # Try different parameter count fields
            param_fields = ['num_parameters', 'n_params', 'num_params']
            for field in param_fields:
                if field in config:
                    # Rough estimate: 2 bytes per parameter (fp16)
                    total_size = config[field] * 2
                    break
        
        # If still no size, check model card for common size patterns
        if total_size == 0:
            model_id = model_info.modelId.lower()
            # Common size patterns in model names
            if '7b' in model_id:
                total_size = 7 * 1e9 * 2  # ~14GB for 7B model
            elif '3b' in model_id or '3.5b' in model_id:
                total_size = 3.5 * 1e9 * 2  # ~7GB for 3.5B model
            elif '2b' in model_id:
                total_size = 2 * 1e9 * 2  # ~4GB for 2B model
            elif '1b' in model_id or '1.1b' in model_id:
                total_size = 1.1 * 1e9 * 2  # ~2.2GB for 1.1B model
            elif '0.5b' in model_id or '500m' in model_id:
                total_size = 0.5 * 1e9 * 2  # ~1GB for 0.5B model
                    
        return total_size
        
    def _validate_model_capabilities(self, model_info) -> bool:
        """Check if model has required capabilities"""
        model_id = model_info.modelId
        
        # Exclude GGUF/GGML models (not compatible with transformers)
        if any(x in model_id.lower() for x in ['gguf', 'ggml', 'gptq']):
            return False
            
        # Check tags
        tags = getattr(model_info, 'tags', [])
        
        required_indicators = [
            any(tag in tags for tag in ['instruct', 'chat', 'conversational', 'instruction-tuned']),
            'instruct' in model_id.lower() or 'chat' in model_id.lower(),
            getattr(model_info, 'pipeline_tag', '') == 'text-generation'
        ]
        
        return any(required_indicators)
        
    def _load_model(self, model_id: str) -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
        """Load model with 4-bit quantization for memory efficiency"""
        logger.info(f"Loading model: {model_id}")
        
        try:
            # Load tokenizer first
            tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )
            
            # Set pad token if not set
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Check if CUDA is available
            if torch.cuda.is_available():
                # Configure 4-bit quantization for GPU
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                
                # Load model with quantization
                model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    quantization_config=quantization_config,
                    device_map="auto",
                    cache_dir=self.cache_dir,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )
            else:
                # CPU-only loading
                logger.info("CUDA not available, loading model on CPU")
                model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    torch_dtype=torch.float32,
                    device_map="cpu",
                    cache_dir=self.cache_dir,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )
            
            logger.info(f"Successfully loaded {model_id}")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Failed to load {model_id}: {e}")
            raise
            
    def _load_fallback_model(self) -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
        """Load a known good fallback model"""
        for model_id in self.fallback_models:
            try:
                logger.info(f"Trying fallback model: {model_id}")
                return self._load_model(model_id)
            except Exception as e:
                logger.warning(f"Fallback {model_id} failed: {e}")
                continue
                
        raise RuntimeError("No suitable model could be loaded")
        
    def get_model_info(self, model_id: str) -> Dict:
        """Get information about a specific model"""
        try:
            info = self.hf_api.model_info(model_id)
            return {
                "id": model_id,
                "size": self._estimate_model_size(info),
                "tags": getattr(info, 'tags', []),
                "downloads": getattr(info, 'downloads', 0),
                "likes": getattr(info, 'likes', 0)
            }
        except Exception as e:
            logger.error(f"Error getting info for {model_id}: {e}")
            return None