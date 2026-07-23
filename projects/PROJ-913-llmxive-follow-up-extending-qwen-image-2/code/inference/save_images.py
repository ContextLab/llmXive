from pathlib import Path
from config import PROJECT_ROOT

def save_images(images, output_dir: Path, naming_prefix: str):
    """
    Saves generated images to disk.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    for i, img in enumerate(images):
        img.save(output_dir / f"{naming_prefix}_{i}.png")
