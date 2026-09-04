"""
Simulation of Moral Stories and VR Interaction Logs (T014).

Generates synthetic datasets with a known ground_truth_effect for parameter recovery.
Produces:
  - data/processed/synthetic_stories.csv (Moral Stories text and metadata)
  - data/processed/synthetic_logs.csv (VR Interaction logs with gaze/response time)

This module implements the simulation path for User Story 1.
"""
from __future__ import annotations

import logging
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd

# Import project utilities
from code.config import get_path, init_random_seeds, validate_data_mode
from code.utils.logging import log_operation, get_logger
from code.utils.schema import SalienceLevel

# Constants
NUM_STORIES = 10
GROUND_TRUTH_EFFECT_SIZE = 0.8  # Cohen's d for salience effect
BASE_RESPONSE_TIME_MS = 2500.0
BASE_GAZE_METRICS = {"fixations": 12, "saccades": 45, "pupil_dilation_mm": 3.2}

# Story Templates (Simplified for simulation)
STORY_TEMPLATES = [
    {
        "id": "story_001",
        "text": "A person finds a wallet full of cash on the street. They decide to return it to the owner.",
        "moral_foundation": "fairness",
        "baseline_judgment": 7.5
    },
    {
        "id": "story_002",
        "text": "A soldier disobeys a direct order to save a civilian's life during a conflict.",
        "moral_foundation": "loyalty",
        "baseline_judgment": 6.0
    },
    {
        "id": "story_003",
        "text": "A doctor performs a life-saving surgery on a patient who cannot consent.",
        "moral_foundation": "care",
        "baseline_judgment": 8.0
    },
    {
        "id": "story_004",
        "text": "A community leader enforces a strict dress code based on tradition.",
        "moral_foundation": "authority",
        "baseline_judgment": 5.5
    },
    {
        "id": "story_005",
        "text": "A person refuses to eat a meal prepared with ingredients they consider unclean.",
        "moral_foundation": "purity",
        "baseline_judgment": 4.5
    },
    {
        "id": "story_006",
        "text": "A neighbor helps another neighbor move house without being asked.",
        "moral_foundation": "care",
        "baseline_judgment": 7.8
    },
    {
        "id": "story_007",
        "text": "A company CEO pays all employees the same wage regardless of role.",
        "moral_foundation": "fairness",
        "baseline_judgment": 6.5
    },
    {
        "id": "story_008",
        "text": "A family gathers for a traditional holiday meal despite disagreements.",
        "moral_foundation": "loyalty",
        "baseline_judgment": 7.0
    },
    {
        "id": "story_009",
        "text": "A student studies hard to honor their parents' expectations.",
        "moral_foundation": "authority",
        "baseline_judgment": 6.8
    },
    {
        "id": "story_010",
        "text": "A person avoids touching something they perceive as contaminated.",
        "moral_foundation": "purity",
        "baseline_judgment": 5.0
    }
]

def set_seed(seed: int = 42) -> None:
    """Initialize random seeds for reproducibility."""
    init_random_seeds(seed)

def generate_story_text(story_id: str, salience_level: str) -> str:
    """
    Generate a story text string.
    In simulation, we use the template text. In a full system, this might render VR text.
    """
    template = next((s for s in STORY_TEMPLATES if s["id"] == story_id), None)
    if not template:
        return f"Generic story for {story_id}"
    
    base_text = template["text"]
    # Add salience context to text if high salience
    if salience_level == SalienceLevel.HIGH:
        context = " [High Salience: Visual cues emphasized]"
    else:
        context = " [Low Salience: Subtle cues]"
    
    return base_text + context

def generate_moral_stories_dataset(
    n_participants: int, 
    salience_levels: List[str]
) -> pd.DataFrame:
    """
    Generate the Moral Stories dataset.
    
    Args:
        n_participants: Number of participants.
        salience_levels: List of salience levels to assign.
        
    Returns:
        DataFrame with columns: participant_id, story_id, salience_level, story_text, moral_foundation
    """
    data = []
    story_ids = [s["id"] for s in STORY_TEMPLATES]
    
    for i in range(n_participants):
        # Assign story (cyclic or random)
        story_id = story_ids[i % len(story_ids)]
        salience = salience_levels[i % len(salience_levels)]
        
        template = next(s for s in STORY_TEMPLATES if s["id"] == story_id)
        
        data.append({
            "participant_id": f"P{i+1:04d}",
            "story_id": story_id,
            "salience_level": salience,
            "story_text": generate_story_text(story_id, salience),
            "moral_foundation": template["moral_foundation"],
            "baseline_judgment": template["baseline_judgment"]
        })
    
    return pd.DataFrame(data)

def generate_vr_logs_dataset(
    stories_df: pd.DataFrame,
    ground_truth_effect: float
) -> pd.DataFrame:
    """
    Generate VR Interaction Logs with injected ground_truth_effect.
    
    The effect is injected into response_time and judgment_rating based on salience.
    High salience -> Faster response (lower RT) and higher judgment for positive acts.
    
    Args:
        stories_df: The stories dataframe.
        ground_truth_effect: The effect size (Cohen's d) to inject.
        
    Returns:
        DataFrame with columns: participant_id, story_id, salience_level, 
        response_time, gaze_metrics, judgment_rating
    """
    logs = []
    
    for _, row in stories_df.iterrows():
        participant_id = row["participant_id"]
        story_id = row["story_id"]
        salience = row["salience_level"]
        baseline_judgment = row["baseline_judgment"]
        
        # Determine effect direction: High salience generally increases moral intensity
        is_high_salience = (salience == SalienceLevel.HIGH)
        
        # Inject effect on Response Time (ms)
        # High salience -> faster processing -> lower RT
        # Effect size logic: RT = Base - (Effect * SD)
        rt_noise = np.random.normal(0, 300) # 300ms std dev
        effect_impact = ground_truth_effect * 400 # 400ms shift per unit d
        response_time = BASE_RESPONSE_TIME_MS - (effect_impact if is_high_salience else 0) + rt_noise
        
        # Inject effect on Judgment Rating (1-10)
        # High salience -> stronger judgment (higher or lower depending on valence, assuming positive here)
        judgment_noise = np.random.normal(0, 0.5)
        judgment_shift = ground_truth_effect * 1.5 # 1.5 point shift per unit d
        judgment_rating = baseline_judgment + (judgment_shift if is_high_salience else 0) + judgment_noise
        judgment_rating = np.clip(judgment_rating, 1.0, 10.0)
        
        # Generate Gaze Metrics (simulated based on RT and Salience)
        # High salience -> more fixations, longer dwell time
        base_fixations = 12
        fixations = int(base_fixations + (3 if is_high_salience else 0) + np.random.normal(0, 1))
        fixations = max(1, fixations)
        
        base_saccades = 45
        saccades = int(base_saccades + (10 if is_high_salience else 0) + np.random.normal(0, 3))
        saccades = max(1, saccades)
        
        pupil_dilation = 3.2 + (0.4 if is_high_salience else 0) + np.random.normal(0, 0.1)
        
        gaze_metrics = {
            "fixations": fixations,
            "saccades": saccades,
            "pupil_dilation_mm": round(pupil_dilation, 2)
        }
        
        logs.append({
            "participant_id": participant_id,
            "story_id": story_id,
            "salience_level": salience,
            "response_time": round(response_time, 2),
            "gaze_metrics": json.dumps(gaze_metrics),
            "judgment_rating": round(judgment_rating, 2)
        })
    
    return pd.DataFrame(logs)

def save_datasets(stories_df: pd.DataFrame, logs_df: pd.DataFrame) -> Tuple[Path, Path]:
    """
    Save the generated datasets to disk.
    
    Returns:
        Tuple of (stories_path, logs_path)
    """
    stories_path = get_path("data/processed/synthetic_stories.csv")
    logs_path = get_path("data/processed/synthetic_logs.csv")
    
    # Ensure directory exists
    stories_path.parent.mkdir(parents=True, exist_ok=True)
    
    stories_df.to_csv(stories_path, index=False)
    logs_df.to_csv(logs_path, index=False)
    
    return stories_path, logs_path

def main() -> None:
    """Main entry point for T014."""
    logger = get_logger("simulation_stories")
    
    log_operation("START", "T014: Synthetic Stories and VR Logs Generation")
    
    # Configuration
    N_PARTICIPANTS = 100
    SALIENCE_LEVELS = [SalienceLevel.LOW, SalienceLevel.HIGH]
    
    try:
        set_seed(42)
        
        # Generate Stories
        stories_df = generate_moral_stories_dataset(N_PARTICIPANTS, SALIENCE_LEVELS)
        
        # Generate VR Logs with Ground Truth Effect
        logs_df = generate_vr_logs_dataset(stories_df, GROUND_TRUTH_EFFECT_SIZE)
        
        # Save
        stories_path, logs_path = save_datasets(stories_df, logs_df)
        
        log_operation(
            "COMPLETE", 
            "T014: Generation finished",
            output_stories=str(stories_path),
            output_logs=str(logs_path),
            n_participants=N_PARTICIPANTS,
            ground_truth_effect=GROUND_TRUTH_EFFECT_SIZE
        )
        
        print(f"Generated {len(stories_df)} story records at {stories_path}")
        print(f"Generated {len(logs_df)} VR log records at {logs_path}")
        
    except Exception as e:
        log_operation("ERROR", "T014: Generation failed", error=str(e))
        raise

if __name__ == "__main__":
    main()