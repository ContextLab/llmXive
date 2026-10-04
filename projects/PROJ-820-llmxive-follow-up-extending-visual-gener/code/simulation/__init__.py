"""
Simulation module for llmXive physics engine.

This module handles physics simulations using pymunk to validate
scene descriptions and detect logical contradictions.
"""

from .physics_engine import (
    SceneDescriptionNotFoundError,
    InvalidSceneDescriptionError,
    SimulationError,
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
    'load_scene_descriptions',
    'parse_scene_description',
    'simulate_physics',
    'update_contradiction_log',
    'run_physics_simulation',
    'main'
]