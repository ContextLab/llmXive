"""
Simulation module for llmXive physics engine.
Contains physics simulation logic using pymunk.
"""
from .physics_engine import (
    SceneDescriptionNotFoundError,
    SimulationError,
    InvalidSceneDescriptionError,
    load_scene_descriptions,
    parse_scene_description,
    simulate_physics,
    update_contradiction_log,
    run_physics_simulation,
    main
)

__all__ = [
    'SceneDescriptionNotFoundError',
    'SimulationError',
    'InvalidSceneDescriptionError',
    'load_scene_descriptions',
    'parse_scene_description',
    'simulate_physics',
    'update_contradiction_log',
    'run_physics_simulation',
    'main'
]
