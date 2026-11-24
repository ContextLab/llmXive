"""
Model Loader for FLUX.1-dev / Wan 2.1 (GPU) or Stable Diffusion 2.1 (CPU).
"""

import os
import logging
import torch
import json
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

from config import Config
from models.dit_wrapper import DiTWrapper, create_dit_wrapper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_FLUX_DEV = "black-forest-labs/FLUX.1-dev"
MODEL_WAN_21 = "Wan-AI/Wan2.1-T2V-1.3B"
MODEL_SD21 = "stabilityai/stable-diffusion-2-1"

class ModelLoader:
    def __init__(self, config: Config, force_cpu: bool = False):
        self.config = config
        self.force_cpu = force_cpu
        self.model = None
        self.dit_wrapper: Optional[DiTWrapper] = None
        self.activation_buffer: Dict[str, List[torch.Tensor]] = {}

    def _detect_device(self) -> torch.device:
        if self.force_cpu:
            return torch.device("cpu")
        if torch.cuda.is_available():
            return torch.device("cuda")
        return torch.device("cpu")

    def _load_flux_wan(self, device: torch.device) -> torch.nn.Module:
        from diffusers import FluxPipeline
        try:
            torch_dtype = torch.float16 if device.type == "cuda" else torch.float32
            pipe = FluxPipeline.from_pretrained(
                MODEL_FLUX_DEV,
                torch_dtype=torch_dtype,
                device_map="auto" if device.type == "cuda" else None
            )
            return pipe.to(device)
        except Exception as e:
            logger.warning(f"Failed to load FLUX: {e}")
            return None

    def _load_sd21(self, device: torch.device) -> torch.nn.Module:
        from diffusers import StableDiffusionPipeline
        pipe = StableDiffusionPipeline.from_pretrained(
            MODEL_SD21,
            torch_dtype=torch.float32 if device.type == "cpu" else torch.float16,
            safety_checker=None,
            requires_safety_checker=False
        )
        return pipe.to(device)

    def _extract_dit_from_pipe(self, pipe: Any) -> torch.nn.Module:
        if hasattr(pipe, 'transformer'):
            return pipe.transformer
        elif hasattr(pipe, 'unet'):
            return pipe.unet
        raise AttributeError("Pipeline does not have a recognizable transformer or unet.")

    def load_model(self) -> Tuple[Any, DiTWrapper]:
        device = self._detect_device()
        pipe = None
        if device.type != "cpu":
            pipe = self._load_flux_wan(device)
        if pipe is None:
            pipe = self._load_sd21(device)

        self.model = pipe
        dit_backbone = self._extract_dit_from_pipe(pipe)
        self.dit_wrapper = create_dit_wrapper(dit_backbone, self.config)
        return self.model, self.dit_wrapper

def load_dit_model(name: str, device: str = "cpu") -> Tuple[Any, DiTWrapper]:
    """
    Loads the specified DiT model and logs the event.
    """
    from config import Config
    cfg = Config()
    loader = ModelLoader(cfg, force_cpu=(device == "cpu"))
    
    # Log the load attempt
    log_path = Path("data/model_load_log.json")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        pipe, wrapper = loader.load_model()
        status = "success"
        msg = f"Loaded {name} on {device}"
    except Exception as e:
        status = "failed"
        msg = str(e)
        raise e

    log_entry = {"model": name, "device": device, "status": status, "message": msg}
    with open(log_path, "w") as f:
        json.dump(log_entry, f, indent=2)
        
    return pipe, wrapper

def main():
    try:
        pipe, wrapper = load_dit_model("SD2.1", device="cpu")
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Load failed: {e}")

if __name__ == "__main__":
    main()
