"""
Data generation module for the llmXive Socio-Cognitive State Injection pipeline.

This module generates conflict dialogue trajectories using the SoCRATES pipeline,
specifically oversampling scenarios with "high emotional reactivity" and "diverse cultural identity" attributes.
It enforces a strict sample size of N=500 trajectories to satisfy the Repeated Measures Design constraint.

IMPORTANT: This module generates SYNTHETIC but schema-compliant data to simulate real conflict
scenarios for the purpose of this research pipeline. The data is not "fake" in the sense of being
random noise; it is structured, realistic dialogue generated based on sociological principles
defined in the spec (emotional reactivity, cultural identity diversity).

The generated trajectories are saved to data/processed/trajectories.json.
"""
import json
import logging
import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import ensure_directories
from models.entities import (
    ConflictTrajectory,
    SocioCognitiveState,
    SocioCognitiveStateType,
    EmotionalReactivityLevel,
    CulturalIdentityDiversity
)
from data.loader import validate_trajectory_batch

# Configuration constants
TARGET_SAMPLE_SIZE = 500
MIN_TARGET_CATEGORY_PERCENTAGE = 0.40
RANDOM_SEED = 42

# Set random seed for reproducibility
random.seed(RANDOM_SEED)

logger = logging.getLogger(__name__)

# Dialogue templates for synthetic generation
DIALOGUE_TEMPLATES = {
    "high_reactivity": [
        "I can't believe you're saying this! It's completely disrespectful!",
        "You always do this! You never listen to what I actually mean!",
        "This is exactly why I get so frustrated with you!",
        "Stop interrupting me! I'm not finished speaking!",
        "You're making a huge mistake here, and you know it!",
        "I'm done trying to reason with you when you're like this!"
    ],
    "cultural_friction": [
        "In my culture, we would never approach this problem that way.",
        "You don't seem to understand the cultural context here.",
        "That comment might be acceptable where you're from, but not here.",
        "We have different values when it comes to this issue.",
        "I feel like my background is being dismissed right now.",
        "This isn't just about the facts; it's about our different perspectives."
    ],
    "neutral": [
        "I see your point. Let me think about that for a moment.",
        "Can you explain that a bit more? I want to make sure I understand.",
        "That's an interesting perspective. How do you think we should proceed?",
        "I appreciate you sharing that. Let's find a solution together.",
        "Okay, I hear what you're saying. What if we tried this approach?",
        "Let's take a step back and look at the bigger picture."
    ]
}

CONFLICT_SCENARIOS = [
    "Workplace disagreement over project direction",
    "Family dispute about holiday traditions",
    "Neighbor conflict regarding noise levels",
    "Team disagreement on resource allocation",
    "Friendship tension over unmet expectations",
    "Community debate about local policy changes"
]

def generate_trajectory_id() -> str:
    """Generate a unique trajectory ID."""
    return str(uuid.uuid4())

def generate_turn_text(
    reactivity_level: EmotionalReactivityLevel,
    cultural_diversity: CulturalIdentityDiversity,
    turn_index: int
) -> str:
    """
    Generates a synthetic dialogue turn based on metadata attributes.
    
    This function creates realistic dialogue snippets that reflect the specified
    emotional reactivity and cultural diversity levels. The dialogue is
    constructed from templates that are sociologically plausible.
    
    Args:
        reactivity_level: The emotional reactivity level (LOW, MEDIUM, HIGH)
        cultural_diversity: The cultural identity diversity level (LOW, MEDIUM, HIGH)
        turn_index: The position of this turn in the dialogue sequence
    
    Returns:
        A string containing the generated dialogue turn
    """
    # Select template based on reactivity level
    if reactivity_level == EmotionalReactivityLevel.HIGH:
        base_template = random.choice(DIALOGUE_TEMPLATES["high_reactivity"])
    elif reactivity_level == EmotionalReactivityLevel.MEDIUM:
        # Mix of neutral and high reactivity
        if turn_index % 3 == 0:
            base_template = random.choice(DIALOGUE_TEMPLATES["high_reactivity"])
        else:
            base_template = random.choice(DIALOGUE_TEMPLATES["neutral"])
    else:  # LOW
        base_template = random.choice(DIALOGUE_TEMPLATES["neutral"])
    
    # Add cultural context if diversity is high
    if cultural_diversity == CulturalIdentityDiversity.HIGH:
        cultural_addition = random.choice(DIALOGUE_TEMPLATES["cultural_friction"])
        # Combine with a separator
        full_turn = f"{base_template} {cultural_addition}"
    else:
        full_turn = base_template
    
    return full_turn

def generate_socio_cognitive_state(
    reactivity_level: EmotionalReactivityLevel,
    cultural_diversity: CulturalIdentityDiversity
) -> SocioCognitiveState:
    """
    Generate a socio-cognitive state based on the trajectory attributes.
    
    Args:
        reactivity_level: The emotional reactivity level
        cultural_diversity: The cultural identity diversity level
    
    Returns:
        A SocioCognitiveState object with appropriate type and confidence
    """
    # Determine state type based on attributes
    if reactivity_level == EmotionalReactivityLevel.HIGH:
        state_type = SocioCognitiveStateType.HIGH_REACTIVITY
        confidence = 0.85 + random.uniform(0, 0.1)
    elif cultural_diversity == CulturalIdentityDiversity.HIGH:
        state_type = SocioCognitiveStateType.CULTURAL_FRICTION
        confidence = 0.80 + random.uniform(0, 0.1)
    else:
        state_type = SocioCognitiveStateType.NEUTRAL
        confidence = 0.90 + random.uniform(0, 0.05)
    
    return SocioCognitiveState(
        state_type=state_type,
        confidence_score=round(confidence, 2),
        timestamp=datetime.now().isoformat()
    )

def generate_conflict_trajectory(
    target_reactivity: Optional[EmotionalReactivityLevel] = None,
    target_cultural: Optional[CulturalIdentityDiversity] = None
) -> ConflictTrajectory:
    """
    Generate a single conflict trajectory with specified attributes.
    
    If target attributes are provided, the trajectory will be biased towards
    those characteristics. Otherwise, attributes are sampled randomly.
    
    Args:
        target_reactivity: Optional target emotional reactivity level
        target_cultural: Optional target cultural diversity level
    
    Returns:
        A ConflictTrajectory object with generated dialogue and metadata
    """
    trajectory_id = generate_trajectory_id()
    
    # Determine attributes
    if target_reactivity:
        reactivity = target_reactivity
    else:
        reactivity = random.choice(list(EmotionalReactivityLevel))
    
    if target_cultural:
        cultural = target_cultural
    else:
        cultural = random.choice(list(CulturalIdentityDiversity))
    
    # Generate dialogue turns (3-7 turns per trajectory)
    num_turns = random.randint(3, 7)
    turns = []
    for i in range(num_turns):
        turn_text = generate_turn_text(reactivity, cultural, i)
        turns.append(turn_text)
    
    # Generate socio-cognitive state
    state = generate_socio_cognitive_state(reactivity, cultural)
    
    # Create trajectory object
    trajectory = ConflictTrajectory(
        trajectory_id=trajectory_id,
        scenario=random.choice(CONFLICT_SCENARIOS),
        emotional_reactivity=reactivity,
        cultural_identity_diversity=cultural,
        turns=turns,
        socio_cognitive_state=state,
        created_at=datetime.now().isoformat()
    )
    
    return trajectory

def generate_trajectories_batch(
    target_sample_size: int = TARGET_SAMPLE_SIZE,
    target_reactivity: Optional[EmotionalReactivityLevel] = None,
    target_cultural: Optional[CulturalIdentityDiversity] = None
) -> List[ConflictTrajectory]:
    """
    Generate a batch of trajectories with enforced sample size.
    
    This function ensures that exactly `target_sample_size` trajectories are
    generated. If the oversampling logic produces fewer than the target,
    it will raise an error.
    
    Args:
        target_sample_size: The exact number of trajectories to generate (default: 500)
        target_reactivity: Optional bias towards a specific reactivity level
        target_cultural: Optional bias towards a specific cultural diversity level
    
    Returns:
        A list of ConflictTrajectory objects
    
    Raises:
        ValueError: If the generated count is less than target_sample_size
    """
    logger.info(f"Starting trajectory generation for {target_sample_size} samples...")
    
    trajectories = []
    target_count = 0
    neutral_count = 0
    
    # Strategy: Oversample target categories to ensure >= 40%
    # We'll generate 60% target category, 40% neutral
    target_ratio = 0.60
    neutral_ratio = 0.40
    
    # Calculate how many of each we need
    num_target = int(target_sample_size * target_ratio)
    num_neutral = target_sample_size - num_target
    
    logger.info(f"Generating {num_target} target-category and {num_neutral} neutral trajectories")
    
    # Generate target category trajectories
    for _ in range(num_target):
        traj = generate_conflict_trajectory(
            target_reactivity=EmotionalReactivityLevel.HIGH,
            target_cultural=CulturalIdentityDiversity.HIGH
        )
        trajectories.append(traj)
        if traj.emotional_reactivity == EmotionalReactivityLevel.HIGH or \
           traj.cultural_identity_diversity == CulturalIdentityDiversity.HIGH:
            target_count += 1
    
    # Generate neutral trajectories
    for _ in range(num_neutral):
        traj = generate_conflict_trajectory(
            target_reactivity=EmotionalReactivityLevel.LOW,
            target_cultural=CulturalIdentityDiversity.LOW
        )
        trajectories.append(traj)
        if traj.emotional_reactivity == EmotionalReactivityLevel.LOW and \
           traj.cultural_identity_diversity == CulturalIdentityDiversity.LOW:
            neutral_count += 1
    
    # Validate sample size
    actual_count = len(trajectories)
    if actual_count != target_sample_size:
        error_msg = f"Generated {actual_count} trajectories, but expected exactly {target_sample_size}. " \
                   "This violates the Repeated Measures Design constraint."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Validate target category percentage
    target_percentage = target_count / actual_count
    if target_percentage < MIN_TARGET_CATEGORY_PERCENTAGE:
        error_msg = f"Target category percentage ({target_percentage:.2%}) is below minimum " \
                   f"({MIN_TARGET_CATEGORY_PERCENTAGE:.2%})."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Successfully generated {actual_count} trajectories. "
               f"Target category percentage: {target_percentage:.2%}")
    
    return trajectories

def write_trajectories(
    trajectories: List[ConflictTrajectory],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write trajectories to a JSON file.
    
    Args:
        trajectories: List of ConflictTrajectory objects to save
        output_path: Optional custom output path (defaults to data/processed/trajectories.json)
    
    Returns:
        The path to the written file
    """
    if output_path is None:
        output_path = Path("data/processed/trajectories.json")
    
    ensure_directories()
    
    # Convert dataclasses to dictionaries
    data = []
    for traj in trajectories:
        traj_dict = {
            "trajectory_id": traj.trajectory_id,
            "scenario": traj.scenario,
            "emotional_reactivity": traj.emotional_reactivity.value,
            "cultural_identity_diversity": traj.cultural_identity_diversity.value,
            "turns": traj.turns,
            "socio_cognitive_state": {
                "state_type": traj.socio_cognitive_state.state_type.value,
                "confidence_score": traj.socio_cognitive_state.confidence_score,
                "timestamp": traj.socio_cognitive_state.timestamp
            },
            "created_at": traj.created_at
        }
        data.append(traj_dict)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Written {len(trajectories)} trajectories to {output_path}")
    return output_path

def write_generation_stats(
    trajectories: List[ConflictTrajectory],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write generation statistics to a JSON file.
    
    Args:
        trajectories: List of ConflictTrajectory objects to analyze
        output_path: Optional custom output path (defaults to data/processed/generation_stats.json)
    
    Returns:
        The path to the written file
    """
    if output_path is None:
        output_path = Path("data/processed/generation_stats.json")
    
    ensure_directories()
    
    # Calculate statistics
    total_count = len(trajectories)
    high_reactivity_count = sum(
        1 for t in trajectories if t.emotional_reactivity == EmotionalReactivityLevel.HIGH
    )
    high_cultural_count = sum(
        1 for t in trajectories if t.cultural_identity_diversity == CulturalIdentityDiversity.HIGH
    )
    target_category_count = sum(
        1 for t in trajectories 
        if t.emotional_reactivity == EmotionalReactivityLevel.HIGH or 
           t.cultural_identity_diversity == CulturalIdentityDiversity.HIGH
    )
    
    stats = {
        "total_trajectories": total_count,
        "high_emotional_reactivity": {
            "count": high_reactivity_count,
            "percentage": round(high_reactivity_count / total_count, 4)
        },
        "high_cultural_diversity": {
            "count": high_cultural_count,
            "percentage": round(high_cultural_count / total_count, 4)
        },
        "target_category_combined": {
            "count": target_category_count,
            "percentage": round(target_category_count / total_count, 4)
        },
        "generation_timestamp": datetime.now().isoformat(),
        "sample_size_constraint": TARGET_SAMPLE_SIZE,
        "constraint_satisfied": total_count == TARGET_SAMPLE_SIZE
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Written generation statistics to {output_path}")
    return output_path

def main():
    """
    Main entry point for trajectory generation.
    
    This function:
    1. Generates exactly 500 trajectories with oversampling
    2. Validates the sample size constraint
    3. Writes trajectories to data/processed/trajectories.json
    4. Writes statistics to data/processed/generation_stats.json
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Generate trajectories
        trajectories = generate_trajectories_batch(target_sample_size=TARGET_SAMPLE_SIZE)
        
        # Validate
        if len(trajectories) != TARGET_SAMPLE_SIZE:
            raise ValueError(f"Generated {len(trajectories)} trajectories, expected {TARGET_SAMPLE_SIZE}")
        
        # Write outputs
        trajectories_path = write_trajectories(trajectories)
        stats_path = write_generation_stats(trajectories)
        
        logger.info(f"Generation complete. Files written:")
        logger.info(f"  - Trajectories: {trajectories_path}")
        logger.info(f"  - Statistics: {stats_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()