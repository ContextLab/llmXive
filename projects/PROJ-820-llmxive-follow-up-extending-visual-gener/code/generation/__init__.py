"""
Generation module for llmXive pipeline.

This module handles the creation of prompts, images, and reference geometry
based on physics-constrained scene descriptions.
"""

from .prompt_engine import (
    load_scene_descriptions,
    load_physics_constraints,
    format_physics_constraints,
    generate_baseline_prompt,
    generate_experimental_prompt,
    generate_control_prompt,
    write_prompt_file,
    run_prompt_engineering,
    main as prompt_engine_main
)

from .reference_geometry import (
    ReferenceGeometryRenderError,
    load_physics_constraint,
    extract_bounding_boxes,
    render_reference_geometry,
    run_reference_geometry_generation,
    main as reference_geometry_main
)

from .seed_manager import (
    SeedManager,
    get_generation_seed,
    get_baseline_experimental_seeds,
    main as seed_manager_main
)

from .image_saver import (
    ImageSaveError,
    save_image,
    save_batch_images,
    main as image_saver_main
)

__all__ = [
    # Prompt Engine
    'load_scene_descriptions',
    'load_physics_constraints',
    'format_physics_constraints',
    'generate_baseline_prompt',
    'generate_experimental_prompt',
    'generate_control_prompt',
    'write_prompt_file',
    'run_prompt_engineering',
    'prompt_engine_main',
    
    # Reference Geometry
    'ReferenceGeometryRenderError',
    'load_physics_constraint',
    'extract_bounding_boxes',
    'render_reference_geometry',
    'run_reference_geometry_generation',
    'reference_geometry_main',
    
    # Seed Manager
    'SeedManager',
    'get_generation_seed',
    'get_baseline_experimental_seeds',
    'seed_manager_main',
    
    # Image Saver
    'ImageSaveError',
    'save_image',
    'save_batch_images',
    'image_saver_main'
]