"""
Generation module for llmXive.
Contains modules for prompt engineering, diffusion generation, and seed management.
"""

from .prompt_engine import (
    PromptEngineError,
    SceneDescriptionNotFoundError,
    PhysicsConstraintNotFoundError,
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

from .diffusion_runner import (
    DiffusionGenerationError,
    ModelLoadError,
    PromptFileNotFoundError,
    GenerationTimeoutError,
    load_prompt_file,
    load_all_prompts,
    load_seed_manifest,
    load_model,
    generate_single_image,
    generate_images_for_scene,
    run_diffusion_generation,
    main as diffusion_main
)

from .image_saver import (
    ImageSaveError,
    save_image,
    save_batch_images,
    main as image_saver_main
)

from .memory_monitor import (
    MemoryLimitExceededError,
    TimeLimitExceededError,
    get_memory_usage_mb,
    check_memory_limit,
    enforce_memory_limit,
    TimeLimitEnforcer,
    monitor_batch_generation,
    main as memory_monitor_main
)

from .seed_manager import (
    SeedManager,
    get_generation_seed,
    get_baseline_experimental_seeds,
    run_seed_generation,
    main as seed_manager_main
)

from .reference_geometry import (
    ReferenceGeometryRenderError,
    load_physics_constraint,
    extract_bounding_boxes,
    render_reference_geometry,
    run_reference_geometry_generation,
    main as reference_geometry_main
)

__all__ = [
    # Prompt Engine
    'PromptEngineError', 'SceneDescriptionNotFoundError', 'PhysicsConstraintNotFoundError',
    'load_scene_descriptions', 'load_physics_constraints', 'format_physics_constraints',
    'generate_baseline_prompt', 'generate_experimental_prompt', 'generate_control_prompt',
    'write_prompt_file', 'run_prompt_engineering', 'prompt_engine_main',
    
    # Diffusion Runner
    'DiffusionGenerationError', 'ModelLoadError', 'PromptFileNotFoundError',
    'GenerationTimeoutError', 'load_prompt_file', 'load_all_prompts',
    'load_seed_manifest', 'load_model', 'generate_single_image',
    'generate_images_for_scene', 'run_diffusion_generation', 'diffusion_main',
    
    # Image Saver
    'ImageSaveError', 'save_image', 'save_batch_images', 'image_saver_main',
    
    # Memory Monitor
    'MemoryLimitExceededError', 'TimeLimitExceededError', 'get_memory_usage_mb',
    'check_memory_limit', 'enforce_memory_limit', 'TimeLimitEnforcer',
    'monitor_batch_generation', 'memory_monitor_main',
    
    # Seed Manager
    'SeedManager', 'get_generation_seed', 'get_baseline_experimental_seeds',
    'run_seed_generation', 'seed_manager_main',
    
    # Reference Geometry
    'ReferenceGeometryRenderError', 'load_physics_constraint', 'extract_bounding_boxes',
    'render_reference_geometry', 'run_reference_geometry_generation', 'reference_geometry_main'
]
