"""
T014: Generate synthetic Moral Stories and VR interaction logs.

This script generates a synthetic dataset for moral stories and VR interaction logs
with known ground truth effect sizes for parameter recovery analysis.

Distributions:
- response_time ~ LogNormal(3.5, 0.5)
- gaze_metrics ~ Normal(0.5, 0.1)

Outputs:
- data/processed/synthetic_logs.csv
- data/processed/synthetic_stories.csv (if separate)
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from code.config import get_path, N_CONFIG, DATA_MODE
from code.data.simulation_mfq import load_mdes_report
from code.utils.hashing import calculate_checksum, update_state_file
from code.utils.logging import log_operation, get_logger

# Constants
GROUND_TRUTH_EFFECT_SIZE = 0.8  # Cohen's d for salience effect on judgment
RESPONSE_TIME_MEAN = 3.5
RESPONSE_TIME_STD = 0.5
GAZE_MEAN = 0.5
GAZE_STD = 0.1
NUM_STORIES = 10
SALIENCE_LEVELS = ["low", "high"]

logger = get_logger("simulation_stories")


def set_seed(seed: int = 42) -> None:
    """Set random seed for reproducibility."""
    np.random.seed(seed)
    logger.log("set_seed", seed=seed)


def generate_story_text(story_id: int, salience_level: str) -> str:
    """
    Generate a synthetic moral story text.
    
    In a real implementation, this would map to actual story templates.
    For simulation, we generate placeholder text with metadata.
    """
    templates = [
        "The agent {action} the victim in the {context}.",
        "A person {action} another person who was {context}.",
        "The protagonist {action} the target while {context}.",
    ]
    actions = ["helped", "harmed", "ignored", "protected"]
    contexts = ["danger", "need", "confusion", "distress"]
    
    action = np.random.choice(actions)
    context = np.random.choice(contexts)
    
    template = np.random.choice(templates)
    text = template.format(action=action, context=context)
    
    # Inject salience into text for simulation purposes
    if salience_level == "high":
        text += f" [Salience: High - {story_id}]"
    else:
        text += f" [Salience: Low - {story_id}]"
        
    return text


def determine_salience_level(story_id: int, seed: Optional[int] = None) -> str:
    """
    Determine salience level for a story.
    
    Balanced assignment: even IDs -> low, odd IDs -> high (or random with seed).
    """
    if seed is not None:
        np.random.seed(seed + story_id)
        return np.random.choice(SALIENCE_LEVELS)
    return SALIENCE_LEVELS[story_id % 2]


def generate_moral_stories_dataset(n_participants: int, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic moral stories dataset.
    
    Columns:
    - participant_id
    - story_id
    - salience_level
    - story_text
    - ground_truth_effect (injected for recovery analysis)
    """
    set_seed(seed)
    
    records = []
    for p_id in range(1, n_participants + 1):
        for s_id in range(1, NUM_STORIES + 1):
            salience = determine_salience_level(s_id, seed=p_id)
            text = generate_story_text(s_id, salience)
            
            # Inject ground truth effect based on salience
            # High salience -> higher effect, Low salience -> baseline
            effect = GROUND_TRUTH_EFFECT_SIZE if salience == "high" else 0.0
            
            records.append({
                "participant_id": p_id,
                "story_id": s_id,
                "salience_level": salience,
                "story_text": text,
                "ground_truth_effect": effect
            })
    
    df = pd.DataFrame(records)
    logger.log("generate_moral_stories_dataset", n_records=len(df), n_participants=n_participants)
    return df


def generate_vr_logs_dataset(n_participants: int, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic VR interaction logs dataset.
    
    Distributions:
    - response_time ~ LogNormal(3.5, 0.5)
    - gaze_metrics ~ Normal(0.5, 0.1)
    
    Judgment rating is influenced by ground_truth_effect + noise.
    
    Columns:
    - participant_id
    - story_id
    - salience_level
    - response_time
    - gaze_metrics
    - judgment_rating
    """
    set_seed(seed)
    
    records = []
    for p_id in range(1, n_participants + 1):
        for s_id in range(1, NUM_STORIES + 1):
            salience = determine_salience_level(s_id, seed=p_id)
            
            # Generate response time
            response_time = np.random.lognormal(RESPONSE_TIME_MEAN, RESPONSE_TIME_STD)
            
            # Generate gaze metrics
            gaze_metrics = np.random.normal(GAZE_MEAN, GAZE_STD)
            gaze_metrics = max(0.0, min(1.0, gaze_metrics))  # Clamp to [0, 1]
            
            # Generate judgment rating influenced by ground truth effect
            base_rating = 3.0  # Neutral
            effect = GROUND_TRUTH_EFFECT_SIZE if salience == "high" else 0.0
            noise = np.random.normal(0, 0.5)
            judgment_rating = base_rating + effect + noise
            judgment_rating = max(1.0, min(5.0, judgment_rating))  # Clamp to [1, 5]
            
            records.append({
                "participant_id": p_id,
                "story_id": s_id,
                "salience_level": salience,
                "response_time": round(response_time, 4),
                "gaze_metrics": round(gaze_metrics, 4),
                "judgment_rating": round(judgment_rating, 4),
                "ground_truth_effect": effect
            })
    
    df = pd.DataFrame(records)
    logger.log("generate_vr_logs_dataset", n_records=len(df), n_participants=n_participants)
    return df


def save_datasets(mfq_df: pd.DataFrame, stories_df: pd.DataFrame, logs_df: pd.DataFrame) -> Tuple[Path, Path]:
    """
    Save synthetic datasets to disk.
    
    Returns:
    - Path to synthetic_stories.csv
    - Path to synthetic_logs.csv
    """
    stories_path = get_path("data/processed/synthetic_stories.csv")
    logs_path = get_path("data/processed/synthetic_logs.csv")
    
    stories_df.to_csv(stories_path, index=False)
    logs_df.to_csv(logs_path, index=False)
    
    logger.log("save_datasets", stories_path=str(stories_path), logs_path=str(logs_path))
    return stories_path, logs_path


def update_artifact_hashes(stories_path: Path, logs_path: Path) -> None:
    """
    Calculate and update checksums for generated artifacts.
    """
    stories_hash = calculate_checksum(stories_path)
    logs_hash = calculate_checksum(logs_path)
    
    update_state_file(stories_path, stories_hash)
    update_state_file(logs_path, logs_hash)
    
    logger.log("update_artifact_hashes", stories_hash=stories_hash, logs_hash=logs_hash)


def run_simulation_pipeline() -> Tuple[Path, Path]:
    """
    Run the full simulation pipeline for stories and VR logs.
    
    Steps:
    1. Check MDES report (dependency T045-MDES-Calc)
    2. Generate moral stories dataset
    3. Generate VR logs dataset
    4. Save to disk
    5. Update artifact hashes
    
    Returns:
    - Path to synthetic_stories.csv
    - Path to synthetic_logs.csv
    """
    log_operation("START", "T014: Synthetic Stories and VR Logs Generation")
    
    # 1. Check MDES report
    try:
        mdes_report = load_mdes_report()
        n_required = mdes_report.get("n_required", N_CONFIG)
        logger.log("load_mdes_report", n_required=n_required)
    except FileNotFoundError as e:
        logger.log("ERROR", message=str(e))
        raise FileNotFoundError(
            "MDES report missing at state/mdes_report.yaml. "
            "Ensure T045-MDES-Calc is complete before running this task."
        ) from e
    
    # Use n_required or fallback to N_CONFIG
    n_participants = n_required if n_required > 0 else N_CONFIG
    logger.log("using_n_participants", n=n_participants)
    
    # 2. Generate moral stories dataset
    stories_df = generate_moral_stories_dataset(n_participants)
    
    # 3. Generate VR logs dataset
    logs_df = generate_vr_logs_dataset(n_participants)
    
    # 4. Save to disk
    stories_path, logs_path = save_datasets(pd.DataFrame(), stories_df, logs_df)
    
    # 5. Update artifact hashes
    update_artifact_hashes(stories_path, logs_path)
    
    log_operation("COMPLETE", "T014: Synthetic Stories and VR Logs Generation completed")
    return stories_path, logs_path


def main() -> None:
    """Main entry point for T014."""
    try:
        stories_path, logs_path = run_simulation_pipeline()
        print(f"Successfully generated:")
        print(f"  - {stories_path}")
        print(f"  - {logs_path}")
        
        # Verify columns
        logs_df = pd.read_csv(logs_path)
        required_columns = [
            "participant_id", "story_id", "salience_level", 
            "response_time", "gaze_metrics", "judgment_rating"
        ]
        missing = [col for col in required_columns if col not in logs_df.columns]
        if missing:
            raise ValueError(f"Missing required columns in synthetic_logs.csv: {missing}")
        
        print(f"Verification passed: All required columns present in {logs_path}")
        
    except Exception as e:
        logger.log("ERROR", message=str(e), error_type=type(e).__name__)
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()