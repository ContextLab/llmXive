"""
T014: Generate synthetic Moral Stories and VR interaction logs with known ground truth effect.

This script generates synthetic data for the Moral Stories and VR Logs simulation.
It uses specific distributions:
  - response_time ~ LogNormal(3.5, 0.5)
  - gaze_metrics ~ Normal(0.5, 0.1)

It injects a known `ground_truth_effect` for parameter recovery analysis.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import yaml

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config import get_path, DATA_MODE
from code.utils.hashing import calculate_checksum, update_state_file
from code.utils.logging import log_operation, get_logger
from code.analysis.power_analysis import load_mdes_report

# Configure logger
logger = get_logger("simulation_stories")

# Constants
GROUND_TRUTH_EFFECT = 0.8  # Known effect size for parameter recovery
N_PARTICIPANTS = 100  # Default, will be overridden by MDES if available
STORY_COUNT = 10
RESPONSE_TIME_MEAN = 3.5
RESPONSE_TIME_STD = 0.5
GAZE_MEAN = 0.5
GAZE_STD = 0.1

# Story templates (simplified moral scenarios)
STORY_TEMPLATES = [
    "A person finds a wallet containing {amount} and decides to {action}.",
    "During a meeting, someone {action} regarding a critical decision.",
    "A team member {action} while the group was working on a shared goal.",
    "An individual {action} when no one was watching.",
    "A leader {action} affecting the entire organization.",
    "A friend {action} when you needed support the most.",
    "A stranger {action} in a public place.",
    "A colleague {action} during a high-pressure situation.",
    "A community member {action} that impacted everyone.",
    "A family member {action} during a difficult time."
]

ACTIONS = {
    "high_salience": [
        "returns it immediately to the owner",
        "publicly announces the truth",
        "takes responsibility for the mistake",
        "helps without being asked",
        "prioritizes the group's welfare",
        "supports you unconditionally",
        "stands up for what is right",
        "admits the error and fixes it",
        "contributes generously to the cause",
        "protects the vulnerable"
    ],
    "low_salience": [
        "keeps it for themselves",
        "remains silent about the issue",
        "shifts blame to others",
        "ignores the request for help",
        "prioritizes personal gain",
        "abandons you when needed",
        "looks the other way",
        "denies the error occurred",
        "withholds resources",
        "prioritizes self over community"
    ]
}

def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    np.random.seed(seed)
    logger.log("set_seed", seed=seed)

def load_mdes_report() -> Dict[str, Any]:
    """Load the MDES report to determine required sample size."""
    mdes_path = get_path("state", "mdes_report.yaml")
    if not os.path.exists(mdes_path):
        logger.log("load_mdes_report", status="failed", message="MDES report not found")
        # Fallback to default if MDES report is missing, but log warning
        logger.log("load_mdes_report", status="warning", message="Using default N_PARTICIPANTS")
        return {"n_required": N_PARTICIPANTS}
    
    with open(mdes_path, 'r') as f:
        return yaml.safe_load(f)

def validate_ground_truth_effect(effect: float) -> None:
    """Validate that the ground truth effect is within reasonable bounds."""
    if not (0.0 <= effect <= 2.0):
        raise ValueError(f"Ground truth effect {effect} is outside reasonable bounds [0.0, 2.0]")

def load_blend_shape_config() -> Dict[str, Any]:
    """Load the Unity blend shape configuration."""
    config_path = get_path("data", "config/unity_blend_shapes.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Blend shape config not found at {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def generate_story_text(story_id: int, salience_level: str) -> str:
    """Generate a story text based on the story ID and salience level."""
    template = STORY_TEMPLATES[story_id % len(STORY_TEMPLATES)]
    action_list = ACTIONS[salience_level]
    action = action_list[story_id % len(action_list)]
    
    if "{amount}" in template:
        amount = np.random.randint(10, 1000)
        return template.format(amount=amount, action=action)
    else:
        return template.format(action=action)

def determine_salience_level(story_id: int) -> str:
    """Determine salience level based on story ID (alternating for balance)."""
    return "high" if story_id % 2 == 0 else "low"

def generate_moral_stories_dataset(n_participants: int) -> pd.DataFrame:
    """Generate synthetic moral stories dataset."""
    logger.log("generate_moral_stories_dataset", n_participants=n_participants)
    
    data = []
    for i in range(n_participants):
        for j in range(STORY_COUNT):
            story_id = i * STORY_COUNT + j
            salience = determine_salience_level(story_id)
            story_text = generate_story_text(j, salience)
            
            data.append({
                "participant_id": f"P{i+1:03d}",
                "story_id": f"S{j+1:03d}",
                "salience_level": salience,
                "story_text": story_text
            })
    
    return pd.DataFrame(data)

def generate_vr_logs_dataset(stories_df: pd.DataFrame) -> pd.DataFrame:
    """Generate synthetic VR interaction logs dataset with known effect."""
    logger.log("generate_vr_logs_dataset", n_records=len(stories_df))
    
    data = []
    for _, row in stories_df.iterrows():
        salience = row["salience_level"]
        
        # Generate response_time ~ LogNormal(3.5, 0.5)
        # Note: For high salience, we might expect faster response times (lower mean)
        # but we keep the distribution consistent as per spec, adding effect via judgment
        rt_mean = RESPONSE_TIME_MEAN
        if salience == "high":
            # Slight adjustment to simulate effect, but keep distribution shape
            rt_mean = RESPONSE_TIME_MEAN - 0.2 
        response_time = np.random.lognormal(mean=rt_mean, sigma=RESPONSE_TIME_STD)
        
        # Generate gaze_metrics ~ Normal(0.5, 0.1)
        gaze_mean = GAZE_MEAN
        if salience == "high":
            gaze_mean = GAZE_MEAN + 0.05
        gaze_metrics = np.random.normal(loc=gaze_mean, scale=GAZE_STD)
        gaze_metrics = max(0.0, min(1.0, gaze_metrics))  # Clamp to [0, 1]
        
        # Generate judgment_rating based on ground truth effect
        # High salience -> higher judgment rating (more moral)
        base_rating = 3.0
        if salience == "high":
            judgment_rating = base_rating + GROUND_TRUTH_EFFECT + np.random.normal(0, 0.5)
        else:
            judgment_rating = base_rating + np.random.normal(0, 0.5)
        judgment_rating = max(1.0, min(5.0, judgment_rating))  # Clamp to [1, 5]
        
        data.append({
            "participant_id": row["participant_id"],
            "story_id": row["story_id"],
            "salience_level": salience,
            "response_time": round(response_time, 4),
            "gaze_metrics": round(gaze_metrics, 4),
            "judgment_rating": round(judgment_rating, 2),
            "ground_truth_effect": GROUND_TRUTH_EFFECT
        })
    
    return pd.DataFrame(data)

def save_datasets(stories_df: pd.DataFrame, logs_df: pd.DataFrame) -> None:
    """Save generated datasets to disk."""
    stories_path = get_path("data", "processed/synthetic_stories.csv")
    logs_path = get_path("data", "processed/synthetic_logs.csv")
    
    logger.log("save_datasets", stories_path=str(stories_path), logs_path=str(logs_path))
    
    stories_df.to_csv(stories_path, index=False)
    logs_df.to_csv(logs_path, index=False)
    
    logger.log("save_datasets", status="success", stories_count=len(stories_df), logs_count=len(logs_df))

def update_artifact_hashes() -> None:
    """Update artifact hashes for the generated files."""
    files_to_hash = [
        get_path("data", "processed/synthetic_stories.csv"),
        get_path("data", "processed/synthetic_logs.csv")
    ]
    
    for file_path in files_to_hash:
        if os.path.exists(file_path):
            checksum = calculate_checksum(file_path)
            update_state_file(file_path, checksum)
            logger.log("update_artifact_hashes", file=str(file_path), checksum=checksum)

def run_simulation_pipeline() -> pd.DataFrame:
    """Run the full simulation pipeline."""
    logger.log("run_simulation_pipeline", status="start")
    
    # Validate mode
    if DATA_MODE != "simulation":
        # In real mode, we should not be generating synthetic data
        # But for T014, we are explicitly in simulation validation
        logger.log("run_simulation_pipeline", status="warning", message="DATA_MODE is not simulation")
    
    # Load MDES report to determine sample size
    mdes_report = load_mdes_report()
    n_participants = mdes_report.get("n_required", N_PARTICIPANTS)
    logger.log("run_simulation_pipeline", n_participants=n_participants)
    
    # Validate ground truth effect
    validate_ground_truth_effect(GROUND_TRUTH_EFFECT)
    
    # Set seed for reproducibility
    set_seed(42)
    
    # Generate datasets
    stories_df = generate_moral_stories_dataset(n_participants)
    logs_df = generate_vr_logs_dataset(stories_df)
    
    # Save datasets
    save_datasets(stories_df, logs_df)
    
    # Update hashes
    update_artifact_hashes()
    
    logger.log("run_simulation_pipeline", status="complete")
    return logs_df

def main() -> None:
    """Main entry point."""
    try:
        logger.log("main", status="start")
        logs_df = run_simulation_pipeline()
        
        # Verify output
        output_path = get_path("data", "processed/synthetic_logs.csv")
        if os.path.exists(output_path):
            logger.log("main", status="success", output_path=str(output_path))
            # Verify columns
            expected_cols = ["participant_id", "story_id", "salience_level", "response_time", "gaze_metrics", "judgment_rating", "ground_truth_effect"]
            if all(col in logs_df.columns for col in expected_cols):
                logger.log("main", status="verified", columns=expected_cols)
            else:
                logger.log("main", status="error", message=f"Missing columns. Expected: {expected_cols}, Found: {list(logs_df.columns)}")
        else:
            logger.log("main", status="error", message=f"Output file not found: {output_path}")
            
    except Exception as e:
        logger.log("main", status="failed", error=str(e))
        raise

if __name__ == "__main__":
    main()
