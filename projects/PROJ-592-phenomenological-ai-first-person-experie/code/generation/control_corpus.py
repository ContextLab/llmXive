"""Control corpus generation using real technical reports.

This module generates a control corpus of non-phenomenological text (technical
reports) to serve as a baseline for discriminant validity analysis.

Real Data Source: 'cnn_dailymail' dataset (articles column treated as technical text).
Fallback: 'imdb' dataset (reviews treated as technical text) if primary fails.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import random
import pandas as pd

from utils.logging import log_operation, get_logger, retry_on_failure
from utils.io import safe_write_csv, safe_write_json

# Verified Real Source: 'cnn_dailymail' (view as 'article' column)
# This is a standard news summarization dataset where articles are non-first-person
# technical/journalistic text, suitable for control corpus.
DATASET_ID = "cnn_dailymail"
DATASET_CONFIG = "3.0.0"
TEXT_COLUMN = "article"

logger = get_logger()


def load_control_dataset(split: str = "train", limit: Optional[int] = None):
    """Load a real dataset to serve as control corpus.
    
    Args:
        split: Dataset split to load (default: 'train')
        limit: Maximum number of samples to load (None for all)
        
    Returns:
        Dataset object with text samples
        
    Raises:
        RuntimeError: If no real dataset can be loaded
    """
    log_operation("load_control_dataset", dataset=DATASET_ID, split=split, limit=limit)
    
    try:
        from datasets import load_dataset
        
        # Load dataset with streaming to handle large datasets efficiently
        dataset = load_dataset(
            DATASET_ID, 
            name=DATASET_CONFIG, 
            split=split, 
            trust_remote_code=True,
            streaming=True
        )
        
        # Convert streaming dataset to list if limit is specified
        if limit:
            samples = []
            for item in dataset:
                if len(samples) >= limit:
                    break
                samples.append(item)
            # Create a simple list-based dataset-like object
            class SimpleDataset:
                def __init__(self, data):
                    self.data = data
                def __iter__(self):
                    return iter(self.data)
                def __len__(self):
                    return len(self.data)
            dataset = SimpleDataset(samples)
        else:
            # If no limit, convert to list for easier iteration
            dataset = list(dataset)
            class SimpleDataset:
                def __init__(self, data):
                    self.data = data
                def __iter__(self):
                    return iter(self.data)
                def __len__(self):
                    return len(self.data)
            dataset = SimpleDataset(dataset)
        
        return dataset
    except Exception as e:
        logger.warning(f"Failed to load {DATASET_ID}: {e}. Falling back to 'imdb'.")
        try:
            from datasets import load_dataset
            dataset = load_dataset("imdb", split="train", streaming=True)
            # Map 'text' to 'article' for consistency
            class MappedDataset:
                def __init__(self, base_dataset):
                    self.base_dataset = base_dataset
                def __iter__(self):
                    for item in self.base_dataset:
                        item['article'] = item.pop('text')
                        yield item
                def __len__(self):
                    # Unknown for streaming, return 0 or estimate
                    return 0
            dataset = MappedDataset(dataset)
            return dataset
        except Exception as e2:
            logger.error(f"Failed to load fallback dataset: {e2}")
            raise RuntimeError("Could not load any real dataset for control corpus.") from e2


@retry_on_failure(max_attempts=3, delay=2.0, logger=logger)
def sample_control_corpus(dataset, n_samples: int = 80) -> List[Dict[str, Any]]:
    """Sample n_samples from the dataset and format as control.
    
    Args:
        dataset: Dataset object to sample from
        n_samples: Number of samples to extract
        
    Returns:
        List of formatted control samples
    """
    log_operation("sample_control_corpus", n_samples=n_samples)
    
    samples = []
    count = 0
    
    for item in dataset:
        if count >= n_samples:
            break
        
        text = item.get(TEXT_COLUMN, "")
        # Ensure text has sufficient length and is not empty
        if text and len(text.strip()) > 100:
            samples.append({
                "id": f"control_{count:04d}",
                "text": text[:2000],  # Truncate to avoid massive tokens
                "strategy": "Technical",
                "type": "control",
                "control_label": "control",
                "seed": random.randint(1000, 9999)
            })
            count += 1
    
    if len(samples) < n_samples:
        logger.warning(f"Only sampled {len(samples)} control samples, requested {n_samples}")
    
    return samples


def save_control_corpus(samples: List[Dict[str, Any]], output_path: str) -> None:
    """Save control samples to CSV/JSON.
    
    Args:
        samples: List of sample dictionaries
        output_path: Path to output file
    """
    log_operation("save_control_corpus", output_path=output_path, num_samples=len(samples))
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as CSV
    df = pd.DataFrame(samples)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(samples)} control samples to {output_path}")


def merge_with_phenomenological(control_path: str, pheno_path: str, output_path: str) -> None:
    """Merge control corpus with existing phenomenological outputs.
    
    Args:
        control_path: Path to control corpus CSV
        pheno_path: Path to phenomenological corpus CSV (if exists)
        output_path: Path to merged output CSV
    """
    log_operation("merge_with_phenomenological", 
                control_path=control_path, 
                pheno_path=pheno_path, 
                output_path=output_path)
    
    # Load control data
    control_df = pd.read_csv(control_path)
    
    # Load phenomenological data if it exists
    if os.path.exists(pheno_path):
        pheno_df = pd.read_csv(pheno_path)
        # Ensure both have 'type' column
        if 'type' not in pheno_df.columns:
            pheno_df['type'] = 'phenomenological'
        if 'type' not in control_df.columns:
            control_df['type'] = 'control'
        
        # Concatenate
        merged_df = pd.concat([pheno_df, control_df], ignore_index=True)
    else:
        # Only control data exists
        if 'type' not in control_df.columns:
            control_df['type'] = 'control'
        merged_df = control_df
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write merged dataset
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Merged {len(merged_df)} samples to {output_path}")
    logger.info(f"Control samples: {(merged_df['type'] == 'control').sum()}")
    logger.info(f"Phenomenological samples: {(merged_df['type'] == 'phenomenological').sum()}")


def verify_marker_absence(samples: List[Dict[str, Any]], marker_dicts: Dict[str, List[str]]) -> Dict[str, Any]:
    """Verify that control samples lack phenomenological markers.
    
    Args:
        samples: List of control samples
        marker_dicts: Dictionary of marker categories and keywords
        
    Returns:
        Dictionary with verification results
    """
    log_operation("verify_marker_absence", num_samples=len(samples))
    
    results = {
        "total_samples": len(samples),
        "samples_with_markers": 0,
        "marker_counts": {"sensory": 0, "temporal": 0, "intentional": 0},
        "details": []
    }
    
    from config import get_marker_dictionaries
    if not marker_dicts:
        marker_dicts = get_marker_dictionaries()
    
    for sample in samples:
        text = sample.get("text", "").lower()
        sample_markers = {"sensory": 0, "temporal": 0, "intentional": 0}
        
        for category, keywords in marker_dicts.items():
            if category in sample_markers:
                for keyword in keywords:
                    if keyword.lower() in text:
                        sample_markers[category] += 1
                        results["marker_counts"][category] += 1
        
        if sum(sample_markers.values()) > 0:
            results["samples_with_markers"] += 1
            results["details"].append({
                "id": sample.get("id"),
                "markers": sample_markers
            })
    
    logger.info(f"Verification: {results['samples_with_markers']}/{results['total_samples']} "
               f"control samples contained phenomenological markers")
    
    return results


def generate_control_corpus(config: Dict[str, Any]) -> None:
    """Main entry point for control corpus generation.
    
    Args:
        config: Configuration dictionary with generation parameters
    """
    log_operation("generate_control_corpus")
    
    limit = config.get("generation_limit", 80)
    output_dir = Path(config.get("output_dir", "data/processed"))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    control_path = output_dir / "control_corpus.csv"
    merged_path = output_dir / "merged_dataset.csv"
    pheno_path = output_dir / "phenomenological_corpus.csv"  # Expected path for pheno data
    
    # Load real data
    logger.info(f"Loading control dataset (limit={limit})...")
    dataset = load_control_dataset(limit=limit)
    
    # Sample
    logger.info(f"Sampling {limit} control samples...")
    samples = sample_control_corpus(dataset, n_samples=limit)
    
    # Save control corpus
    save_control_corpus(samples, str(control_path))
    
    # Merge with phenomenological data if it exists
    # Note: phenomenological data should be generated by T009/T009b
    if os.path.exists(pheno_path):
        logger.info(f"Found phenomenological corpus at {pheno_path}, merging...")
        merge_with_phenomenological(str(control_path), pheno_path, str(merged_path))
    elif os.path.exists(merged_path):
        # Append to existing merged file
        logger.info(f"Appending to existing merged dataset at {merged_path}")
        merge_with_phenomenological(str(control_path), merged_path, str(merged_path))
    else:
        # No phenomenological data yet, just save control as merged
        logger.info("No phenomenological data found, saving control corpus as merged dataset")
        safe_write_csv(samples, str(merged_path))
    
    # Verify marker absence
    from config import get_marker_dictionaries
    marker_dicts = get_marker_dictionaries()
    verification = verify_marker_absence(samples, marker_dicts)
    
    # Save verification report
    verification_path = output_dir / "control_verification.json"
    safe_write_json(verification, str(verification_path))
    
    log_operation("generate_control_corpus_complete", 
                samples=len(samples),
                verification=verification)
    
    logger.info("Control corpus generation complete")


def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate control corpus for phenomenological analysis")
    parser.add_argument("--limit", type=int, default=80, help="Number of control samples to generate")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory")
    args = parser.parse_args()
    
    config = {
        "generation_limit": args.limit,
        "output_dir": args.output_dir
    }
    generate_control_corpus(config)


if __name__ == "__main__":
    main()
