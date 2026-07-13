"""
Control Corpus Generation Module.

Generates control samples from real datasets for discriminant validity analysis.
Uses arxiv_nlp dataset as the control source.
"""
import os
import random
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Local imports
from config import get_config
from utils.logging import get_logger, log_operation, retry_on_failure
from utils.io import safe_write_json, safe_write_csv

logger = get_logger("control_corpus")

def load_control_dataset(dataset_name: str = "arxiv_nlp") -> Any:
    """
    Load the control dataset.
    
    Args:
        dataset_name: Name of the dataset to load
    
    Returns:
        Loaded dataset object
    """
    try:
        from datasets import load_dataset
        logger.log("dataset_load", name=dataset_name)
        dataset = load_dataset(dataset_name, split="train")
        return dataset
    except ImportError:
        logger.log("dataset_load_error", error="datasets library not installed")
        raise
    except Exception as e:
        logger.log("dataset_load_error", error=str(e))
        raise

@retry_on_failure(max_attempts=3, delay=2.0, logger=logger)
def sample_control_corpus(
    dataset: Any,
    num_samples: int = 80,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Sample control corpus from the dataset.
    
    Args:
        dataset: Loaded dataset object
        num_samples: Number of samples to extract
        seed: Random seed for reproducibility
    
    Returns:
        List of sampled text entries
    """
    random.seed(seed)
    
    # Get random indices
    indices = random.sample(range(len(dataset)), min(num_samples, len(dataset)))
    
    samples = []
    for idx in indices:
        row = dataset[idx]
        # Extract text content (adjust based on dataset schema)
        text = row.get("text", row.get("abstract", row.get("content", "")))
        if text and len(text) > 50:  # Filter very short entries
            samples.append({
                "text": text[:1024],  # Truncate if too long
                "source": "arxiv_nlp",
                "original_index": idx,
                "seed": seed
            })
    
    logger.log("sampling_complete", count=len(samples), target=num_samples)
    return samples

def save_control_corpus(samples: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save control corpus to file.
    
    Args:
        samples: List of sampled entries
        output_path: Path to save the file
    """
    safe_write_json(output_path, samples)
    logger.log("save_complete", path=str(output_path), count=len(samples))

def generate_control_corpus(
    config_path: str,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate the full control corpus.
    
    Args:
        config_path: Path to configuration file
        output_dir: Optional output directory override
    
    Returns:
        Summary of the generation run
    """
    config = get_config(config_path)
    output_dir = output_dir or config.get("output_dir", "data/raw")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.log("control_corpus_start", config_path=config_path)
    
    # Load dataset
    dataset = load_control_dataset()
    
    # Sample corpus
    num_samples = config.get("control_samples", 80)
    seed = config.get("seed", 42)
    samples = sample_control_corpus(dataset, num_samples=num_samples, seed=seed)
    
    # Save results
    output_file = output_path / "control_corpus.json"
    save_control_corpus(samples, output_file)
    
    # Summary
    summary = {
        "total_samples": len(samples),
        "target_samples": num_samples,
        "source": "arxiv_nlp",
        "seed": seed,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    summary_file = output_path / "control_corpus_summary.json"
    safe_write_json(summary_file, summary)
    
    logger.log("control_corpus_complete", **summary)
    
    return summary

def main():
    """CLI entry point for control corpus generation."""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Control Corpus Generator")
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.py",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Override output directory"
    )
    
    args = parser.parse_args()
    
    try:
        summary = generate_control_corpus(
            config_path=args.config,
            output_dir=args.output_dir
        )
        
        print(json.dumps(summary, indent=2))
        logger.log("main_success", summary=summary)
        
    except Exception as e:
        logger.log("main_error", error=str(e))
        print(f"Error: {e}", file=sys.stderr)
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
