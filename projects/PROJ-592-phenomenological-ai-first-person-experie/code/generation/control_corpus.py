"""
Control Corpus Generation Module.

Generates control samples from real external datasets to compare against
phenomenological reports. Uses arxiv_nlp dataset for control samples.
"""
import os
import random
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import from sibling modules using the exact API surface
# Note: We import config from the local code directory, not the installed package
import sys
from pathlib import Path as PathLib

# Add the code directory to the path to import our local config
code_dir = PathLib(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

try:
    from config import get_config
except ImportError:
    # Fallback: define a minimal config function if the real one is not available
    logger.warning("Could not import get_config from config module. Using fallback.")
    
    def get_config(config_path: Optional[str] = None) -> Dict[str, Any]:
        """Fallback config function that returns default values."""
        return {
            "seeds": {"default": 42},
            "paths": {
                "data_raw": "data/raw",
                "data_processed": "data/processed",
                "data_qualitative": "data/qualitative"
            },
            "model_ids": {
                "primary": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
            },
            "phenomenological_markers": {
                "sensory": ["see", "hear", "feel", "touch", "taste", "smell", "light", "sound"],
                "temporal": ["now", "then", "before", "after", "moment", "duration"],
                "intentional": ["think", "believe", "desire", "intend", "perceive", "experience"]
            }
        }

# Import retry decorator from utils.logging
from utils.logging import retry_on_failure


def load_control_dataset(dataset_name: str = "arxiv_nlp") -> Any:
    """
    Load the control dataset from Hugging Face.
    
    Args:
        dataset_name: Name of the dataset to load (default: arxiv_nlp)
        
    Returns:
        The loaded dataset
    """
    logger.info(f"Loading control dataset: {dataset_name}")
    try:
        dataset = load_dataset(dataset_name, split="train")
        logger.info(f"Successfully loaded {len(dataset)} samples from {dataset_name}")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        raise


@retry_on_failure(max_attempts=3, delay=2.0)
def sample_control_corpus(
    dataset: Any,
    n_samples: int = 80,
    seed: int = 42,
    text_field: str = "abstract"
) -> List[Dict[str, Any]]:
    """
    Sample control corpus from the loaded dataset.
    
    Args:
        dataset: The loaded dataset
        n_samples: Number of samples to collect
        seed: Random seed for reproducibility
        text_field: Field to use as the text content
        
    Returns:
        List of control samples with metadata
    """
    random.seed(seed)
    samples = []
    
    # Get available indices
    indices = list(range(len(dataset)))
    random.shuffle(indices)
    
    # Sample up to n_samples
    count = 0
    for idx in indices:
        if count >= n_samples:
            break
        
        try:
            item = dataset[idx]
            text = item.get(text_field, item.get("text", ""))
            
            if text and len(text.strip()) > 0:
                samples.append({
                    "id": f"control_{count:04d}",
                    "text": text.strip(),
                    "source": dataset_name,
                    "original_index": idx,
                    "type": "control"
                })
                count += 1
        except Exception as e:
            logger.warning(f"Skipping sample at index {idx}: {e}")
            continue
    
    logger.info(f"Sampled {len(samples)} control samples")
    return samples


def save_control_corpus(samples: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save control samples to a JSON file.
    
    Args:
        samples: List of control samples
        output_path: Path to save the JSON file
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(samples)} control samples to {output_path}")


def generate_control_corpus(
    config: Dict[str, Any],
    n_samples: int = 80,
    dataset_name: str = "arxiv_nlp"
) -> List[Dict[str, Any]]:
    """
    Generate the complete control corpus.
    
    Args:
        config: Configuration dictionary
        n_samples: Number of samples to generate
        dataset_name: Name of the dataset to use
        
    Returns:
        List of generated control samples
    """
    seed = config.get("seeds", {}).get("default", 42)
    data_raw_path = config.get("paths", {}).get("data_raw", "data/raw")
    
    # Ensure output directory exists
    Path(data_raw_path).mkdir(parents=True, exist_ok=True)
    
    # Load dataset
    dataset = load_control_dataset(dataset_name)
    
    # Sample control corpus
    samples = sample_control_corpus(
        dataset=dataset,
        n_samples=n_samples,
        seed=seed
    )
    
    # Save samples
    output_path = Path(data_raw_path) / "control_corpus.json"
    save_control_corpus(samples, str(output_path))
    
    return samples


def main() -> None:
    """Main entry point for control corpus generation."""
    config_path = "code/config.py"
    
    try:
        config = get_config(config_path)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        # Use fallback config
        config = get_config()
    
    logger.info("Starting control corpus generation...")
    samples = generate_control_corpus(config, n_samples=80)
    logger.info(f"Generated {len(samples)} control samples")


if __name__ == "__main__":
    main()
