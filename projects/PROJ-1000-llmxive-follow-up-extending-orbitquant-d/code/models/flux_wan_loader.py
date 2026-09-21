"""
Model Loader for FLUX.1-dev / Wan 2.1 (GPU) or Stable Diffusion 2.1 (CPU).

This module provides a unified interface to load the specified diffusion model
based on hardware availability (GPU vs CPU) and injects hooks for activation
capture during the text-to-image generation loop.

It integrates with `code/models/dit_wrapper.py` to wrap the DiT backbone
and capture intermediate activations.
"""

import os
import logging
import torch
from typing import Optional, Dict, Any, List, Callable, Tuple

from config import Config
from models.dit_wrapper import DiTWrapper, ActivationCapture, create_dit_wrapper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model identifiers
MODEL_FLUX_DEV = "black-forest-labs/FLUX.1-dev"
MODEL_WAN_21 = "Wan-AI/Wan2.1-T2V-1.3B" # Placeholder ID, actual might vary
MODEL_SD21 = "stabilityai/stable-diffusion-2-1"

class ModelLoader:
    """
    Handles loading of the target diffusion model with optional activation hooks.
    """

    def __init__(self, config: Config, force_cpu: bool = False):
        self.config = config
        self.force_cpu = force_cpu
        self.model = None
        self.dit_wrapper: Optional[DiTWrapper] = None
        self.hooks: List[Any] = []
        self.activation_buffer: Dict[str, List[torch.Tensor]] = {}

    def _detect_device(self) -> torch.device:
        """Detect available device: GPU (CUDA/MPS) or CPU."""
        if self.force_cpu:
            logger.info("Forcing CPU mode via configuration.")
            return torch.device("cpu")
        
        if torch.cuda.is_available():
            logger.info(f"CUDA available. Using device: cuda:{torch.cuda.current_device()}")
            return torch.device("cuda")
        
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.info("MPS (Metal) available. Using device: mps")
            return torch.device("mps")
        
        logger.warning("No GPU found. Falling back to CPU. This may be slow.")
        return torch.device("cpu")

    def _load_flux_wan(self, device: torch.device) -> torch.nn.Module:
        """
        Loads FLUX.1-dev or Wan 2.1.
        Note: FLUX.1-dev requires specific diffusers pipeline setup.
        For this implementation, we assume a standard Diffusers pipeline structure.
        """
        from diffusers import FluxPipeline, AutoencoderKL, FlowMatchEulerDiscreteScheduler
        from transformers import CLIPTextModel, CLIPTokenizer, T5EncoderModel, T5TokenizerFast
        import traceback

        logger.info(f"Attempting to load FLUX.1-dev/Wan model on {device}...")
        
        try:
            # Attempt to load FLUX.1-dev as the primary target
            # Note: FLUX.1-dev is a large model. We use torch_dtype to manage memory.
            torch_dtype = torch.float16 if device.type == "cuda" else torch.float32
            
            # We need the text encoders and VAE
            # Using a simplified loading strategy for demonstration; 
            # in production, handle specific model paths or HF token requirements.
            pipe = FluxPipeline.from_pretrained(
                MODEL_FLUX_DEV,
                torch_dtype=torch_dtype,
                device_map="auto" if device.type == "cuda" else None,
                use_safetensors=True,
                variant="fp16" if device.type == "cuda" else None
            )
            
            if device.type == "cpu":
                pipe = pipe.to(device)

            logger.info("FLUX.1-dev loaded successfully.")
            return pipe

        except Exception as e:
            logger.warning(f"Failed to load FLUX.1-dev: {e}. Falling back to SD2.1.")
            logger.debug(traceback.format_exc())
            return None

    def _load_sd21(self, device: torch.device) -> torch.nn.Module:
        """
        Loads Stable Diffusion 2.1.
        Fallback for CPU or if FLUX fails.
        """
        from diffusers import StableDiffusionPipeline, AutoencoderKL, UNet2DConditionModel
        from transformers import CLIPTextModel, CLIPTokenizer

        logger.info(f"Loading Stable Diffusion 2.1 on {device}...")

        try:
            pipe = StableDiffusionPipeline.from_pretrained(
                MODEL_SD21,
                torch_dtype=torch.float32 if device.type == "cpu" else torch.float16,
                safety_checker=None, # Disable for speed/research
                requires_safety_checker=False
            )
            
            pipe = pipe.to(device)
            logger.info("Stable Diffusion 2.1 loaded successfully.")
            return pipe

        except Exception as e:
            logger.error(f"Failed to load Stable Diffusion 2.1: {e}")
            raise e

    def _extract_dit_from_pipe(self, pipe: Any) -> torch.nn.Module:
        """
        Extracts the DiT backbone (transformer/unet) from the pipeline.
        For FLUX, this is the 'transformer'. For SD2.1, it is the 'unet'.
        """
        if hasattr(pipe, 'transformer'):
            return pipe.transformer
        elif hasattr(pipe, 'unet'):
            return pipe.unet
        else:
            raise AttributeError("Pipeline does not have a recognizable transformer or unet attribute.")

    def inject_hooks(self, layer_names: Optional[List[str]] = None) -> ActivationCapture:
        """
        Injects hooks into the DiT layers to capture activations.
        
        Args:
            layer_names: Optional list of layer names to hook. If None, hooks all
                         intermediate layers defined in dit_wrapper.
        
        Returns:
            ActivationCapture object that holds the buffers.
        """
        if self.dit_wrapper is None:
            raise RuntimeError("Model must be loaded before injecting hooks.")

        logger.info(f"Injecting hooks into DiT layers: {layer_names or 'default set'}")
        
        # Use the DiTWrapper to handle hook injection
        self.dit_wrapper.set_activation_buffer(self.activation_buffer)
        
        # The DiTWrapper handles the registration of forward hooks
        # based on the internal logic of create_dit_wrapper or manual registration
        self.dit_wrapper.register_hooks(layer_names)
        
        return self.dit_wrapper

    def load_model(self) -> Tuple[Any, DiTWrapper]:
        """
        Main entry point to load the model and prepare it for generation.
        Returns the pipeline and the DiT wrapper.
        """
        device = self._detect_device()
        pipe = None

        # Strategy: Try FLUX first if GPU, otherwise SD2.1
        if device.type != "cpu":
            pipe = self._load_flux_wan(device)
        
        if pipe is None:
            pipe = self._load_sd21(device)

        self.model = pipe
        
        # Extract the DiT backbone
        dit_backbone = self._extract_dit_from_pipe(pipe)
        
        # Wrap with DiTWrapper to manage hooks
        self.dit_wrapper = create_dit_wrapper(dit_backbone, self.config)
        
        logger.info("Model loading and wrapping complete.")
        return self.model, self.dit_wrapper

    def clear_buffers(self):
        """Clears the activation buffers before a new generation run."""
        self.activation_buffer.clear()
        logger.debug("Activation buffers cleared.")

    def get_activations(self) -> Dict[str, List[torch.Tensor]]:
        """Returns the captured activations."""
        return self.activation_buffer

def main():
    """
    Standalone runner to test model loading and hook injection.
    """
    config = Config()
    loader = ModelLoader(config, force_cpu=config.default_device == "cpu")
    
    try:
        pipe, dit_wrapper = loader.load_model()
        
        # Simulate hook injection
        capture = loader.inject_hooks()
        print(f"Model loaded: {type(pipe).__name__}")
        print(f"DiT Wrapper layers: {list(dit_wrapper.layer_hooks.keys())}")
        print("Hooks injected successfully. Ready for generation loop.")
        
    except Exception as e:
        logger.critical(f"Model loading failed: {e}")
        raise

if __name__ == "__main__":
    main()