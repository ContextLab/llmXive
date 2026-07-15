"""
Integration test for the baseline inference pipeline (User Story 1).

This test verifies that the end-to-end baseline pipeline:
1. Loads real video clips from the dataset (DAVIS/YouTube-VOS via streaming).
2. Computes optical flow (T009 dependency).
3. Processes videos to generate masks and stratify by motion.
4. Runs the baseline LiveEdit model inference (T014 dependency).
5. Calculates metrics (SSIM, BSS, memory) (T016 dependency).
6. Generates a valid JSON report (T017 dependency).

The test asserts that the output file exists, contains valid data,
and matches the expected schema.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

import pytest
import numpy as np

# Project imports (matching API surface)
from data.models import VideoClip, MetricRecord, AnalysisResult
from data.flow import process_video_flow, aggregate_flow_stats
from data.processor import process_video_clip, stratify_clips_by_motion
from models.baseline import run_baseline_inference
from metrics.ssim import calculate_bss, calculate_flow_normalized_ssim
from metrics.resource import MemoryProfiler
from analysis.reporter import generate_baseline_report
from config import get_default_config, ensure_directories
from utils.logger import get_logger
from contracts.metrics_validator import MetricsValidator

# Constants for test configuration
TEST_SUBSET_SIZE = 3  # Small subset for integration test speed
TEST_OUTPUT_DIR = "tests/integration/output"
TEST_REPORT_FILE = "baseline_integration_results.json"

logger = get_logger(__name__)


@pytest.fixture(scope="module")
def test_environment():
    """Setup and teardown for integration test environment."""
    # Create temporary output directory
    output_dir = Path(TEST_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure project directories exist
    ensure_directories()
    
    yield output_dir
    
    # Cleanup (optional, keep for debugging if needed)
    # shutil.rmtree(output_dir, ignore_errors=True)


def test_baseline_pipeline_end_to_end(test_environment):
    """
    Integration test: Run the full baseline pipeline on a small subset of real data.
    
    Steps:
    1. Load a small subset of real video clips (streaming).
    2. Compute optical flow for each clip.
    3. Process clips (mask generation, motion stratification).
    4. Run baseline inference.
    5. Calculate metrics.
    6. Generate and validate report.
    """
    # 1. Load real data subset
    # Note: This relies on T012 (downloader) being implemented.
    # We assume the downloader populates data/raw or we stream directly.
    # For this test, we will attempt to stream from the 'datasets' library directly
    # to ensure we are using REAL data as per constraints.
    
    from datasets import load_dataset
    
    logger.info("Loading real dataset subset (DAVIS) via streaming...")
    try:
        # Using DAVIS dataset, split 'train' or 'validation', streaming=True
        # Selecting a small subset for speed
        ds = load_dataset("DAVIS", split="validation", streaming=True)
        clips: List[VideoClip] = []
        
        count = 0
        for item in ds:
            if count >= TEST_SUBSET_SIZE:
                break
            
            # Construct VideoClip from dataset item
            # Assuming item has 'frames' (list of PIL images) and 'name'
            frames = item['frames']
            name = item.get('name', f"clip_{count}")
            
            clip = VideoClip(
                id=f"test_{count}",
                name=name,
                frames=frames,
                duration=len(frames) / 10.0, # Assume 10fps for test
                source="DAVIS",
                is_valid=True
            )
            clips.append(clip)
            count += 1
        
        assert len(clips) > 0, "Failed to load any real clips from DAVIS."
        logger.info(f"Loaded {len(clips)} real clips for integration test.")
        
    except Exception as e:
        logger.error(f"Failed to load real dataset: {e}")
        # Fail loudly as per constraints
        pytest.fail(f"Could not load real data source (DAVIS). Integration test aborted. Error: {e}")

    # 2. Compute Optical Flow (Dependency T009)
    logger.info("Computing optical flow for clips...")
    flow_results = []
    for clip in clips:
        flow_data = process_video_flow(clip)
        flow_results.append({
            "clip_id": clip.id,
            "stats": aggregate_flow_stats(flow_data)
        })
    
    # 3. Process Video Clips (Dependency T013)
    logger.info("Processing videos and stratifying by motion...")
    processed_clips = []
    for i, clip in enumerate(clips):
        # Generate synthetic mask and process
        processed = process_video_clip(clip, flow_data=flow_results[i]['stats'])
        processed_clips.append(processed)
    
    # Stratify (just to verify the function works)
    stratified = stratify_clips_by_motion(processed_clips)
    logger.info(f"Stratified clips: Static={len(stratified.get('Static', []))}, "
                f"Slow={len(stratified.get('Slow Rigid', []))}, "
                f"Fast={len(stratified.get('Fast Non-Rigid', []))}")

    # 4. Run Baseline Inference (Dependency T014/T015)
    logger.info("Running baseline inference...")
    config = get_default_config()
    inference_results = []
    
    profiler = MemoryProfiler()
    profiler.start()
    
    for processed_clip in processed_clips:
        try:
            # Run inference (this should return edited frames or metrics)
            # The baseline model wrapper is expected to return a dict with 'edited_frames'
            result = run_baseline_inference(processed_clip, config)
            inference_results.append(result)
        except Exception as e:
            logger.warning(f"Inference failed for clip {processed_clip.id}: {e}")
            # Continue with other clips to test pipeline robustness, 
            # but ensure at least one succeeds if possible.
            continue
    
    profiler.stop()
    peak_memory = profiler.get_peak_mb()
    logger.info(f"Peak memory usage: {peak_memory:.2f} MB")

    # 5. Calculate Metrics (Dependency T016)
    logger.info("Calculating metrics (SSIM, BSS)...")
    metric_records: List[MetricRecord] = []
    
    for i, result in enumerate(inference_results):
        clip = processed_clips[i]
        edited_frames = result.get('edited_frames', [])
        
        if len(edited_frames) < 2:
            continue
        
        # Calculate BSS (Background Stability Score)
        bss_score = calculate_bss(edited_frames)
        
        # Calculate Flow-Normalized SSIM
        flow_norm_ssim = calculate_flow_normalized_ssim(edited_frames, flow_results[i]['stats'])
        
        record = MetricRecord(
            clip_id=clip.id,
            bss=bss_score,
            flow_normalized_ssim=flow_norm_ssim,
            peak_memory_mb=peak_memory,
            inference_time_ms=result.get('inference_time_ms', 0.0),
            flow_magnitude_mean=flow_results[i]['stats'].get('mean_magnitude', 0.0),
            is_valid=True
        )
        metric_records.append(record)
    
    assert len(metric_records) > 0, "No valid metric records generated."

    # 6. Generate Report (Dependency T017)
    logger.info("Generating baseline report...")
    report_path = test_environment / TEST_REPORT_FILE
    
    report_data = generate_baseline_report(metric_records, output_path=str(report_path))
    
    # 7. Validate Report
    logger.info("Validating report schema...")
    assert report_path.exists(), f"Report file {report_path} was not created."
    
    with open(report_path, 'r') as f:
        report_json = json.load(f)
    
    validator = MetricsValidator()
    is_valid = validator.validate_report(report_json)
    assert is_valid, "Generated report failed schema validation."
    
    # Additional assertions on content
    assert 'metrics' in report_json
    assert len(report_json['metrics']) == len(metric_records)
    assert 'summary' in report_json
    assert 'avg_bss' in report_json['summary']
    
    logger.info("Integration test PASSED: Baseline pipeline executed successfully on real data.")