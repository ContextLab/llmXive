import torch
from diffusers import DiffusionPipeline
from config import PROJECT_ROOT
from utils.logger import get_logger
from utils.seeding import set_global_seed

logger = get_logger("inference")

def load_model(model_id: str, device: str = "cpu"):
    """
    Loads a diffusion model with CPU offloading if needed.
    """
    logger.info(f"Loading model: {model_id} on {device}")
    set_global_seed()
    
    try:
        pipe = DiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            device_map="auto" if device == "cuda" else None
        )
        if device == "cpu":
            # Force CPU if requested, though diffusers handles offloading
            pipe.to("cpu")
        return pipe
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_image(pipe, prompt: str, seed: int = 42):
    """
    Generates a single image.
    """
    generator = torch.Generator(device="cpu").manual_seed(seed)
    image = pipe(prompt, generator=generator, num_inference_steps=20).images[0]
    return image

def main():
    # Example usage
    pass

if __name__ == "__main__":
    main()
