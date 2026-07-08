import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np

from src.models.entities import TopicVector
from src.utils.logging import get_logger
from src.utils.manifest import load_reproducibility_manifest, save_reproducibility_manifest
from src.models.metrics.proportions import save_topic_vectors as proportions_saver

logger = get_logger(__name__)


def load_topic_vectors_from_proportions(
    processed_dir: Path,
    windows: List[str]
) -> Dict[str, TopicVector]:
    """
    Loads topic vectors (proportion distributions) for all windows.
    This assumes T024 (proportions.py) has already saved the data.
    We reconstruct the TopicVector objects from the saved JSON structure.
    """
    vectors = {}
    # The proportions module saves to results/stats/topic_vectors.json
    # We need to read that back to construct the entities or use the saved structure directly.
    # To ensure we have the full TopicVector object structure as defined in entities.py:
    # TopicVector has: window_id, topic_id, proportions (np.array), coherence_score (float)
    
    # Since T024 saves the raw data, we read it here to ensure consistency.
    # However, the task T025 specifically asks to save the vectors and update manifest.
    # We will rely on the fact that T024's `save_topic_vectors` creates the base file.
    # If that file doesn't exist yet, we assume the pipeline runs sequentially and it exists.
    
    input_file = processed_dir.parent / "stats" / "topic_vectors.json"
    if not input_file.exists():
        logger.warning(f"Input file {input_file} not found. Cannot load vectors for T025.")
        return {}

    with open(input_file, 'r') as f:
        data = json.load(f)

    for window_id, window_data in data.items():
        if window_id not in windows:
            continue
        
        # Reconstruct TopicVector objects or use the dict directly if that's what's needed
        # For the manifest update, we need k_topics and coherence_threshold.
        # We assume the data structure contains these or can derive them.
        vectors[window_id] = window_data

    return vectors


def save_final_topic_vectors(
    topic_vectors: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Saves the final topic vectors to the specified JSON path.
    Ensures the directory exists and writes the complete JSON structure.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(topic_vectors, f, indent=2, default=str)
    
    logger.info(f"Saved topic vectors to {output_path}")


def update_manifest_with_analysis_params(
    manifest_path: Path,
    k_topics: int,
    coherence_threshold: float,
    windows: List[str]
) -> None:
    """
    Updates the reproducibility manifest with LDA parameters: k_topics and coherence_threshold.
    """
    if not manifest_path.exists():
        logger.error(f"Manifest file {manifest_path} not found. Cannot update.")
        return

    manifest = load_reproducibility_manifest(manifest_path)
    
    if 'lda_analysis' not in manifest:
        manifest['lda_analysis'] = {}
    
    manifest['lda_analysis']['k_topics'] = k_topics
    manifest['lda_analysis']['coherence_threshold'] = coherence_threshold
    manifest['lda_analysis']['windows_processed'] = windows
    manifest['lda_analysis']['status'] = 'completed'

    save_reproducibility_manifest(manifest, manifest_path)
    logger.info(f"Updated manifest at {manifest_path} with k={k_topics}, threshold={coherence_threshold}")


def main() -> None:
    """
    Main entry point for T025: Save topic vectors and update manifest.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parents[3]
    results_dir = project_root / "results"
    stats_dir = results_dir / "stats"
    manifest_path = results_dir / "manifest.json"
    output_vectors_path = stats_dir / "topic_vectors.json"

    # Configuration parameters (matching T020/T021)
    K_TOPICS = 10
    COHERENCE_THRESHOLD = 0.4
    WINDOWS = ["2000-2004", "2005-2009", "2010-2014", "2015-2019", "2020-2024"]

    logger.info(f"Starting T025: Saving topic vectors to {output_vectors_path}")

    # Ensure directories exist
    stats_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load vectors from the intermediate output (produced by T024 proportions.py)
    # Note: In a real pipeline, T024 would have just run. We read the file it created.
    if not output_vectors_path.exists():
        # If the file doesn't exist, we cannot proceed with real data.
        # In a real execution, this implies T024 failed or hasn't run.
        # We raise an error to satisfy "Fail loudly".
        raise FileNotFoundError(
            f"Required intermediate file {output_vectors_path} not found. "
            "Ensure T024 (proportions.py) has been executed successfully."
        )

    # Read the raw data to verify structure and prepare for final save
    with open(output_vectors_path, 'r') as f:
        raw_vectors = json.load(f)

    # 2. Save the final topic vectors (T025 requirement: Save to results/stats/topic_vectors.json)
    # We read and write back to ensure it's finalized, or we could just assume it's done if T024 did it.
    # The task says "Save topic vectors to ...", so we ensure it's there.
    # If T024 wrote it, this is effectively a confirmation, but we write it again to be safe.
    save_final_topic_vectors(raw_vectors, output_vectors_path)

    # 3. Update the manifest with k_topics and coherence_threshold
    update_manifest_with_analysis_params(
        manifest_path,
        k_topics=K_TOPICS,
        coherence_threshold=COHERENCE_THRESHOLD,
        windows=WINDOWS
    )

    logger.info("T025 completed successfully.")


if __name__ == "__main__":
    main()