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
        # Handle None case with default
        if max_size_gb is None:
            max_size_gb = 3.5
        self.max_size = max_size_gb * 1e9
        self.max_model_size_gb = max_size_gb
        self.cache_dir = cache_dir or os.path.expanduser("~/.cache/huggingface")
        self.hf_api = HfApi()
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Known good fallback models (ordered by size/capability)
        # Choose based on size requirements
        self.fallback_models = self._get_size_appropriate_fallbacks(self.max_model_size_gb)
        
    def _get_size_appropriate_fallbacks(self, max_size_gb: float) -> List[str]:
        """Get fallback models appropriate for the given size limit"""
        # All fallback models with their approximate sizes in GB (2025 trending models)
        all_fallbacks = [
            # Ultra Large models (> 50GB)
            ("Qwen/Qwen2.5-72B-Instruct", 72.0),  # Top performer, 72B params
            ("meta-llama/Llama-3.1-70B-Instruct", 70.0),  # Meta's flagship 70B
            ("microsoft/WizardLM-2-8x22B", 65.0),  # WizardLM mixture of experts
            
            # Large models (20-50GB)
            ("mistralai/Mixtral-8x7B-Instruct-v0.1", 47.0),  # Mixtral 8x7B, 46.7B total params
            ("meta-llama/Llama-3.2-90B-Vision-Instruct", 45.0),  # Multimodal 90B
            ("Qwen/Qwen2.5-32B-Instruct", 32.0),  # Qwen 32B
            ("microsoft/WizardLM-2-7B", 28.0),  # WizardLM 7B series
            
            # Medium models (7-20GB)
            ("Qwen/Qwen2.5-14B-Instruct", 14.0),  # Qwen 14B
            ("meta-llama/Llama-3.2-11B-Vision-Instruct", 11.0),  # Multimodal 11B
            ("meta-llama/Llama-3.1-8B-Instruct", 8.0),  # Meta's 8B instruct
            ("Qwen/Qwen2.5-7B-Instruct", 7.0),  # Qwen 7B
            ("microsoft/Phi-3-medium-4k-instruct", 7.0),  # Phi-3 medium
            
            # Small models (2-7GB)
            ("Qwen/Qwen2.5-3B-Instruct", 3.0),  # Qwen 3B
            ("meta-llama/Llama-3.2-3B-Instruct", 3.0),  # Meta's 3B
            ("microsoft/Phi-3-mini-4k-instruct", 2.2),  # Phi-3 mini
            ("Qwen/Qwen2.5-1.5B-Instruct", 1.5),  # Qwen 1.5B
            
            # Tiny models (< 2GB)
            ("meta-llama/Llama-3.2-1B-Instruct", 1.0),  # Meta's 1B
            ("TinyLlama/TinyLlama-1.1B-Chat-v1.0", 1.1),  # TinyLlama (reliable fallback)
            ("Qwen/Qwen2.5-0.5B-Instruct", 0.5),  # Qwen 0.5B
        ]
        
        # Filter models that fit within the size limit
        suitable_models = []
        for model_id, size_gb in all_fallbacks:
            if size_gb <= max_size_gb:
                suitable_models.append(model_id)
        
        # If no models fit (very restrictive limit), use the smallest available
        if not suitable_models:
            suitable_models = ["Qwen/Qwen1.5-0.5B-Chat"]
        
        return suitable_models
        
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
            # Common size patterns in model names (2025 updates)
            if '72b' in model_id:
                total_size = 72 * 1e9 * 2  # ~144GB for 72B model
            elif '70b' in model_id:
                total_size = 70 * 1e9 * 2  # ~140GB for 70B model
            elif '8x7b' in model_id or 'mixtral' in model_id:
                total_size = 47 * 1e9 * 2  # ~94GB for Mixtral 8x7B (46.7B params)
            elif '32b' in model_id:
                total_size = 32 * 1e9 * 2  # ~64GB for 32B model
            elif '14b' in model_id:
                total_size = 14 * 1e9 * 2  # ~28GB for 14B model
            elif '11b' in model_id:
                total_size = 11 * 1e9 * 2  # ~22GB for 11B model
            elif '8b' in model_id:
                total_size = 8 * 1e9 * 2  # ~16GB for 8B model
            elif '7b' in model_id:
                total_size = 7 * 1e9 * 2  # ~14GB for 7B model
            elif '3b' in model_id or '3.5b' in model_id:
                total_size = 3.5 * 1e9 * 2  # ~7GB for 3.5B model
            elif '2.5b' in model_id:
                total_size = 2.5 * 1e9 * 2  # ~5GB for 2.5B model
            elif '2b' in model_id:
                total_size = 2 * 1e9 * 2  # ~4GB for 2B model
            elif '1.5b' in model_id:
                total_size = 1.5 * 1e9 * 2  # ~3GB for 1.5B model
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
            # Fix transformers library bug: ALL_PARALLEL_STYLES is None in some versions
            import transformers.modeling_utils as modeling_utils
            if modeling_utils.ALL_PARALLEL_STYLES is None:
                logger.info("Fixing transformers library bug: setting ALL_PARALLEL_STYLES")
                modeling_utils.ALL_PARALLEL_STYLES = ['colwise', 'rowwise', 'auto']
            
            # Load tokenizer first
            tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )
            
            # Set pad token if not set
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Try different loading strategies to handle compatibility issues
            model = None
            loading_error = None
            
            # Monkey patch for TinyLlama tensor parallelism issue
            if "TinyLlama" in model_id:
                try:
                    # Load config first and fix the issue
                    from transformers import AutoConfig
                    config = AutoConfig.from_pretrained(model_id, cache_dir=self.cache_dir)
                    # Set tensor parallelism attributes to avoid the error
                    config.base_model_tp_plan = None
                    config.base_model_pp_plan = None
                except Exception as e:
                    logger.debug(f"Could not patch config: {e}")
            
            # Check if CUDA is available
            if torch.cuda.is_available():
                try:
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
                except Exception as e:
                    logger.warning(f"GPU loading failed: {e}")
                    loading_error = e
            
            # If GPU loading failed or not available, try CPU
            if model is None:
                logger.info("Loading model on CPU")
                
                # Try different configurations to handle compatibility issues
                loading_configs = []
                
                # If we have a patched config for TinyLlama, use it
                if "TinyLlama" in model_id and 'config' in locals():
                    loading_configs.extend([
                        # Config with patched config object
                        {
                            "config": config,
                            "torch_dtype": torch.float32,
                            "cache_dir": self.cache_dir,
                            "trust_remote_code": True,
                            "low_cpu_mem_usage": True
                        },
                        {
                            "config": config,
                            "torch_dtype": torch.float32,
                            "cache_dir": self.cache_dir
                        }
                    ])
                
                # Standard configs for all models
                loading_configs.extend([
                    # Config 1: Basic CPU loading without device_map
                    {
                        "torch_dtype": torch.float32,
                        "cache_dir": self.cache_dir,
                        "trust_remote_code": True,
                        "low_cpu_mem_usage": True
                    },
                    # Config 2: With explicit device map
                    {
                        "torch_dtype": torch.float32,
                        "device_map": "cpu",
                        "cache_dir": self.cache_dir,
                        "trust_remote_code": True,
                        "low_cpu_mem_usage": True
                    },
                    # Config 3: Minimal config
                    {
                        "torch_dtype": torch.float32,
                        "cache_dir": self.cache_dir
                    }
                ])
                
                for i, config in enumerate(loading_configs):
                    try:
                        logger.debug(f"Trying loading config {i+1}")
                        model = AutoModelForCausalLM.from_pretrained(model_id, **config)
                        logger.info(f"Successfully loaded with config {i+1}")
                        break
                    except Exception as e:
                        logger.debug(f"Config {i+1} failed: {e}")
                        loading_error = e
                        continue
            
            if model is None:
                raise RuntimeError(f"Failed to load {model_id} with any configuration. Last error: {loading_error}")
            
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