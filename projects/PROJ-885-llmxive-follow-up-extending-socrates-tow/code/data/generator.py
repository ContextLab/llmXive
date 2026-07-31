"""
Conflict Trajectory Generator for llmXive Dynamic Socio-Cognitive State Injection.

This module generates synthetic conflict dialogue trajectories using the SoCRATES pipeline
principles. It creates schema-compliant data simulating real conflict scenarios with
targeted metadata attributes (emotional reactivity, cultural identity) for oversampling
specific conditions.

IMPORTANT: This module generates SYNTHETIC data for research simulation purposes ONLY.
It does not load external datasets. The synthetic nature is explicit and required
by the project's simulation design (US1).
"""
import json
import logging
import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import ensure_directories, get_config_summary
from models.entities import (
    ConflictTrajectory,
    SocioCognitiveState,
    SocioCognitiveStateType,
    EmotionalReactivityLevel,
    CulturalIdentityDiversity
)
from data.loader import validate_trajectory_batch

# Configure logging
logger = logging.getLogger(__name__)

# Templates for synthetic dialogue generation
DIALOGUE_TEMPLATES = {
    "high_reactivity": [
        "I can't believe you're saying this! It's completely unacceptable!",
        "You never listen to me! This is exactly why we always fight!",
        "I'm done with this conversation. You're impossible to reason with!",
        "This is ridiculous! Why do you always have to be so stubborn?",
        "I feel completely dismissed and disrespected right now!",
        "You're making this way worse than it needs to be!",
        "I can't handle this level of conflict anymore!",
        "This is exactly what I was afraid would happen!"
    ],
    "cultural_friction": [
        "In my culture, this would be considered deeply disrespectful.",
        "I don't think you understand the cultural context here.",
        "This approach conflicts with my community's values.",
        "My family taught me differently about handling this situation.",
        "I feel like my cultural perspective is being ignored.",
        "This isn't how we would handle this in my background.",
        "There's a cultural nuance here that seems to be missed.",
        "My community would see this as a significant breach of trust."
    ],
    "neutral": [
        "I see your point, let's think about this more carefully.",
        "That's an interesting perspective, tell me more.",
        "I'm trying to understand where you're coming from.",
        "Let's find a middle ground that works for both of us.",
        "I appreciate you sharing your thoughts on this.",
        "This is complex, but I want to work through it together.",
        "I'm listening and trying to process what you're saying.",
        "Let's take a step back and look at the bigger picture."
    ]
}

CONTEXT_TEMPLATES = [
    "Workplace disagreement about project priorities",
    "Family dispute over holiday traditions",
    "Community meeting about local development",
    "Academic debate on research methodology",
    "Neighborhood conflict regarding shared spaces",
    "Team disagreement on strategic direction",
    "Personal relationship misunderstanding",
    "Civic organization policy discussion"
]

def generate_trajectory_id() -> str:
    """Generate a unique trajectory identifier."""
    return str(uuid.uuid4())

def generate_turn_text(
    emotional_reactivity: float,
    cultural_identity_diversity: float,
    turn_index: int
) -> str:
    """
    Generate a synthetic dialogue turn based on metadata attributes.
    
    Args:
        emotional_reactivity: Float between 0.0 and 1.0
        cultural_identity_diversity: Float between 0.0 and 1.0
        turn_index: Current turn number in the trajectory
        
    Returns:
        A string representing the dialogue turn
    """
    # Determine which template set to use based on thresholds
    if emotional_reactivity > 0.7:
        template_set = DIALOGUE_TEMPLATES["high_reactivity"]
    elif cultural_identity_diversity > 0.7:
        template_set = DIALOGUE_TEMPLATES["cultural_friction"]
    else:
        template_set = DIALOGUE_TEMPLATES["neutral"]
    
    # Select a random template and add variation
    base_text = random.choice(template_set)
    variation = f" (Turn {turn_index})"
    return base_text + variation

def generate_conflict_trajectory(
    emotional_reactivity_level: float,
    cultural_identity_diversity: float,
    num_turns: int = 10
) -> ConflictTrajectory:
    """
    Generate a single conflict trajectory with specified metadata.
    
    Args:
        emotional_reactivity_level: Float between 0.0 and 1.0
        cultural_identity_diversity: Float between 0.0 and 1.0
        num_turns: Number of dialogue turns in the trajectory
        
    Returns:
        A ConflictTrajectory dataclass instance
    """
    trajectory_id = generate_trajectory_id()
    context = random.choice(CONTEXT_TEMPLATES)
    
    # Generate turns
    turns = []
    for i in range(num_turns):
        turn_text = generate_turn_text(
            emotional_reactivity_level,
            cultural_identity_diversity,
            i + 1
        )
        turns.append(turn_text)
    
    # Create socio-cognitive state
    state_type = SocioCognitiveStateType.CONFLICT
    state = SocioCognitiveState(
        state_type=state_type,
        emotional_reactivity=emotional_reactivity_level,
        cultural_identity_diversity=cultural_identity_diversity
    )
    
    # Determine labels based on thresholds (for downstream classification)
    label = "neutral"
    if emotional_reactivity_level > 0.7:
        label = "high_reactivity"
    elif cultural_identity_diversity > 0.7:
        label = "cultural_friction"
    
    trajectory = ConflictTrajectory(
        trajectory_id=trajectory_id,
        context=context,
        turns=turns,
        socio_cognitive_state=state,
        generated_at=datetime.now().isoformat(),
        target_emotional_reactivity=emotional_reactivity_level,
        target_cultural_identity_diversity=cultural_identity_diversity,
        label=label
    )
    
    return trajectory

def generate_trajectories_batch(
    total_count: int = 500,
    target_high_reactivity_ratio: float = 0.4,
    target_cultural_diversity_ratio: float = 0.4
) -> List[ConflictTrajectory]:
    """
    Generate a batch of trajectories with targeted oversampling.
    
    Args:
        total_count: Total number of trajectories to generate
        target_high_reactivity_ratio: Target proportion of high reactivity samples
        target_cultural_diversity_ratio: Target proportion of high diversity samples
        
    Returns:
        List of ConflictTrajectory instances
    """
    trajectories = []
    
    # Calculate counts for each category
    high_reactivity_count = int(total_count * target_high_reactivity_ratio)
    high_cultural_count = int(total_count * target_cultural_diversity_ratio)
    neutral_count = total_count - high_reactivity_count - high_cultural_count
    
    # Generate high reactivity trajectories
    for _ in range(high_reactivity_count):
        # Ensure high reactivity (>0.7)
        er = random.uniform(0.75, 0.95)
        cid = random.uniform(0.2, 0.6)  # Lower diversity for this group
        traj = generate_conflict_trajectory(er, cid)
        trajectories.append(traj)
    
    # Generate high cultural diversity trajectories
    for _ in range(high_cultural_count):
        er = random.uniform(0.2, 0.6)  # Lower reactivity for this group
        cid = random.uniform(0.75, 0.95)
        traj = generate_conflict_trajectory(er, cid)
        trajectories.append(traj)
    
    # Generate neutral trajectories
    for _ in range(neutral_count):
        er = random.uniform(0.2, 0.6)
        cid = random.uniform(0.2, 0.6)
        traj = generate_conflict_trajectory(er, cid)
        trajectories.append(traj)
    
    # Shuffle to mix categories
    random.shuffle(trajectories)
    
    return trajectories

def write_trajectories(
    trajectories: List[ConflictTrajectory],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write trajectories to a JSON file.
    
    Args:
        trajectories: List of ConflictTrajectory instances
        output_path: Optional path to write to (default: data/processed/trajectories.json)
        
    Returns:
        Path to the written file
    """
    if output_path is None:
        output_path = Path("data/processed/trajectories.json")
    
    ensure_directories()
    
    # Convert to dict format for JSON serialization
    data = []
    for traj in trajectories:
        traj_dict = {
            "trajectory_id": traj.trajectory_id,
            "context": traj.context,
            "turns": traj.turns,
            "socio_cognitive_state": {
                "state_type": traj.socio_cognitive_state.state_type.value,
                "emotional_reactivity": traj.socio_cognitive_state.emotional_reactivity,
                "cultural_identity_diversity": traj.socio_cognitive_state.cultural_identity_diversity
            },
            "generated_at": traj.generated_at,
            "target_emotional_reactivity": traj.target_emotional_reactivity,
            "target_cultural_identity_diversity": traj.target_cultural_identity_diversity,
            "label": traj.label
        }
        data.append(traj_dict)
    
    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Wrote {len(trajectories)} trajectories to {output_path}")
    return output_path

def write_generation_stats(
    trajectories: List[ConflictTrajectory],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write generation statistics to a JSON file.
    
    Args:
        trajectories: List of ConflictTrajectory instances
        output_path: Optional path to write to (default: data/processed/generation_stats.json)
        
    Returns:
        Path to the written file
    """
    if output_path is None:
        output_path = Path("data/processed/generation_stats.json")
    
    ensure_directories()
    
    # Calculate statistics
    total = len(trajectories)
    high_reactivity_count = sum(1 for t in trajectories if t.label == "high_reactivity")
    cultural_friction_count = sum(1 for t in trajectories if t.label == "cultural_friction")
    neutral_count = sum(1 for t in trajectories if t.label == "neutral")
    
    stats = {
        "total_trajectories": total,
        "category_counts": {
            "high_reactivity": high_reactivity_count,
            "cultural_friction": cultural_friction_count,
            "neutral": neutral_count
        },
        "category_percentages": {
            "high_reactivity": (high_reactivity_count / total * 100) if total > 0 else 0,
            "cultural_friction": (cultural_friction_count / total * 100) if total > 0 else 0,
            "neutral": (neutral_count / total * 100) if total > 0 else 0
        },
        "target_oversampling": {
            "high_reactivity_target": 0.4,
            "cultural_diversity_target": 0.4
        },
        "generated_at": datetime.now().isoformat()
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Wrote generation stats to {output_path}")
    return output_path

def main():
    """Main entry point for trajectory generation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load config
    config = get_config_summary()
    logger.info(f"Starting trajectory generation with config: {config}")
    
    # Generate trajectories
    total_count = config.get("TOTAL_TRAJECTORIES", 500)
    target_high_reactivity = config.get("TARGET_HIGH_REACTIVITY_RATIO", 0.4)
    target_cultural_diversity = config.get("TARGET_CULTURAL_DIVERSITY_RATIO", 0.4)
    
    logger.info(f"Generating {total_count} trajectories...")
    trajectories = generate_trajectories_batch(
        total_count=total_count,
        target_high_reactivity_ratio=target_high_reactivity,
        target_cultural_diversity_ratio=target_cultural_diversity
    )
    
    # Validate
    validation_result = validate_trajectory_batch(trajectories)
    if not validation_result["valid"]:
        logger.error(f"Validation failed: {validation_result['errors']}")
        raise ValueError("Trajectory validation failed")
    
    # Write outputs
    write_trajectories(trajectories)
    write_generation_stats(trajectories)
    
    logger.info(f"Successfully generated {len(trajectories)} trajectories")

if __name__ == "__main__":
    main()