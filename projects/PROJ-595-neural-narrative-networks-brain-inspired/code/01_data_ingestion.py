import os
import sys
from pathlib import Path
from typing import Optional
from config import get_config
from utils.logging_config import get_logger, info, error, warning

try:
    from datasets import load_dataset
except ImportError:
    error("HuggingFace datasets library not found. Please install it via pip install datasets.")
    sys.exit(1)

logger = get_logger(__name__)

def download_rocstories_corpus(output_dir: Optional[str] = None, sample_size: int = 1000) -> Path:
    """
    Download ROCStories corpus via HuggingFace datasets and sample a representative subset.
    
    Args:
        output_dir: Directory to save the sampled dataset. Defaults to data/text/
        sample_size: Number of stories to sample.
        
    Returns:
        Path to the output JSONL file.
    """
    config = get_config()
    if output_dir is None:
        output_dir = str(Path("data/text"))
        
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "rocstories_sample.jsonl"
    
    info(f"Loading ROCStories dataset from HuggingFace...")
    try:
        # Load the ROCStories dataset
        dataset = load_dataset("rocstories", split="train")
        
        info(f"Dataset loaded with {len(dataset)} stories. Sampling {sample_size} stories...")
        
        # Ensure sample_size doesn't exceed dataset size
        actual_sample_size = min(sample_size, len(dataset))
        
        # Sample randomly
        sampled_indices = dataset.train_test_split(test_size=actual_sample_size, shuffle=True, seed=config['random_seed'])['test']
        
        # Convert to list of dicts for JSONL export
        stories = []
        for item in sampled_indices:
            story_text = " ".join(item['story'])
            stories.append({
                "story_id": item.get('story_id', len(stories)),
                "text": story_text,
                "source": "rocstories"
            })
        
        # Write to JSONL file
        with open(output_file, 'w', encoding='utf-8') as f:
            for story in stories:
                f.write(f"{story}\n")
        
        info(f"Successfully saved {len(stories)} stories to {output_file}")
        return output_file
        
    except Exception as e:
        error(f"Failed to download or process ROCStories: {str(e)}")
        raise

def main():
    """Main entry point for data ingestion script."""
    config = get_config()
    logger.info("Starting data ingestion pipeline...")
    
    # Download OpenNeuro dataset (placeholder for T012 implementation)
    # download_openneuro_dataset()
    
    # Download ROCStories corpus (T015)
    rocstories_path = download_rocstories_corpus()
    
    logger.info("Data ingestion pipeline completed.")
    return rocstories_path

if __name__ == "__main__":
    main()
