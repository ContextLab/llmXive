"""
Generation module for llmXive follow-up project.

This module handles image generation, prompt engineering, and related utilities.
"""

from .image_saver import ImageSaveError, save_image, save_batch_images
from .memory_monitor import (
    MemoryLimitExceededError,
    TimeLimitExceededError,
    get_memory_usage_mb,
    check_memory_limit,
    enforce_memory_limit,
    TimeLimitEnforcer,
    monitor_batch_generation,
)
from .prompt_engine import (
    load_scene_descriptions,
    load_physics_constraints,
    format_physics_constraints,
    generate_baseline_prompt,
    generate_experimental_prompt,
    generate_control_prompt,
    write_prompt_file,
    run_prompt_engineering,
)
from .reference_geometry import (
    ReferenceGeometryRenderError,
    load_physics_constraint,
    extract_bounding_boxes,
    render_reference_geometry,
    run_reference_geometry_generation,
)
from .seed_manager import SeedManager, get_generation_seed, get_baseline_experimental_seeds

__all__ = [
    "ImageSaveError",
    "save_image",
    "save_batch_images",
    "MemoryLimitExceededError",
    "TimeLimitExceededError",
    "get_memory_usage_mb",
    "check_memory_limit",
    "enforce_memory_limit",
    "TimeLimitEnforcer",
    "monitor_batch_generation",
    "load_scene_descriptions",
    "load_physics_constraints",
    "format_physics_constraints",
    "generate_baseline_prompt",
    "generate_experimental_prompt",
    "generate_control_prompt",
    "write_prompt_file",
    "run_prompt_engineering",
    "ReferenceGeometryRenderError",
    "load_physics_constraint",
    "extract_bounding_boxes",
    "render_reference_geometry",
    "run_reference_geometry_generation",
    "SeedManager",
    "get_generation_seed",
    "get_baseline_experimental_seeds",
]