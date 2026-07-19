"""
Simulate Moral Stories and VR interaction logs for pipeline validation.

This module generates synthetic data with a known ground truth effect to validate
the pipeline architecture. It does NOT fetch real data; that is handled by Phase 4.

Authorization: Staged Implementation (Phase 3) - Simulation-Only
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Import from project utils
from code.config import get_path, ensure_directories, init_random_seeds
from code.utils.schema import MoralStory, MoralStoriesDataset, VRInteractionLog, VRLogsDataset, SalienceLevel
from code.utils.logging import get_logger, log_pipeline_step

# Constants for simulation
N_STORIES = 50
N_PARTICIPANTS = 200
GROUND_TRUTH_EFFECT = 0.8  # Known effect size for validation
RANDOM_SEED = 42

logger = get_logger(__name__)

def set_seed(seed: int = RANDOM_SEED) -> None:
    """Set random seed for reproducibility."""
    np.random.seed(seed)

def generate_story_text(story_id: int) -> str:
    """
    Generate a synthetic moral story text.
    
    Uses a deterministic template based on story_id to ensure reproducibility,
    rather than random noise.
    """
    themes = ["honesty", "loyalty", "fairness", "care", "authority", "purity"]
    violations = ["theft", "deception", "harm", "disrespect", "betrayal", "contamination"]
    
    theme = themes[story_id % len(themes)]
    violation = violations[story_id % len(violations)]
    
    template = (
        f"Story {story_id}: In a scenario involving {theme}, "
        f"a character committed an act of {violation}. "
        f"The context suggests the action was intentional and had significant consequences. "
        f"Participants must evaluate the moral wrongness of this action."
    )
    return template

def generate_moral_stories_dataset(n_stories: int = N_STORIES) -> pd.DataFrame:
    """
    Generate the Moral Stories dataset.
    
    Creates a DataFrame with story_id, text, and ground truth labels.
    """
    set_seed()
    
    stories = []
    for i in range(n_stories):
        story = {
            "story_id": f"story_{i:03d}",
            "text": generate_story_text(i),
            "theme": ["honesty", "loyalty", "fairness", "care", "authority", "purity"][i % 6],
            "ground_truth_wrongness": np.random.normal(5.0, 1.0)  # Base wrongness score
        }
        stories.append(story)
    
    df = pd.DataFrame(stories)
    logger.info(f"Generated {len(df)} moral stories")
    return df

def generate_vr_logs_dataset(
    stories_df: pd.DataFrame,
    n_participants: int = N_PARTICIPANTS,
    ground_truth_effect: float = GROUND_TRUTH_EFFECT
) -> pd.DataFrame:
    """
    Generate VR interaction logs with a known ground truth effect.
    
    Simulates:
    - Response times (log-normal distribution)
    - Gaze coordinates (normal distribution)
    - Judgment ratings (influenced by salience and ground truth)
    
    The 'salience_level' is assigned deterministically based on story_id to
    create the known effect for validation.
    """
    set_seed()
    
    logs = []
    n_stories = len(stories_df)
    
    for p_id in range(n_participants):
        participant_id = f"p_{p_id:03d}"
        
        for _, story_row in stories_df.iterrows():
            story_id = story_row["story_id"]
            story_num = int(story_id.split("_")[1])
            
            # Deterministic salience assignment: even IDs = high salience, odd = low
            # This creates a clear, known effect for validation
            salience_level = "high" if story_num % 2 == 0 else "low"
            
            # Generate response time (log-normal)
            response_time = np.random.lognormal(mean=3.0, sigma=0.5)
            
            # Generate gaze coordinates
            gaze_x = np.random.normal(0.5, 0.1)
            gaze_y = np.random.normal(0.5, 0.1)
            
            # Base judgment from story + noise
            base_judgment = story_row["ground_truth_wrongness"]
            
            # Apply known ground truth effect based on salience
            if salience_level == "high":
                judgment = base_judgment + ground_truth_effect + np.random.normal(0, 0.5)
            else:
                judgment = base_judgment + np.random.normal(0, 0.5)
            
            # Clamp judgment to [1, 7] scale
            judgment = np.clip(judgment, 1.0, 7.0)
            
            log_entry = {
                "participant_id": participant_id,
                "story_id": story_id,
                "response_time": response_time,
                "gaze_x": gaze_x,
                "gaze_y": gaze_y,
                "judgment_rating": judgment,
                "salience_level": salience_level
            }
            logs.append(log_entry)
    
    df = pd.DataFrame(logs)
    logger.info(f"Generated {len(df)} VR interaction logs for {n_participants} participants")
    return df

def save_datasets(stories_df: pd.DataFrame, vr_logs_df: pd.DataFrame) -> Tuple[Path, Path]:
    """
    Save the generated datasets to disk.
    
    Returns paths to the saved files.
    """
    ensure_directories()
    
    stories_path = get_path("data/raw/synthetic_stories.csv")
    logs_path = get_path("data/raw/synthetic_vr_logs.csv")
    
    stories_df.to_csv(stories_path, index=False)
    vr_logs_df.to_csv(logs_path, index=False)
    
    logger.info(f"Saved stories to {stories_path}")
    logger.info(f"Saved VR logs to {logs_path}")
    
    return stories_path, logs_path

def main() -> None:
    """Main entry point for simulation."""
    init_random_seeds()
    log_pipeline_step("Starting Moral Stories and VR Logs simulation")
    
    # Generate datasets
    stories_df = generate_moral_stories_dataset()
    vr_logs_df = generate_vr_logs_dataset(stories_df)
    
    # Validate schemas (basic check)
    assert "story_id" in stories_df.columns
    assert "text" in stories_df.columns
    assert "participant_id" in vr_logs_df.columns
    assert "response_time" in vr_logs_df.columns
    assert "judgment_rating" in vr_logs_df.columns
    assert "salience_level" in vr_logs_df.columns
    
    # Save to disk
    stories_path, logs_path = save_datasets(stories_df, vr_logs_df)
    
    log_pipeline_step(
        f"Simulation complete. Files: {stories_path}, {logs_path}",
        status="success"
    )
    
    print(f"Generated: {stories_path}")
    print(f"Generated: {logs_path}")

if __name__ == "__main__":
    main()