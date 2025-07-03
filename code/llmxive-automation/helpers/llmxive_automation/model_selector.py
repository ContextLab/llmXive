"""Model selection engine for choosing appropriate LLMs from HuggingFace"""

import os
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass
from huggingface_hub import HfApi, ModelInfo
import requests

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a selected model"""
    model_id: str
    model_size: int
    likes: int
    downloads: int
    pipeline_tag: str
    quantization: Optional[str] = None


class ModelSelector:
    """Dynamically selects appropriate small language models from HuggingFace"""
    
    def __init__(self, max_size_gb: float = 7.0, hf_token: Optional[str] = None):
        """
        Initialize model selector
        
        Args:
            max_size_gb: Maximum model size in GB (default 7GB for free tier)
            hf_token: Optional HuggingFace API token
        """
        self.hf_api = HfApi(token=hf_token or os.getenv("HF_TOKEN"))
        self.max_size_bytes = max_size_gb * 1e9
        self.required_tags = ["text-generation"]
        self.preferred_keywords = ["instruct", "chat", "assistant"]
        
        # Fallback models if dynamic selection fails
        self.fallback_models = [
            "microsoft/phi-2",
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            "EleutherAI/pythia-1.4b-deduped",
            "cerebras/Cerebras-GPT-1.3B",
        ]
    
    def get_trending_model(self) -> ModelConfig:
        """
        Get the most suitable trending model from HuggingFace
        
        Returns:
            ModelConfig for the selected model
        """
        try:
            models = self._fetch_candidate_models()
            
            for model in models:
                config = self._validate_and_configure_model(model)
                if config:
                    logger.info(f"Selected model: {config.model_id}")
                    return config
            
            logger.warning("No suitable trending models found, using fallback")
            return self._get_fallback_model()
            
        except Exception as e:
            logger.error(f"Error selecting model: {e}")
            return self._get_fallback_model()
    
    def _fetch_candidate_models(self) -> List[ModelInfo]:
        """Fetch candidate models from HuggingFace"""
        models = []
        
        # Search for instruct models
        for keyword in self.preferred_keywords:
            try:
                keyword_models = self.hf_api.list_models(
                    pipeline_tag="text-generation",
                    sort="likes7d",  # Trending in last 7 days
                    search=keyword,
                    limit=20
                )
                models.extend(keyword_models)
            except Exception as e:
                logger.warning(f"Error fetching models with keyword '{keyword}': {e}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_models = []
        for model in models:
            if model.modelId not in seen:
                seen.add(model.modelId)
                unique_models.append(model)
        
        return unique_models
    
    def _validate_and_configure_model(self, model: ModelInfo) -> Optional[ModelConfig]:
        """
        Validate a model and create configuration if suitable
        
        Args:
            model: HuggingFace model info
            
        Returns:
            ModelConfig if valid, None otherwise
        """
        try:
            # Check model size
            model_size = self._estimate_model_size(model)
            if model_size > self.max_size_bytes:
                logger.debug(f"Model {model.modelId} too large: {model_size/1e9:.1f}GB")
                return None
            
            # Check if model supports text generation
            if "text-generation" not in (model.pipeline_tag or ""):
                logger.debug(f"Model {model.modelId} doesn't support text generation")
                return None
            
            # Check for GGUF/quantized versions for better performance
            quantization = self._check_quantization_available(model)
            
            return ModelConfig(
                model_id=model.modelId,
                model_size=model_size,
                likes=model.likes or 0,
                downloads=model.downloads or 0,
                pipeline_tag=model.pipeline_tag,
                quantization=quantization
            )
            
        except Exception as e:
            logger.debug(f"Error validating model {model.modelId}: {e}")
            return None
    
    def _estimate_model_size(self, model: ModelInfo) -> int:
        """Estimate model size in bytes"""
        # Try to get size from model card
        if hasattr(model, 'safetensors') and model.safetensors:
            total_size = sum(file.size for file in model.safetensors.values())
            if total_size > 0:
                return total_size
        
        # Estimate from model name patterns
        model_id_lower = model.modelId.lower()
        
        size_patterns = {
            "70b": 70e9, "65b": 65e9, "40b": 40e9, "34b": 34e9,
            "30b": 30e9, "20b": 20e9, "13b": 13e9, "12b": 12e9,
            "7b": 7e9, "6b": 6e9, "3b": 3e9, "2b": 2e9,
            "1.3b": 1.3e9, "1.1b": 1.1e9, "1b": 1e9,
            "phi-2": 2.7e9,  # Known model sizes
            "tinyllama": 1.1e9,
            "pythia": 1.4e9,
        }
        
        for pattern, size in size_patterns.items():
            if pattern in model_id_lower:
                return int(size)
        
        # Default estimate
        return int(3e9)  # Assume 3B if unknown
    
    def _check_quantization_available(self, model: ModelInfo) -> Optional[str]:
        """Check if quantized versions are available"""
        # This is a simplified check - in production, would query model files
        model_id_lower = model.modelId.lower()
        
        if "gguf" in model_id_lower or "gptq" in model_id_lower:
            return "gguf" if "gguf" in model_id_lower else "gptq"
        
        return None
    
    def _get_fallback_model(self) -> ModelConfig:
        """Get a fallback model when dynamic selection fails"""
        for model_id in self.fallback_models:
            try:
                model = self.hf_api.model_info(model_id)
                config = self._validate_and_configure_model(model)
                if config:
                    logger.info(f"Using fallback model: {model_id}")
                    return config
            except Exception as e:
                logger.debug(f"Fallback model {model_id} failed: {e}")
                continue
        
        # Last resort - return first fallback
        return ModelConfig(
            model_id=self.fallback_models[0],
            model_size=int(2.7e9),
            likes=0,
            downloads=0,
            pipeline_tag="text-generation"
        )
    
    def get_model_requirements(self, config: ModelConfig) -> Dict[str, any]:
        """Get installation requirements for a model"""
        requirements = {
            "transformers": True,
            "torch": True,
            "accelerate": True,
        }
        
        if config.quantization == "gguf":
            requirements["llama-cpp-python"] = True
        elif config.quantization == "gptq":
            requirements["auto-gptq"] = True
            
        return requirements