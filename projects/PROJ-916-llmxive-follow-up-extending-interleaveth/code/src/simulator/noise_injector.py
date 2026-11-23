"""
Noise Injector for Simulating Semantic Uncertainty (Noisy Mode).

This module implements the logic to randomly swap relationships or remove objects
from a `SceneDescription` to simulate the "grounding gap" between text prompts
and visual reality. It is used by the simulator to generate "Noisy" mode data.

The injection process is deterministic when a seed is provided via the global
configuration or explicitly passed to the functions.
"""

import random
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict, replace

from src.config import get_config
from src.simulator.parser import (
    ParsedObject,
    ParsedRelationship,
    SceneDescription,
)


@dataclass
class NoiseInjectionResult:
    """Result of a noise injection operation."""
    original: SceneDescription
    noisy: SceneDescription
    injected_noise_count: int
    noise_type_distribution: Dict[str, int]


def _get_rng() -> random.Random:
    """
    Returns a random number generator instance seeded from config or default.
    Ensures reproducibility as per T018b.
    """
    config = get_config()
    seed = getattr(config, 'random_seed', 42)
    return random.Random(seed)


def remove_objects(
    scene_desc: SceneDescription,
    rng: Optional[random.Random] = None,
    removal_prob: float = 0.1
) -> Tuple[SceneDescription, int]:
    """
    Randomly removes objects from the scene description.

    Args:
        scene_desc: The original scene description.
        rng: Random number generator instance. If None, uses global config seed.
        removal_prob: Probability (0.0 to 1.0) of removing each object.

    Returns:
        A tuple of (new_scene_desc, count_of_removed_objects).
    """
    if rng is None:
        rng = _get_rng()

    objects = list(scene_desc.objects)
    objects_to_keep = []
    removed_count = 0

    for obj in objects:
        if rng.random() > removal_prob:
            objects_to_keep.append(obj)
        else:
            removed_count += 1

    # Identify relationships that involve removed objects to clean up
    removed_obj_ids = {obj.id for obj in objects if obj not in objects_to_keep}
    relationships_to_keep = [
        rel for rel in scene_desc.relationships
        if rel.subject_id not in removed_obj_ids and rel.object_id not in removed_obj_ids
    ]

    new_desc = replace(
        scene_desc,
        objects=objects_to_keep,
        relationships=relationships_to_keep
    )

    return new_desc, removed_count


def swap_relationships(
    scene_desc: SceneDescription,
    rng: Optional[random.Random] = None,
    swap_prob: float = 0.1
) -> Tuple[SceneDescription, int]:
    """
    Randomly swaps the subject and object of relationships to simulate
    semantic uncertainty (e.g., 'man riding horse' -> 'horse riding man').

    Args:
        scene_desc: The original scene description.
        rng: Random number generator instance.
        swap_prob: Probability of swapping a relationship.

    Returns:
        A tuple of (new_scene_desc, count_of_swapped_relationships).
    """
    if rng is None:
        rng = _get_rng()

    new_relationships = []
    swapped_count = 0

    for rel in scene_desc.relationships:
        if rng.random() < swap_prob and len(scene_desc.objects) >= 2:
            # Swap subject and object
            swapped_rel = replace(rel, subject_id=rel.object_id, object_id=rel.subject_id)
            new_relationships.append(swapped_rel)
            swapped_count += 1
        else:
            new_relationships.append(rel)

    new_desc = replace(scene_desc, relationships=new_relationships)
    return new_desc, swapped_count


def inject_noise(
    scene_desc: SceneDescription,
    noise_level: float = 0.1,
    seed: Optional[int] = None
) -> NoiseInjectionResult:
    """
    Main entry point to inject noise into a scene description.

    This function performs two operations:
    1. Removes a fraction of objects (controlled by noise_level).
    2. Swaps the direction of a fraction of relationships (controlled by noise_level).

    Args:
        scene_desc: The original scene description.
        noise_level: The target probability for both removal and swapping (0.0 to 1.0).
                     Target total error rate is roughly proportional to this value.
        seed: Optional seed to override the global config for this specific call.

    Returns:
        NoiseInjectionResult containing the noisy scene and statistics.
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = _get_rng()

    # Step 1: Remove objects
    noisy_desc, removed_count = remove_objects(scene_desc, rng, removal_prob=noise_level)

    # Step 2: Swap relationships on the already-modified scene
    noisy_desc, swapped_count = swap_relationships(noisy_desc, rng, swap_prob=noise_level)

    total_noise = removed_count + swapped_count

    return NoiseInjectionResult(
        original=scene_desc,
        noisy=noisy_desc,
        injected_noise_count=total_noise,
        noise_type_distribution={
            "removed_objects": removed_count,
            "swapped_relationships": swapped_count
        }
    )


def calculate_noise_ratio(result: NoiseInjectionResult) -> float:
    """
    Calculates the ratio of injected noise elements to the total original elements.
    Total elements = original objects + original relationships.
    """
    total_original = len(result.original.objects) + len(result.original.relationships)
    if total_original == 0:
        return 0.0
    return result.injected_noise_count / total_original
