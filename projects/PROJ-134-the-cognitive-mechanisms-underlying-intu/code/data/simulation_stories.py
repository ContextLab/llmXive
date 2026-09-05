"""
Synthetic Moral Stories and VR interaction logs generation.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import List, Dict

import numpy as np
import pandas as pd

from code.config import get_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(get_path("data/logs/simulation_stories.log"))
    ]
)
logger = logging.getLogger(__name__)

STORIES_OUTPUT_PATH = "data/raw/synthetic_stories.csv"
VR_LOGS_OUTPUT_PATH = "data/raw/synthetic_vr_logs.csv"

# Sample stories
STORY_TEMPLATES = [
    {"id": "S001", "text": "A person helps a stranger in need.", "moral_foundation": "care"},
    {"id": "S002", "text": "A person cheats on a test.", "moral_foundation": "fairness"},
    {"id": "S003", "text": "A person betrays their team.", "moral_foundation": "loyalty"},
    {"id": "S004", "text": "A person disrespects an elder.", "moral_foundation": "authority"},
    {"id": "S005", "text": "A person engages in unsanitary behavior.", "moral_foundation": "purity"},
    {"id": "S006", "text": "A person donates to charity.", "moral_foundation": "care"},
    {"id": "S007", "text": "A person steals from a store.", "moral_foundation": "fairness"},
    {"id": "S008", "text": "A person ignores a national holiday.", "moral_foundation": "loyalty"},
    {"id": "S009", "text": "A person insults a leader.", "moral_foundation": "authority"},
    {"id": "S010", "text": "A person eats something taboo.", "moral_foundation": "purity"},
]


def set_seed(seed: int = 42) -> None:
    """Set random seed for reproducibility."""
    np.random.seed(seed)


def generate_story_text(story_id: str) -> str:
    """Get the text for a given story ID."""
    for story in STORY_TEMPLATES:
        if story["id"] == story_id:
            return story["text"]
    return "Unknown story."


def generate_moral_stories_dataset(n_participants: int, n_stories: int = 10) -> pd.DataFrame:
    """
    Generate a dataset of moral story judgments.
    
    Args:
        n_participants: Number of participants
        n_stories: Number of stories per participant
        
    Returns:
        DataFrame with story judgments
    """
    records = []
    
    for p_id in range(1, n_participants + 1):
        for s_idx, story in enumerate(STORY_TEMPLATES[:n_stories]):
            # Simulate judgment rating (1-7 scale)
            base_rating = 4.0  # Neutral
            # Add some noise
            rating = np.clip(base_rating + np.random.normal(0, 1.0), 1, 7)
            
            records.append({
                "participant_id": p_id,
                "story_id": story["id"],
                "story_text": story["text"],
                "moral_foundation": story["moral_foundation"],
                "judgment_rating": round(rating, 2)
            })
    
    return pd.DataFrame(records)


def generate_vr_logs_dataset(stories_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate synthetic VR interaction logs.
    
    Args:
        stories_df: DataFrame with story judgments
        
    Returns:
        DataFrame with VR interaction logs
    """
    records = []
    
    for _, row in stories_df.iterrows():
        # Simulate response time (LogNormal distribution)
        response_time = np.random.lognormal(3.5, 0.5)
        
        # Simulate gaze metrics (Normal distribution)
        gaze_metrics = round(np.random.normal(0.5, 0.1), 3)
        
        # Assign salience level (50/50 split)
        salience_level = "high" if row["participant_id"] % 2 == 0 else "low"
        
        records.append({
            "participant_id": row["participant_id"],
            "story_id": row["story_id"],
            "response_time": round(response_time, 2),
            "gaze_metrics": gaze_metrics,
            "salience_level": salience_level,
            "judgment_rating": row["judgment_rating"]
        })
    
    return pd.DataFrame(records)


def save_datasets(stories_df: pd.DataFrame, vr_logs_df: pd.DataFrame) -> None:
    """Save the generated datasets to disk."""
    # Save stories
    stories_path = get_path(STORIES_OUTPUT_PATH)
    stories_path.parent.mkdir(parents=True, exist_ok=True)
    stories_df.to_csv(stories_path, index=False)
    logger.info(f"Saved {len(stories_df)} story records to {stories_path}")
    
    # Save VR logs
    vr_logs_path = get_path(VR_LOGS_OUTPUT_PATH)
    vr_logs_path.parent.mkdir(parents=True, exist_ok=True)
    vr_logs_df.to_csv(vr_logs_path, index=False)
    logger.info(f"Saved {len(vr_logs_df)} VR log records to {vr_logs_path}")


def main() -> None:
    """Main entry point for stories simulation."""
    try:
        logger.info("Starting synthetic stories and VR logs generation")
        
        set_seed(42)
        
        # Load MDES report for sample size
        import yaml
        mdes_path = get_path("state/mdes_report.yaml")
        if mdes_path.exists():
            with open(mdes_path, 'r') as f:
                mdes_report = yaml.safe_load(f)
            n_participants = mdes_report.get('n_participants', 200)
        else:
            n_participants = 200
            logger.warning("MDES report not found, using default N=200")
        
        # Generate datasets
        stories_df = generate_moral_stories_dataset(n_participants)
        vr_logs_df = generate_vr_logs_dataset(stories_df)
        
        # Save
        save_datasets(stories_df, vr_logs_df)
        
        logger.info("Stories and VR logs simulation completed successfully")
        
    except Exception as e:
        logger.error(f"Stories simulation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()