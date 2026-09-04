import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Import the pipeline functions
from pipeline.generate import generate_frames_from_model, run_generation_pipeline
from models.dreamx_lite import create_dreamx_lite_model
from models.dreamx_base import create_dreamx_base_model
from utils.config import set_global_seed, init_environment

@pytest.fixture
def sample_prompts():
    """Sample prompts for testing."""
    return [
        "A person walking in a park",
        "A car driving down a city street"
    ]

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_generate_frames_from_model_dreamx_lite(sample_prompts, temp_output_dir):
    """Test frame generation with DreamX-Lite model."""
    set_global_seed(42)
    init_environment()
    
    model = create_dreamx_lite_model()
    
    generated_paths = generate_frames_from_model(
        model=model,
        model_type="dreamx_lite",
        prompts=sample_prompts,
        num_frames=8,
        height=256,
        width=256,
        seed=42,
        output_dir=temp_output_dir
    )
    
    # Verify paths were created
    assert len(generated_paths) == len(sample_prompts)
    
    for path in generated_paths:
        assert path.exists()
        frames_dir = path / "frames"
        assert frames_dir.exists()
        
        # Check that frames were generated
        frame_files = list(frames_dir.glob("frame_*.png"))
        assert len(frame_files) == 8
        
        # Verify frame files have content
        for frame_file in frame_files:
            assert frame_file.stat().st_size > 0

def test_generate_frames_from_model_baseline(sample_prompts, temp_output_dir):
    """Test frame generation with Baseline model."""
    set_global_seed(42)
    init_environment()
    
    model = create_dreamx_base_model()
    
    generated_paths = generate_frames_from_model(
        model=model,
        model_type="baseline",
        prompts=sample_prompts,
        num_frames=8,
        height=256,
        width=256,
        seed=42,
        output_dir=temp_output_dir
    )
    
    # Verify paths were created
    assert len(generated_paths) == len(sample_prompts)
    
    for path in generated_paths:
        assert path.exists()
        frames_dir = path / "frames"
        assert frames_dir.exists()
        
        # Check that frames were generated
        frame_files = list(frames_dir.glob("frame_*.png"))
        assert len(frame_files) == 8

def test_run_generation_pipeline_dreamx_lite(temp_output_dir):
    """Test the complete generation pipeline for DreamX-Lite."""
    set_global_seed(42)
    init_environment()
    
    # Override output directory
    original_output = os.environ.get('OUTPUT_DIR')
    os.environ['OUTPUT_DIR'] = str(temp_output_dir)
    
    try:
        results = run_generation_pipeline(
            model_type="dreamx_lite",
            num_prompts=2,
            num_frames=8,
            height=256,
            width=256,
            seed=42,
            use_baseline=False
        )
        
        assert results["status"] == "success"
        assert results["model_type"] == "dreamx_lite"
        assert len(results["generated_paths"]) == 2
        
        # Verify output directories exist
        for path_str in results["generated_paths"]:
            path = Path(path_str)
            assert path.exists()
            frames_dir = path / "frames"
            assert frames_dir.exists()
            assert len(list(frames_dir.glob("frame_*.png"))) == 8
    finally:
        if original_output:
            os.environ['OUTPUT_DIR'] = original_output
        elif 'OUTPUT_DIR' in os.environ:
            del os.environ['OUTPUT_DIR']

def test_run_generation_pipeline_baseline(temp_output_dir):
    """Test the complete generation pipeline for Baseline model."""
    set_global_seed(42)
    init_environment()
    
    original_output = os.environ.get('OUTPUT_DIR')
    os.environ['OUTPUT_DIR'] = str(temp_output_dir)
    
    try:
        results = run_generation_pipeline(
            model_type="baseline",
            num_prompts=2,
            num_frames=8,
            height=256,
            width=256,
            seed=42,
            use_baseline=False
        )
        
        assert results["status"] == "success"
        assert results["model_type"] == "baseline"
        assert len(results["generated_paths"]) == 2
    finally:
        if original_output:
            os.environ['OUTPUT_DIR'] = original_output
        elif 'OUTPUT_DIR' in os.environ:
            del os.environ['OUTPUT_DIR']

def test_identical_prompts_across_models(temp_output_dir):
    """Test that both models generate with identical prompts."""
    set_global_seed(42)
    init_environment()
    
    prompts = ["A person walking in a park"]
    
    # Generate with DreamX-Lite
    lite_results = run_generation_pipeline(
        model_type="dreamx_lite",
        num_prompts=1,
        num_frames=8,
        height=256,
        width=256,
        seed=42,
        use_baseline=False
    )
    
    # Generate with Baseline
    baseline_results = run_generation_pipeline(
        model_type="baseline",
        num_prompts=1,
        num_frames=8,
        height=256,
        width=256,
        seed=42,
        use_baseline=False
    )
    
    assert lite_results["status"] == "success"
    assert baseline_results["status"] == "success"
    assert len(lite_results["generated_paths"]) == len(baseline_results["generated_paths"])
    
    # Both should have generated the same number of frames
    for lite_path, baseline_path in zip(lite_results["generated_paths"], baseline_results["generated_paths"]):
        lite_frames = list(Path(lite_path).glob("frames/frame_*.png"))
        baseline_frames = list(Path(baseline_path).glob("frames/frame_*.png"))
        assert len(lite_frames) == len(baseline_frames) == 8
