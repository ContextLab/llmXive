"""
Control Corpus Generation Module.
Generates technical report samples to serve as a control group (non-phenomenological).
Merges these with phenomenological outputs for discriminant validity analysis.
"""
from __future__ import annotations

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
from datasets import load_dataset

# Project imports
from config import get_marker_dictionaries, PROJECT_ROOT
from utils.logging import get_logger, log_operation, retry_on_failure

# Constants
TARGET_SAMPLES = 80
DATASET_NAME = "cnn_dailymail"  # Verified real source: CNN/DailyMail news summaries
DATASET_SPLIT = "3.0.0"  # Specific version to ensure reproducibility
SAMPLE_SIZE = 150  # Load slightly more than target to account for filtering

logger = get_logger(__name__)


class ControlCorpusError(Exception):
    """Custom exception for control corpus generation errors."""
    pass


def load_control_dataset() -> Any:
    """
    Load the CNN/DailyMail dataset.
    This dataset contains news articles and summaries, which are typically
    written in an objective, third-person, technical/journalistic style.
    """
    log_operation("load_control_dataset_start", dataset=DATASET_NAME)
    try:
        # Use streaming to avoid loading the full dataset into memory
        dataset = load_dataset(DATASET_NAME, "3.0.0", split="train", streaming=True)
        logger.info(f"Successfully loaded dataset stream: {DATASET_NAME}")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset {DATASET_NAME}: {e}")
        raise ControlCorpusError(f"Dataset load failed: {e}")


@retry_on_failure(max_attempts=3, delay=2.0, logger=logger)
def sample_control_corpus(dataset: Any, n: int = TARGET_SAMPLES) -> List[Dict[str, Any]]:
    """
    Sample n items from the control dataset.
    Filters for items with sufficient length to be meaningful reports.
    """
    log_operation("sample_control_corpus_start", n=n)
    samples = []
    count = 0
    
    # Iterate through the streaming dataset
    for item in dataset:
        if count >= n:
            break
        
        # Filter for reasonable length (avoid very short snippets)
        text = item.get("article", "") or item.get("highlights", "")
        if len(text) > 50:
            samples.append({
                "id": f"control_{count:04d}",
                "text": text,
                "source": DATASET_NAME,
                "type": "control"  # Explicitly mark as control
            })
            count += 1
    
    if count < n:
        logger.warning(f"Only collected {count} samples, requested {n}. Dataset may be exhausted.")
    
    log_operation("sample_control_corpus_complete", collected=count)
    return samples


def save_control_corpus(samples: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the control samples to a JSON file."""
    log_operation("save_control_corpus_start", path=str(output_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(samples)} control samples to {output_path}")
    log_operation("save_control_corpus_complete", path=str(output_path), count=len(samples))


def verify_marker_absence(samples: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Verify that control samples lack phenomenological markers.
    Returns a dictionary of marker density scores (should be low).
    """
    log_operation("verify_marker_absence_start")
    markers = get_marker_dictionaries()
    all_markers = [m for cat in markers.values() for m in cat]
    
    results = {
        "sensory": 0,
        "temporal": 0,
        "intentional": 0,
        "total_markers": 0,
        "sample_count": len(samples)
    }
    
    for sample in samples:
        text = sample.get("text", "").lower()
        for category, marker_list in markers.items():
            count = sum(1 for m in marker_list if m in text)
            results[category] += count
        
        results["total_markers"] += sum(
            1 for m in all_markers if m in text
        )
    
    # Calculate density (markers per sample)
    if len(samples) > 0:
        results["density_sensory"] = results["sensory"] / len(samples)
        results["density_temporal"] = results["temporal"] / len(samples)
        results["density_intentional"] = results["intentional"] / len(samples)
        results["density_total"] = results["total_markers"] / len(samples)
    
    log_operation("verify_marker_absence_complete", densities={
        k: v for k, v in results.items() if k.startswith("density")
    })
    return results


def merge_with_phenomenological(
    control_path: Path, 
    phenomenological_path: Path, 
    output_path: Path
) -> Path:
    """
    Merge control samples with phenomenological outputs into a single CSV.
    Ensures the 'type' column distinguishes between 'control' and 'phenomenological'.
    """
    log_operation("merge_datasets_start", control=str(control_path), pheno=str(phenomenological_path))
    
    # Load control data
    with open(control_path, "r", encoding="utf-8") as f:
        control_data = json.load(f)
    df_control = pd.DataFrame(control_data)
    if "type" not in df_control.columns:
        df_control["type"] = "control"
    
    # Load phenomenological data (assuming it's already a CSV or JSON)
    if phenomenological_path.suffix == ".csv":
        df_pheno = pd.read_csv(phenomenological_path)
    else:
        with open(phenomenological_path, "r", encoding="utf-8") as f:
            pheno_data = json.load(f)
        df_pheno = pd.DataFrame(pheno_data)
    
    # Ensure type column exists for phenomenological data
    if "type" not in df_pheno.columns:
        df_pheno["type"] = "phenomenological"
    
    # Normalize columns if necessary
    # Assume phenomenological data has 'text' or 'content'
    if "text" not in df_pheno.columns and "content" in df_pheno.columns:
        df_pheno.rename(columns={"content": "text"}, inplace=True)
    
    # Concatenate
    df_merged = pd.concat([df_pheno, df_control], ignore_index=True)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    df_merged.to_csv(output_path, index=False)
    
    logger.info(f"Merged {len(df_pheno)} phenomenological and {len(df_control)} control samples into {output_path}")
    log_operation("merge_datasets_complete", output=str(output_path), total=len(df_merged))
    
    return output_path


def generate_control_corpus(
    output_dir: Optional[Path] = None,
    merge_with: Optional[Path] = None
) -> Path:
    """
    Main entry point to generate the control corpus and optionally merge it.
    """
    if output_dir is None:
        output_dir = PROJECT_ROOT / "data" / "processed"
    
    control_path = output_dir / "control_corpus.json"
    merged_path = output_dir / "merged_dataset.csv"
    
    # 1. Load and sample
    dataset = load_control_dataset()
    samples = sample_control_corpus(dataset, n=TARGET_SAMPLES)
    
    if len(samples) < TARGET_SAMPLES:
        logger.warning(f"Generated only {len(samples)} control samples. Proceeding anyway.")
    
    # 2. Save control corpus
    save_control_corpus(samples, control_path)
    
    # 3. Verify marker absence
    verification = verify_marker_absence(samples)
    logger.info(f"Control corpus marker density: {verification['density_total']:.2f} per sample")
    
    # 4. Merge if requested
    if merge_with and merge_with.exists():
        merge_with_phenomenological(control_path, merge_with, merged_path)
        return merged_path
    
    return control_path


def main():
    """CLI entry point for control corpus generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate control corpus for phenomenological AI study.")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory path")
    parser.add_argument("--merge-with", type=str, default=None, help="Path to phenomenological CSV to merge with")
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir) if args.output_dir else None
    merge_with = Path(args.merge_with) if args.merge_with else None
    
    result_path = generate_control_corpus(output_dir=output_dir, merge_with=merge_with)
    print(f"Control corpus generation complete. Output: {result_path}")


if __name__ == "__main__":
    main()