"""
T014: Simulation of Moral Stories and VR Interaction Logs.

Generates synthetic Moral Stories and VR interaction logs with a known ground_truth_effect.
Distributions:
  - response_time ~ LogNormal(3.5, 0.5)
  - gaze_metrics ~ Normal(0.5, 0.1)
Output: data/processed/synthetic_logs.csv
"""
from __future__ import annotations

import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

# Local imports from project API
from code.config import get_path
from code.utils.hashing import calculate_checksum, update_state_file
from code.utils.logging import log_operation, get_logger

# Constants
GROUND_TRUTH_EFFECT = 0.45  # Injected effect size for parameter recovery (T027c)
N_PARTICIPANTS = 100
N_STORIES = 10
SEED = 42

logger = get_logger(__name__)


def set_seed(seed: int = SEED) -> None:
    """Set random seed for reproducibility."""
    np.random.seed(seed)
    logging.getLogger(__name__).info(f"Random seed set to {seed}")


def generate_story_text(story_id: int) -> str:
    """
    Generate a synthetic story text based on the story_id.
    In a real scenario, this would load from a corpus. Here we simulate content.
    """
    templates = [
        "In a virtual environment, {person} encountered a situation where {action}.",
        "The scenario involved {person} making a decision about {action} under pressure.",
        "Observers noted that {person} reacted to {action} with {emotion}.",
        "A moral dilemma arose when {person} had to choose between {option1} and {option2}.",
        "The virtual agent {person} displayed {emotion} while performing {action}."
    ]
    
    subjects = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
    actions = ["helping a stranger", "stealing resources", "sharing information", "ignoring a plea", "betraying a friend"]
    emotions = ["fear", "anger", "compassion", "indifference", "joy"]
    options = ["safety", "duty", "loyalty", "fairness", "purity"]

    template = templates[story_id % len(templates)]
    data = {
        "person": subjects[story_id % len(subjects)],
        "action": actions[story_id % len(actions)],
        "emotion": emotions[story_id % len(emotions)],
        "option1": options[story_id % len(options)],
        "option2": options[(story_id + 1) % len(options)]
    }
    
    return template.format(**data)


def determine_salience_level(story_id: int) -> str:
    """
    Determine salience level (low/high) based on story_id and blend shape config.
    For simulation, we alternate or use a deterministic mapping.
    """
    # Load config to ensure mapping exists (T044 dependency)
    config_path = get_path("data/config/unity_blend_shapes.yaml")
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        # If config exists, we can map story_id to a level. 
        # For simplicity in simulation, we use modulo.
        return "low" if story_id % 2 == 0 else "high"
    else:
        # Fallback if config missing (should not happen if T044 done)
        return "low" if story_id % 2 == 0 else "high"


def generate_moral_stories_dataset(n_participants: int = N_PARTICIPANTS, 
                                   n_stories: int = N_STORIES) -> pd.DataFrame:
    """
    Generate the Moral Stories dataset.
    Columns: participant_id, story_id, story_text, salience_level
    """
    data = []
    for p_id in range(n_participants):
        for s_id in range(n_stories):
            salience = determine_salience_level(s_id)
            text = generate_story_text(s_id)
            data.append({
                "participant_id": f"P{p_id:03d}",
                "story_id": f"S{s_id:02d}",
                "story_text": text,
                "salience_level": salience
            })
    
    df = pd.DataFrame(data)
    logger.info(f"Generated {len(df)} story records.")
    return df


def generate_vr_logs_dataset(stories_df: pd.DataFrame, ground_truth_effect: float = GROUND_TRUTH_EFFECT) -> pd.DataFrame:
    """
    Generate VR interaction logs based on the stories dataset.
    
    Distributions:
      - response_time ~ LogNormal(3.5, 0.5)
      - gaze_metrics ~ Normal(0.5, 0.1)
    
    Injects a ground_truth_effect into judgment_rating based on salience_level.
    """
    logs = []
    
    for _, row in stories_df.iterrows():
        p_id = row["participant_id"]
        s_id = row["story_id"]
        salience = row["salience_level"]
        
        # 1. Response Time: LogNormal(3.5, 0.5)
        rt = np.random.lognormal(mean=3.5, sigma=0.5)
        
        # 2. Gaze Metrics: Normal(0.5, 0.1)
        gaze = np.random.normal(loc=0.5, scale=0.1)
        
        # 3. Judgment Rating: Base + Effect * Salience + Noise
        # Salience High (1) adds effect, Low (0) adds nothing.
        base_rating = 3.0  # Neutral rating on a 1-5 scale
        effect_val = ground_truth_effect if salience == "high" else 0.0
        noise = np.random.normal(loc=0.0, scale=0.5)
        rating = base_rating + effect_val + noise
        rating = np.clip(rating, 1.0, 5.0) # Clamp to 1-5
        
        logs.append({
            "participant_id": p_id,
            "story_id": s_id,
            "salience_level": salience,
            "response_time": round(rt, 4),
            "gaze_metrics": round(gaze, 4),
            "judgment_rating": round(rating, 4)
        })
    
    df_logs = pd.DataFrame(logs)
    logger.info(f"Generated {len(df_logs)} VR log records with ground_truth_effect={ground_truth_effect}.")
    return df_logs


def save_datasets(stories_df: pd.DataFrame, logs_df: pd.DataFrame) -> Tuple[str, str]:
    """
    Save the generated datasets to disk.
    Returns paths to the saved files.
    """
    # Ensure output directory exists
    output_dir = get_path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save Stories (optional, but good for completeness)
    stories_path = output_dir / "synthetic_stories.csv"
    stories_df.to_csv(stories_path, index=False)
    logger.info(f"Saved stories to {stories_path}")
    
    # Save Logs (Main Deliverable for T014)
    logs_path = output_dir / "synthetic_logs.csv"
    logs_df.to_csv(logs_path, index=False)
    logger.info(f"Saved logs to {logs_path}")
    
    return str(stories_path), str(logs_path)


def update_artifact_hashes(logs_path: str) -> None:
    """Calculate checksum and update state/artifact_hashes.yaml."""
    checksum = calculate_checksum(logs_path)
    update_state_file(logs_path, checksum)
    logger.info(f"Updated artifact hash for {logs_path}: {checksum[:16]}...")


def run_simulation_pipeline() -> None:
    """
    Main pipeline execution for T014.
    1. Set seed
    2. Generate Stories
    3. Generate VR Logs (injecting effect)
    4. Save to CSV
    5. Update Hashes
    """
    log_operation("T014_START", parameters={"n_participants": N_PARTICIPANTS, "n_stories": N_STORIES})
    
    try:
        # 1. Seed
        set_seed(SEED)
        
        # 2. Generate Stories
        stories_df = generate_moral_stories_dataset()
        
        # 3. Generate Logs
        logs_df = generate_vr_logs_dataset(stories_df, GROUND_TRUTH_EFFECT)
        
        # 4. Save
        stories_path, logs_path = save_datasets(stories_df, logs_df)
        
        # 5. Hash
        update_artifact_hashes(logs_path)
        
        log_operation("T014_COMPLETE", parameters={"output_file": logs_path, "effect_size": GROUND_TRUTH_EFFECT})
        
    except Exception as e:
        log_operation("T014_FAILED", parameters={"error": str(e)})
        raise


def main() -> None:
    """Entry point for script execution."""
    run_simulation_pipeline()


if __name__ == "__main__":
    main()