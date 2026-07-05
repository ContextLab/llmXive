import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.config import ensure_directories, init_random_seeds
from code.utils.schema import SalienceLevel
from code.utils.logging_utils import log_pipeline_step

LOG_FILE = "data/logs/simulation_stories_log.txt"
STORIES_OUTPUT = "data/processed/synthetic_stories.csv"
VR_LOGS_OUTPUT = "data/processed/synthetic_vr_logs.csv"

# Ground truth effect size for validation (parameter recovery)
GROUND_TRUTH_SALIENCE_EFFECT = 0.8

def set_seed(seed: int = 42):
    """Set random seed for reproducibility."""
    np.random.seed(seed)

def generate_story_text(story_id: int, salience_level: SalienceLevel) -> str:
    """Generate a mock moral story text based on salience level."""
    templates_low = [
        "Person A made a decision that affected Person B.",
        "A situation occurred where resources were distributed.",
        "An individual faced a choice regarding social norms."
    ]
    templates_high = [
        f"Person A vividly witnessed a vivid event involving Person B, with intense emotional impact.",
        f"A highly detailed situation occurred where resources were distributed with clear moral implications.",
        f"An individual faced a critical choice regarding social norms, with strong visual cues present."
    ]
    
    templates = templates_high if salience_level == SalienceLevel.HIGH else templates_low
    return np.random.choice(templates)

def generate_moral_stories_dataset(n_stories: int = 200, n_participants: int = 500) -> pd.DataFrame:
    """
    Generate synthetic Moral Stories dataset.
    Each participant is assigned a subset of stories.
    """
    init_random_seeds()
    log_pipeline_step(f"Generating synthetic Moral Stories data", LOG_FILE)
    
    data = []
    story_ids = range(1, n_stories + 1)
    participant_ids = range(1, n_participants + 1)
    
    for story_id in story_ids:
        salience = np.random.choice([SalienceLevel.LOW, SalienceLevel.HIGH])
        text = generate_story_text(story_id, salience)
        
        # Assign this story to a random subset of participants (e.g., 50%)
        assigned_participants = np.random.choice(
            list(participant_ids), 
            size=int(n_participants * 0.5), 
            replace=False
        )
        
        for pid in assigned_participants:
            data.append({
                'participant_id': int(pid),
                'story_id': int(story_id),
                'story_text': text,
                'salience_level': salience.value
            })
    
    df = pd.DataFrame(data)
    log_pipeline_step(f"Generated {len(df)} story assignments", LOG_FILE)
    return df

def generate_vr_logs_dataset(stories_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate synthetic VR interaction logs with a known ground truth effect.
    The judgment score is influenced by salience_level.
    """
    init_random_seeds()
    log_pipeline_step("Generating synthetic VR logs data", LOG_FILE)
    
    data = []
    
    for _, row in stories_df.iterrows():
        # Simulate response time, gaze, and judgment
        salience = SalienceLevel(row['salience_level'])
        
        # Base judgment score (random)
        base_judgment = np.random.uniform(1, 7)
        
        # Apply ground truth effect
        if salience == SalienceLevel.HIGH:
            judgment = base_judgment + GROUND_TRUTH_SALIENCE_EFFECT
        else:
            judgment = base_judgment
        
        # Clip to Likert scale
        judgment = np.clip(judgment, 1, 7)
        
        # Simulate response time (lower for high salience)
        response_time = np.random.exponential(scale=2.0)
        if salience == SalienceLevel.HIGH:
            response_time *= 0.8
        
        # Simulate gaze fixation duration (higher for high salience)
        gaze_duration = np.random.normal(loc=2.5, scale=0.5)
        if salience == SalienceLevel.HIGH:
            gaze_duration += 0.5
        
        data.append({
            'participant_id': row['participant_id'],
            'story_id': row['story_id'],
            'response_time': round(response_time, 3),
            'gaze_duration': round(gaze_duration, 3),
            'judgment': round(judgment, 2)
        })
    
    df = pd.DataFrame(data)
    log_pipeline_step(f"Generated {len(df)} VR log records", LOG_FILE)
    return df

def save_datasets(stories_df: pd.DataFrame, vr_logs_df: pd.DataFrame):
    """Save generated datasets to CSV files."""
    stories_path = project_root / STORIES_OUTPUT
    vr_logs_path = project_root / VR_LOGS_OUTPUT
    
    stories_df.to_csv(stories_path, index=False)
    vr_logs_df.to_csv(vr_logs_path, index=False)
    
    log_pipeline_step(f"Stories saved to {stories_path}", LOG_FILE)
    log_pipeline_step(f"VR Logs saved to {vr_logs_path}", LOG_FILE)

def main():
    """Main entry point for Stories and VR logs simulation."""
    log_pipeline_step("Starting Stories & VR Logs Simulation (T014)", LOG_FILE)
    
    ensure_directories()
    
    try:
        stories_df = generate_moral_stories_dataset()
        vr_logs_df = generate_vr_logs_dataset(stories_df)
        save_datasets(stories_df, vr_logs_df)
        
        print(f"Successfully generated synthetic Stories and VR logs.")
        print(f"Stories shape: {stories_df.shape}")
        print(f"VR Logs shape: {vr_logs_df.shape}")
        return True
    except Exception as e:
        log_pipeline_step(f"Stories Simulation failed: {str(e)}", LOG_FILE)
        print(f"Error generating stories data: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
