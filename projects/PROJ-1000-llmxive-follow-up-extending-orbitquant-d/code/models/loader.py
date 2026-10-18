"""
Model loader for Diffusion Transformers (DiT) with GPU escape hatch.
Provides load_dit_model(name: str, device: str = "cpu") which loads a Stable Diffusion
pipeline (which contains the UNet used as the DiT) and logs the load event.
"""
import torch
from diffusers import StableDiffusionPipeline
from llmxive_toolkit import paths, get_logger
from datetime import datetime
import json

log = get_logger(__name__)

LOG_FILE = paths.data("processed", "logs", "model_load_log.json")

def _ensure_log_file():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.is_file():
        LOG_FILE.write_text("[]", encoding="utf-8")

def _append_log(entry: dict):
    _ensure_log_file()
    try:
        with LOG_FILE.open("r+", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                data = []
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
    except json.JSONDecodeError:
        # Corrupt log – overwrite
        with LOG_FILE.open("w", encoding="utf-8") as f:
            json.dump([entry], f, indent=2)

def load_dit_model(name: str, device: str = "cpu"):
    """
    Loads a Stable Diffusion pipeline (which contains the DiT UNet) and moves it to the
    requested device. If a CUDA device is available and ``device`` is ``cpu`` the
    function automatically switches to ``cuda``.

    Parameters
    ----------
    name: str
        The HuggingFace repo identifier of the model (e.g. ``stabilityai/stable-diffusion-2-1``).
    device: str, optional
        Desired device (``cpu`` or ``cuda``). ``cuda`` is used automatically when
        ``torch.cuda.is_available()`` and ``device`` is ``cpu``.

    Returns
    -------
    StableDiffusionPipeline
        The loaded diffusion pipeline ready for inference.
    """
    # GPU escape hatch
    if device == "cpu" and torch.cuda.is_available():
        device = "cuda"
        log.info("CUDA available – switching device to 'cuda'")

    log.info(f"Loading model {name} on device {device}")

    # Load the pipeline – this pulls both UNet and text encoder.
    pipeline = StableDiffusionPipeline.from_pretrained(
        name,
        torch_dtype=torch.float32,
        safety_checker=None,  # speed‑up / avoid extra downloads
    )
    pipeline = pipeline.to(device)

    # Log the load event
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model_name": name,
        "device": device,
    }
    _append_log(entry)

    return pipeline
