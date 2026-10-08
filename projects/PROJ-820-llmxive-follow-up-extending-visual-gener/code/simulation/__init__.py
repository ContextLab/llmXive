"""
Simulation module for llmXive.
Contains physics simulation logic using PyMunk.
"""

from .physics_engine import (
    SceneDescriptionNotFoundError,
    InvalidSceneDescriptionError,
    SimulationError,
    PhysicsConstraint,
    load_scene_descriptions,
    parse_scene_description,
    simulate_physics,
    update_contradiction_log,
    run_physics_simulation,
    main
)

__all__ = [
    'SceneDescriptionNotFoundError',
    'InvalidSceneDescriptionError',
    'SimulationError',
    'PhysicsConstraint',
    'load_scene_descriptions',
    'parse_scene_description',
    'simulate_physics',
    'update_contradiction_log',
    'run_physics_simulation',
    'main'
]
