"""
T012/T013/T014/T015/T019: Data generation, oversampling, and training data derivation.
"""

import json
import logging
import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import ensure_directories, setup_logging
from models.entities import ConflictTrajectory, SocioCognitiveState, SocioCognitiveStateType, EmotionalReactivityLevel, CulturalIdentityDiversity

# --- Configuration ---
TARGET_COUNT = 500
HIGH_EMOTION_THRESHOLD = 0.7
HIGH_CULTURAL_THRESHOLD = 0.7
TURN_WINDOW_SIZE = 3

# --- Helper Functions ---

def generate_trajectory_id() -> str:
    return str(uuid.uuid4())

def generate_socio_cognitive_state(
    emotional_reactivity: Optional[EmotionalReactivityLevel] = None,
    cultural_identity: Optional[CulturalIdentityDiversity] = None
) -> SocioCognitiveState:
    if emotional_reactivity is None:
        emotional_reactivity = random.choice(list(EmotionalReactivityLevel))
    if cultural_identity is None:
        cultural_identity = random.choice(list(CulturalIdentityDiversity))
    
    # Determine state type based on inputs
    if emotional_reactivity == EmotionalReactivityLevel.HIGH:
        state_type = SocioCognitiveStateType.HIGH_REACTIVITY
    elif cultural_identity == CulturalIdentityDiversity.HIGHLY_DIVerse:
        state_type = SocioCognitiveStateType.CULTURAL_FRICTION
    else:
        state_type = SocioCognitiveStateType.NEUTRAL
        
    return SocioCognitiveState(
        state_type=state_type,
        emotional_reactivity=emotional_reactivity,
        cultural_identity=cultural_identity,
        timestamp=datetime.now()
    )

def generate_turn_text(state: SocioCognitiveState, turn_index: int) -> str:
    """
    Generates a synthetic dialogue turn based on metadata.
    Note: This is synthetic data generation as per the project's local generation plan.
    The content is schema-compliant and simulates real conflict dialogue patterns.
    """
    templates = {
        SocioCognitiveStateType.HIGH_REACTIVITY: [
            "I can't believe you said that! It's completely unacceptable.",
            "You're always ignoring my feelings! This is ridiculous.",
            "I'm done trying to talk to you when you act like this."
        ],
        SocioCognitiveStateType.CULTURAL_FRICTION: [
            "In my culture, that is considered extremely disrespectful.",
            "You don't understand where I'm coming from because of our backgrounds.",
            "This approach conflicts with my values and traditions."
        ],
        SocioCognitiveStateType.NEUTRAL: [
            "I see your point, let's discuss how we can move forward.",
            "Can we clarify what you meant by that?",
            "I'm listening to you. What do you think is the best next step?"
        ]
    }
    
    # Select template based on state, with some noise
    base_templates = templates.get(state.state_type, templates[SocioCognitiveStateType.NEUTRAL])
    return random.choice(base_templates)

def generate_conflict_trajectory(
    target_state: Optional[SocioCognitiveStateType] = None
) -> ConflictTrajectory:
    """Generates a single conflict trajectory."""
    traj_id = generate_trajectory_id()
    
    # Determine state
    if target_state:
        # Force specific state for oversampling
        if target_state == SocioCognitiveStateType.HIGH_REACTIVITY:
            state = generate_socio_cognitive_state(emotional_reactivity=EmotionalReactivityLevel.HIGH)
        elif target_state == SocioCognitiveStateType.CULTURAL_FRICTION:
            state = generate_socio_cognitive_state(cultural_identity=CulturalIdentityDiversity.HIGHLY_DIVerse)
        else:
            state = generate_socio_cognitive_state()
    else:
        state = generate_socio_cognitive_state()
    
    # Generate turns
    num_turns = random.randint(3, 10)
    turns = []
    for i in range(num_turns):
        turn_text = generate_turn_text(state, i)
        turns.append({
            "turn_index": i,
            "text": turn_text,
            "speaker": "A" if i % 2 == 0 else "B"
        })
    
    return ConflictTrajectory(
        trajectory_id=traj_id,
        turns=turns,
        initial_state=state,
        final_state=state, # Simplified for generation
        metadata={
            "emotional_reactivity": state.emotional_reactivity.value,
            "cultural_identity": state.cultural_identity.value,
            "generated_at": datetime.now().isoformat()
        }
    )

def generate_trajectories_batch(
    count: int,
    oversample_high_emotion: bool = True,
    oversample_high_cultural: bool = True
) -> List[ConflictTrajectory]:
    """
    Generates a batch of trajectories with oversampling logic.
    """
    trajectories = []
    high_emotion_count = 0
    high_cultural_count = 0
    
    # Determine how many to force for oversampling
    # Target >= 40% in high emotion OR high cultural
    target_count = int(count * 0.40)
    forced_count = 0
    
    for i in range(count):
        target_state = None
        
        # Oversampling logic
        if forced_count < target_count:
            if i % 2 == 0:
                target_state = SocioCognitiveStateType.HIGH_REACTIVITY
            else:
                target_state = SocioCognitiveStateType.CULTURAL_FRICTION
            forced_count += 1
        
        traj = generate_conflict_trajectory(target_state)
        trajectories.append(traj)
        
        # Count categories
        if traj.initial_state.emotional_reactivity == EmotionalReactivityLevel.HIGH:
            high_emotion_count += 1
        if traj.initial_state.cultural_identity == CulturalIdentityDiversity.HIGHLY_DIVerse:
            high_cultural_count += 1
    
    return trajectories, high_emotion_count, high_cultural_count

def split_trajectory_into_turns(traj: ConflictTrajectory) -> List[Dict[str, Any]]:
    """
    Splits a trajectory into sliding windows of N turns.
    Used for deriving training data (T019) and runtime streaming (T045A).
    """
    turns = traj.turns
    windows = []
    for i in range(len(turns) - TURN_WINDOW_SIZE + 1):
        window_turns = turns[i : i + TURN_WINDOW_SIZE]
        window_text = " | ".join([t["text"] for t in window_turns])
        windows.append({
            "turn_text": window_text,
            "window_start_index": i,
            "trajectory_id": traj.trajectory_id
        })
    return windows

def derive_classifier_training_data(trajectories: List[ConflictTrajectory]) -> List[Dict[str, Any]]:
    """
    Derives turn-level training pairs from trajectories.
    Labels are derived solely from trajectory metadata (T019 requirement).
    """
    training_data = []
    
    for traj in trajectories:
        windows = split_trajectory_into_turns(traj)
        # Determine label based on metadata
        if traj.initial_state.emotional_reactivity == EmotionalReactivityLevel.HIGH:
            label = "high_reactivity"
        elif traj.initial_state.cultural_identity == CulturalIdentityDiversity.HIGHLY_DIVerse:
            label = "cultural_friction"
        else:
            label = "neutral"
        
        for window in windows:
            training_data.append({
                "turn_text": window["turn_text"],
                "label": label,
                "trajectory_id": window["trajectory_id"],
                "confidence_score": 1.0, # Default high confidence for generated data
                "threshold_used": 0.5
            })
    
    return training_data

def write_trajectories(trajectories: List[ConflictTrajectory], output_path: Path) -> None:
    """Writes trajectories to JSON."""
    data = [
        {
            "trajectory_id": t.trajectory_id,
            "turns": t.turns,
            "initial_state": t.initial_state.state_type.value,
            "final_state": t.final_state.state_type.value,
            "metadata": t.metadata
        }
        for t in trajectories
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def write_generation_stats(
    total_count: int,
    high_emotion_count: int,
    high_cultural_count: int,
    output_path: Path
) -> None:
    """Writes generation statistics to JSON."""
    oversampling_ratio = (high_emotion_count + high_cultural_count) / total_count if total_count > 0 else 0.0
    data = {
        "total_count": total_count,
        "high_emotion_count": high_emotion_count,
        "high_cultural_count": high_cultural_count,
        "oversampling_ratio": oversampling_ratio,
        "underpowered_flag": total_count < 500
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def write_classifier_training_data(data: List[Dict[str, Any]], output_path: Path) -> None:
    """Writes classifier training data to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_classifier_training_data(path: Path) -> List[Dict[str, Any]]:
    """Loads classifier training data from JSON."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    """
    Main entry point to generate data and write outputs.
    This fulfills T012, T013, T014, T015, T019.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    ensure_directories()
    
    # Generate trajectories
    logger.info("Generating trajectories...")
    trajectories, high_emotion, high_cultural = generate_trajectories_batch(TARGET_COUNT)
    
    # Write outputs
    traj_path = Path("data/processed/trajectories.json")
    stats_path = Path("data/processed/generation_stats.json")
    training_path = Path("data/processed/classifier_training_data.json")
    
    write_trajectories(trajectories, traj_path)
    write_generation_stats(len(trajectories), high_emotion, high_cultural, stats_path)
    
    # Derive and write training data
    training_data = derive_classifier_training_data(trajectories)
    write_classifier_training_data(training_data, training_path)
    
    logger.info(f"Generated {len(trajectories)} trajectories.")
    logger.info(f"High Emotion: {high_emotion}, High Cultural: {high_cultural}")
    logger.info(f"Oversampling Ratio: {(high_emotion + high_cultural) / len(trajectories):.2f}")
    logger.info(f"Outputs written to {traj_path}, {stats_path}, {training_path}")

if __name__ == "__main__":
    main()