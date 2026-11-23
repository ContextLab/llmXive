import json
import csv
from pathlib import Path
from config import PROJECT_ROOT
from utils.logger import get_logger
from inference import load_model, generate_image
import os
import gc

logger = get_logger("generate_pilot")

def generate_pilot_images(base_model_id: str, rl_model_id: str):
    """
    Generates images for the pilot prompt sets.
    """
    prompts_path = PROJECT_ROOT / "data" / "prompts" / "pilot_in_distribution.csv"
    if not prompts_path.exists():
        logger.error("Pilot prompts not found. Run T015a first.")
        return

    with open(prompts_path, "r") as f:
        reader = csv.DictReader(f)
        prompts = [row for row in reader]

    logger.info(f"Loaded {len(prompts)} pilot prompts.")

    base_pipe = load_model(base_model_id)
    rl_pipe = load_model(rl_model_id)

    output_base = PROJECT_ROOT / "data" / "outputs" / "pilot_base"
    output_rl = PROJECT_ROOT / "data" / "outputs" / "pilot_rl_unified"
    output_base.mkdir(parents=True, exist_ok=True)
    output_rl.mkdir(parents=True, exist_ok=True)

    for i, row in enumerate(prompts):
        prompt_id = row.get("id", f"pilot_{i}")
        prompt_text = row.get("prompt", "")
        
        # Generate Base
        img_base = generate_image(base_pipe, prompt_text, seed=42)
        img_base.save(output_base / f"{prompt_id}_base.png")
        
        # Generate RL
        img_rl = generate_image(rl_pipe, prompt_text, seed=42)
        img_rl.save(output_rl / f"{prompt_id}_rl.png")
        
        gc.collect()
        logger.info(f"Processed {i+1}/{len(prompts)}")

    logger.info("Pilot generation complete.")

def main():
    generate_pilot_images("Qwen/Qwen-Image-2.0", "Qwen/Qwen-Image-2.0-RL")

if __name__ == "__main__":
    main()
