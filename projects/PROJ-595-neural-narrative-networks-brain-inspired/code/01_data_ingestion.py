import os
import sys
from pathlib import Path
from typing import Optional
from config import get_config
from utils.logging_config import get_logger, info, error, warning

# Import datasets dynamically to avoid hard dependency if not installed,
# but the task requires it to be present.
try:
    from datasets import load_dataset
except ImportError:
    error("E001", "Missing dependency: 'datasets' package. Please run 'pip install datasets' to proceed.")
    sys.exit(1)

logger = get_logger(__name__)

def download_rocstories_corpus(output_dir: str, sample_size: int = 1000) -> str:
    """
    Downloads the ROCStories corpus via HuggingFace datasets and samples a subset.
    
    Args:
        output_dir: Path to the directory where the JSONL file will be saved.
        sample_size: Number of stories to sample from the dataset.
        
    Returns:
        Path to the generated JSONL file.
        
    Raises:
        RuntimeError: If the dataset cannot be fetched or processed.
    """
    dataset_id = "rocstories"
    output_path = Path(output_dir) / "rocstories_sample.jsonl"
    
    logger.info(f"Attempting to load dataset: {dataset_id}")
    
    try:
        # Load the dataset with streaming to avoid memory issues if large
        # We specifically request the 'train' split which contains the stories.
        dataset = load_dataset(dataset_id, split="train", streaming=True)
    except Exception as e:
        error("E002", f"Failed to load dataset '{dataset_id}' from HuggingFace: {str(e)}")
        raise RuntimeError(f"Data fetch failed: {e}") from e
    
    logger.info(f"Sampling {sample_size} stories from the dataset...")
    
    stories = []
    count = 0
    
    try:
        for item in dataset:
            if count >= sample_size:
                break
            
            # ROCStories dataset typically has 'story' or 'text' fields.
            # The standard 'rocstories' dataset usually has a 'story' field containing the full text.
            # We verify the key existence.
            story_text = item.get("story") or item.get("text")
            
            if story_text:
                stories.append({"story_id": count, "text": story_text})
                count += 1
            else:
                warning(f"Skipping item {count} due to missing 'story' or 'text' field.")
                
    except Exception as e:
        error("E003", f"Error during dataset iteration or sampling: {str(e)}")
        raise RuntimeError(f"Sampling failed: {e}") from e
    
    if count == 0:
        error("E004", "No stories were extracted from the dataset. The dataset structure might have changed.")
        raise RuntimeError("No data extracted.")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing {count} stories to {output_path}...")
    
    with open(output_path, "w", encoding="utf-8") as f:
        for story in stories:
            f.write(json.dumps(story, ensure_ascii=False) + "\n")
    
    info(f"Successfully wrote {count} stories to {output_path}")
    return str(output_path)

def main():
    """
    Main entry point for the ROCStories ingestion task.
    """
    config = get_config()
    output_dir = Path(config.get("data_dir", "data")) / "text"
    
    # Default sample size for a representative subset (as per task T015)
    sample_size = 1000
    
    try:
        file_path = download_rocstories_corpus(str(output_dir), sample_size)
        info(f"Task T015 completed: {file_path}")
    except Exception as e:
        error("E005", f"Task T015 failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
