"""
Data Generation Module for Dynamic Socio-Cognitive State Injection.

This module generates synthetic conflict dialogue trajectories using the SoCRATES pipeline,
with specific oversampling of scenarios with "high emotional reactivity" and "diverse cultural identity" attributes.
It also derives turn-level training pairs for the classifier from these trajectories.

IMPORTANT: This module generates synthetic data for the purpose of simulating conflict scenarios
as defined in the research protocol. It does not use real-world private data.
"""
import json
import logging
import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import ensure_directories, get_config_summary
from models.entities import (
    ConflictTrajectory,
    SocioCognitiveState,
    SocioCognitiveStateType,
    EmotionalReactivityLevel,
    CulturalIdentityDiversity
)

logger = logging.getLogger(__name__)

# Configuration Constants
NUM_TURNS_PER_TRAJECTORY = 10
TURN_WINDOW_SIZE = 3  # Used for sliding window derivation in T019
TARGET_SAMPLE_SIZE = 500

# Templates for synthetic dialogue generation
DIALOGUE_TEMPLATES = {
    "high_reactivity": [
        "I can't believe you would say something so insensitive!",
        "This is exactly the kind of behavior I was worried about.",
        "You're completely missing the point here!",
        "I'm getting frustrated with this conversation.",
        "Why do you always have to be so dismissive?"
    ],
    "cultural_friction": [
        "In my culture, we would never approach it that way.",
        "I think there's a misunderstanding of the norms here.",
        "That comment feels disrespectful to my background.",
        "We have different expectations about this situation.",
        "I'm not sure we're interpreting this the same way."
    ],
    "neutral": [
        "Let's try to understand each other's perspective.",
        "I see your point, let me think about that.",
        "Perhaps we can find common ground here.",
        "I appreciate you sharing your view.",
        "Let's continue discussing this constructively."
    ]
}

def generate_trajectory_id() -> str:
    """Generate a unique identifier for a trajectory."""
    return str(uuid.uuid4())

def generate_turn_text(metadata: Dict[str, Any]) -> str:
    """
    Generates a synthetic dialogue turn based on metadata tags.
    
    Args:
        metadata: Dictionary containing emotional_reactivity and cultural_identity tags.
        
    Returns:
        A string representing a dialogue turn.
    """
    reactivity = metadata.get("emotional_reactivity", EmotionalReactivityLevel.LOW)
    cultural = metadata.get("cultural_identity", CulturalIdentityDiversity.HOMOGENEOUS)
    
    # Select template based on metadata to ensure schema compliance
    if reactivity == EmotionalReactivityLevel.HIGH:
        pool = DIALOGUE_TEMPLATES["high_reactivity"]
    elif cultural == CulturalIdentityDiversity.DIVERSE:
        pool = DIALOGUE_TEMPLATES["cultural_friction"]
    else:
        pool = DIALOGUE_TEMPLATES["neutral"]
        
    return random.choice(pool)

def generate_socio_cognitive_state(
    emotional_reactivity: EmotionalReactivityLevel,
    cultural_identity: CulturalIdentityDiversity
) -> SocioCognitiveState:
    """
    Generate a socio-cognitive state based on trajectory metadata.
    
    Args:
        emotional_reactivity: The emotional reactivity level of the trajectory.
        cultural_identity: The cultural identity diversity of the trajectory.
        
    Returns:
        A SocioCognitiveState object.
    """
    # Determine state type based on metadata (independent of evaluator)
    if emotional_reactivity == EmotionalReactivityLevel.HIGH:
        state_type = SocioCognitiveStateType.HIGH_REACTIVITY
    elif cultural_identity == CulturalIdentityDiversity.DIVERSE:
        state_type = SocioCognitiveStateType.CULTURAL_FRICTION
    else:
        state_type = SocioCognitiveStateType.NEUTRAL
        
    return SocioCognitiveState(
        state_type=state_type,
        confidence=1.0, # Synthetic data has high confidence
        timestamp=datetime.now()
    )

def generate_conflict_trajectory(
    emotional_reactivity: EmotionalReactivityLevel,
    cultural_identity: CulturalIdentityDiversity
) -> ConflictTrajectory:
    """
    Generate a single conflict trajectory with specified metadata.
    
    Args:
        emotional_reactivity: The emotional reactivity level for this trajectory.
        cultural_identity: The cultural identity diversity for this trajectory.
        
    Returns:
        A ConflictTrajectory object.
    """
    trajectory_id = generate_trajectory_id()
    metadata = {
        "emotional_reactivity": emotional_reactivity,
        "cultural_identity": cultural_identity
    }
    
    # Generate turns
    turns = []
    for i in range(NUM_TURNS_PER_TRAJECTORY):
        turn_text = generate_turn_text(metadata)
        turns.append({
            "turn_id": i,
            "text": turn_text,
            "speaker": "A" if i % 2 == 0 else "B"
        })
        
    state = generate_socio_cognitive_state(emotional_reactivity, cultural_identity)
    
    return ConflictTrajectory(
        trajectory_id=trajectory_id,
        turns=turns,
        socio_cognitive_state=state,
        metadata=metadata,
        created_at=datetime.now()
    )

def generate_trajectories_batch(
    count: int,
    target_oversample: bool = True
) -> List[ConflictTrajectory]:
    """
    Generate a batch of conflict trajectories with oversampling logic.
    
    Args:
        count: Total number of trajectories to generate.
        target_oversample: If True, ensure >=40% fall into target categories.
        
    Returns:
        List of ConflictTrajectory objects.
    """
    trajectories = []
    
    # Calculate target counts for oversampling
    target_count = int(count * 0.4) # 40% target
    remaining = count - target_count
    
    # Generate target category trajectories first
    target_categories = [
        (EmotionalReactivityLevel.HIGH, CulturalIdentityDiversity.HOMOGENEOUS),
        (EmotionalReactivityLevel.HIGH, CulturalIdentityDiversity.DIVERSE),
        (EmotionalReactivityLevel.LOW, CulturalIdentityDiversity.DIVERSE)
    ]
    
    for _ in range(target_count):
        reactivity, cultural = random.choice(target_categories)
        traj = generate_conflict_trajectory(reactivity, cultural)
        trajectories.append(traj)
        
    # Fill remaining with random distribution
    all_categories = [
        (EmotionalReactivityLevel.HIGH, CulturalIdentityDiversity.HOMOGENEOUS),
        (EmotionalReactivityLevel.HIGH, CulturalIdentityDiversity.DIVERSE),
        (EmotionalReactivityLevel.LOW, CulturalIdentityDiversity.HOMOGENEOUS),
        (EmotionalReactivityLevel.LOW, CulturalIdentityDiversity.DIVERSE)
    ]
    
    for _ in range(remaining):
        reactivity, cultural = random.choice(all_categories)
        traj = generate_conflict_trajectory(reactivity, cultural)
        trajectories.append(traj)
        
    # Shuffle to mix order
    random.shuffle(trajectories)
    return trajectories

def write_trajectories(trajectories: List[ConflictTrajectory], output_path: Path) -> None:
    """
    Write trajectories to a JSON file.
    
    Args:
        trajectories: List of ConflictTrajectory objects.
        output_path: Path to the output JSON file.
    """
    data = []
    for traj in trajectories:
        data.append({
            "trajectory_id": traj.trajectory_id,
            "turns": traj.turns,
            "socio_cognitive_state": {
                "state_type": traj.socio_cognitive_state.state_type.value,
                "confidence": traj.socio_cognitive_state.confidence,
                "timestamp": traj.socio_cognitive_state.timestamp.isoformat()
            },
            "metadata": {
                "emotional_reactivity": traj.metadata["emotional_reactivity"].value,
                "cultural_identity": traj.metadata["cultural_identity"].value
            },
            "created_at": traj.created_at.isoformat()
        })
        
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Wrote {len(trajectories)} trajectories to {output_path}")

def write_generation_stats(trajectories: List[ConflictTrajectory], output_path: Path) -> None:
    """
    Write generation statistics to a JSON file.
    
    Args:
        trajectories: List of ConflictTrajectory objects.
        output_path: Path to the output JSON file.
    """
    total = len(trajectories)
    high_reactivity = sum(1 for t in trajectories if t.metadata["emotional_reactivity"] == EmotionalReactivityLevel.HIGH)
    diverse_cultural = sum(1 for t in trajectories if t.metadata["cultural_identity"] == CulturalIdentityDiversity.DIVERSE)
    
    stats = {
        "total_trajectories": total,
        "high_reactivity_count": high_reactivity,
        "high_reactivity_pct": (high_reactivity / total) * 100 if total > 0 else 0,
        "diverse_cultural_count": diverse_cultural,
        "diverse_cultural_pct": (diverse_cultural / total) * 100 if total > 0 else 0,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Wrote generation stats to {output_path}")

def split_trajectory_into_turns(trajectory: ConflictTrajectory, window_size: int = TURN_WINDOW_SIZE) -> List[Dict[str, Any]]:
    """
    Split a full trajectory history into sliding windows of N turns.
    
    This function creates turn-level training pairs for the classifier.
    It uses ONLY trajectory metadata tags (emotional_reactivity, cultural_identity)
    to derive the label, ensuring independence from the ConsensusGapScore evaluator.
    
    Args:
        trajectory: The ConflictTrajectory object to split.
        window_size: Number of turns in each window (default: 3).
        
    Returns:
        List of dictionaries containing 'turn_text', 'label', 'trajectory_id',
        'confidence_score', and 'threshold_used'.
    """
    training_pairs = []
    turns = trajectory.turns
    trajectory_id = trajectory.trajectory_id
    
    # Derive label strictly from metadata (FR-005 Independence Check)
    # Mapping Logic: {{claim:c_0e3b527c}}
    reactivity = trajectory.metadata.get("emotional_reactivity", EmotionalReactivityLevel.LOW)
    cultural = trajectory.metadata.get("cultural_identity", CulturalIdentityDiversity.HOMOGENEOUS)
    
    if reactivity == EmotionalReactivityLevel.HIGH:
        label = "high_reactivity"
    elif cultural == CulturalIdentityDiversity.DIVERSE:
        label = "cultural_friction"
    else:
        label = "neutral"
    
    # Create sliding windows
    # We create a pair for each turn where we have enough history (window_size)
    # The 'turn_text' will be the concatenation of the last N turns
    for i in range(window_size - 1, len(turns)):
        window_turns = turns[i - window_size + 1 : i + 1]
        turn_text = " | ".join([t["text"] for t in window_turns])
        
        # Assign a fixed confidence score and threshold for derived data
        # These are placeholders that will be used by the classifier training
        # and downstream sensitivity analysis (T039)
        confidence_score = 0.95
        threshold_used = 0.80
        
        training_pairs.append({
            "turn_text": turn_text,
            "label": label,
            "trajectory_id": trajectory_id,
            "turn_index": i,
            "confidence_score": confidence_score,
            "threshold_used": threshold_used
        })
        
    return training_pairs

def derive_classifier_training_data(trajectories: List[ConflictTrajectory], output_path: Path) -> None:
    """
    Derive turn-level training pairs from generated trajectories and save to JSON.
    
    Args:
        trajectories: List of ConflictTrajectory objects.
        output_path: Path to the output JSON file.
    """
    all_pairs = []
    
    for traj in trajectories:
        pairs = split_trajectory_into_turns(traj)
        all_pairs.extend(pairs)
        
    with open(output_path, 'w') as f:
        json.dump(all_pairs, f, indent=2)
        
    logger.info(f"Derived {len(all_pairs)} training pairs from {len(trajectories)} trajectories")
    logger.info(f"Wrote training data to {output_path}")

def main():
    """Main entry point for data generation and derivation."""
    config = get_config_summary()
    ensure_directories()
    
    # Set seeds for reproducibility
    random.seed(config["seed"])
    
    # 1. Generate Trajectories (T012, T013, T014, T015)
    logger.info(f"Generating {TARGET_SAMPLE_SIZE} trajectories...")
    trajectories = generate_trajectories_batch(TARGET_SAMPLE_SIZE)
    
    # Verify sample size (T015)
    if len(trajectories) < TARGET_SAMPLE_SIZE:
        raise ValueError(f"Generated {len(trajectories)} trajectories, expected {TARGET_SAMPLE_SIZE}.")
        
    # Write trajectories (T014)
    trajectories_path = Path("data/processed/trajectories.json")
    write_trajectories(trajectories, trajectories_path)
    
    # Write stats (T014)
    stats_path = Path("data/processed/generation_stats.json")
    write_generation_stats(trajectories, stats_path)
    
    # 2. Derive Training Data (T019)
    logger.info("Deriving turn-level training data...")
    training_data_path = Path("data/processed/classifier_training_data.json")
    derive_classifier_training_data(trajectories, training_data_path)
    
    logger.info("Data generation and derivation complete.")

if __name__ == "__main__":
    main()
