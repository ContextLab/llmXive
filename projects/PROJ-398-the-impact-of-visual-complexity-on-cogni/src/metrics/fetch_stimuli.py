"""
T014: Fetch Real Stimuli (Pilot)

Downloads the first 500 items from the 'train' split of the 
HuggingFace 'video-conference-backgrounds' dataset and saves them 
to the project's data/stimuli directory.
"""
import os
import sys
import shutil
from pathlib import Path

# Add project root to path to ensure imports work regardless of cwd
# This assumes the script is run from the project root or the code is structured accordingly.
# We use a robust approach to find the project root.
def get_project_root():
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "requirements.txt").exists():
            return current
        current = current.parent
    # Fallback if requirements.txt not found in hierarchy
    return Path(__file__).resolve().parent.parent.parent

PROJECT_ROOT = get_project_root()
DATA_DIR = PROJECT_ROOT / "data"
STIMULI_DIR = DATA_DIR / "stimuli"
PILOT_DIR = STIMULI_DIR / "pilot"

def ensure_directory(path: Path) -> None:
    """Create directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)

def fetch_stimuli(target_count: int = 500) -> int:
    """
    Fetches the first `target_count` items from the HuggingFace dataset.
    
    Args:
        target_count: Number of items to download.
        
    Returns:
        Number of successfully downloaded items.
    """
    try:
        from datasets import load_dataset
        from PIL import Image
        import io
    except ImportError as e:
        print(f"Error: Missing required dependency. Run: pip install datasets pillow")
        raise e

    print(f"Loading dataset 'HuggingFaceM4/video-conference-backgrounds' (split='train')...")
    try:
        dataset = load_dataset(
            'HuggingFaceM4/video-conference-backgrounds',
            split='train',
            trust_remote_code=True
        )
    except Exception as e:
        print(f"Error loading dataset: {e}")
        raise

    if len(dataset) < target_count:
        print(f"Warning: Dataset has only {len(dataset)} items. Downloading all available.")
        target_count = len(dataset)

    print(f"Downloading {target_count} items to {PILOT_DIR}...")
    ensure_directory(PILOT_DIR)

    downloaded_count = 0
    for i, item in enumerate(dataset):
        if i >= target_count:
            break
        
        # The dataset structure usually has an 'image' key or similar.
        # Based on common HuggingFace video/image datasets, we check for 'image' or 'background'.
        image_data = item.get('image')
        
        if image_data is None:
            print(f"Skipping item {i}: No image data found.")
            continue

        if isinstance(image_data, Image.Image):
            # It's already a PIL Image
            pil_img = image_data
        elif isinstance(image_data, dict) and 'bytes' in image_data:
            # Handle raw bytes if present
            pil_img = Image.open(io.BytesIO(image_data['bytes']))
        elif isinstance(image_data, dict) and 'path' in image_data:
            # If it's a path reference (rare in loaded datasets, but possible)
            pil_img = Image.open(image_data['path'])
        else:
            # Attempt to open as bytes if it's a bytes object directly
            if isinstance(image_data, bytes):
                pil_img = Image.open(io.BytesIO(image_data))
            else:
                print(f"Skipping item {i}: Unrecognized image format type {type(image_data)}")
                continue

        # Save the image
        filename = f"stimulus_{i:04d}.jpg"
        file_path = PILOT_DIR / filename
        
        try:
            # Ensure mode is compatible with JPEG
            if pil_img.mode in ("RGBA", "P"):
                pil_img = pil_img.convert("RGB")
            pil_img.save(file_path, "JPEG", quality=95)
            downloaded_count += 1
            if (downloaded_count % 50) == 0:
                print(f"Downloaded {downloaded_count} items...")
        except Exception as e:
            print(f"Error saving item {i}: {e}")
            continue

    print(f"Successfully downloaded {downloaded_count} stimuli to {PILOT_DIR}")
    return downloaded_count

def main():
    """Main entry point for the script."""
    print("--- Starting T014: Fetch Real Stimuli (Pilot) ---")
    try:
        count = fetch_stimuli(target_count=500)
        if count == 0:
            print("Error: No stimuli were downloaded.")
            sys.exit(1)
        print("--- T014 Completed Successfully ---")
    except Exception as e:
        print(f"Error during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
