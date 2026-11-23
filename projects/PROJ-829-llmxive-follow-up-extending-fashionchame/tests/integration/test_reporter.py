"""
Integration test for the reporter module (T020).
Verifies that the reporter correctly aggregates scores and generates the report.
"""

import json
import pytest
import tempfile
from pathlib import Path
from src.pipeline.reporter import run_pipeline, aggregate_scores_by_class, calculate_relative_loss

@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        manifest_path = tmp_path / "data" / "processed" / "filtered_subset_manifest.json"
        scores_path = tmp_path / "data" / "processed" / "raw_fidelity_scores.json"
        output_path = tmp_path / "data" / "processed" / "fidelity_report.json"
        
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a mock manifest with excluded samples
        manifest_data = {
            "total_samples": 5,
            "valid_samples": 3,
            "excluded_samples": 2,
            "excluded_list": [
                {
                    "sample_id": "sample_002",
                    "reason": "Low confidence",
                    "excluded_type": "low_confidence",
                    "original_sample": {"id": "sample_002", "prompt": "bad"}
                },
                {
                    "sample_id": "sample_004",
                    "reason": "Conflict",
                    "excluded_type": "conflict",
                    "original_sample": {"id": "sample_004", "prompt": "bad"}
                }
            ],
            "threshold_used": 0.8
        }
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        # Create mock raw scores
        scores_data = [
            {
                "sample_id": "sample_001",
                "lpips": 0.1,
                "ssim": 0.9,
                "baseline_lpips": 0.05,
                "baseline_ssim": 0.95,
                "feature_class": "color",
                "attributes": {"colors": ["red"]}
            },
            {
                "sample_id": "sample_002", # Excluded
                "lpips": 0.2,
                "ssim": 0.8,
                "baseline_lpips": 0.1,
                "baseline_ssim": 0.85,
                "feature_class": "color",
                "attributes": {"colors": ["blue"]}
            },
            {
                "sample_id": "sample_003",
                "lpips": 0.15,
                "ssim": 0.85,
                "baseline_lpips": 0.08,
                "baseline_ssim": 0.92,
                "feature_class": "pattern",
                "attributes": {"patterns": ["striped"]}
            },
            {
                "sample_id": "sample_004", # Excluded
                "lpips": 0.3,
                "ssim": 0.7,
                "baseline_lpips": 0.15,
                "baseline_ssim": 0.8,
                "feature_class": "pattern",
                "attributes": {"patterns": ["checkered"]}
            },
            {
                "sample_id": "sample_005",
                "lpips": 0.05,
                "ssim": 0.95,
                "baseline_lpips": 0.02,
                "baseline_ssim": 0.98,
                "feature_class": "texture",
                "attributes": {"textures": ["smooth"]}
            }
        ]
        with open(scores_path, 'w') as f:
            json.dump(scores_data, f)
        
        yield manifest_path, scores_path, output_path

def test_reporter_excludes_low_confidence(temp_dirs):
    manifest_path, scores_path, output_path = temp_dirs
    
    # Run pipeline
    report = run_pipeline(
        manifest_path=manifest_path,
        scores_path=scores_path,
        output_path=output_path
    )
    
    # Verify output file exists
    assert output_path.exists()
    
    # Verify content
    with open(output_path, 'r') as f:
        saved_report = json.load(f)
    
    # Check that excluded samples (002, 004) are NOT in the report
    # We check by verifying the counts and values
    
    # Color class: Should only have sample_001
    assert 'color' in saved_report
    assert saved_report['color']['sample_count'] == 1
    # Mean LPIPS for color: 0.1
    assert abs(saved_report['color']['mean_lpips'] - 0.1) < 0.001
    
    # Pattern class: Should only have sample_003
    assert 'pattern' in saved_report
    assert saved_report['pattern']['sample_count'] == 1
    # Mean LPIPS for pattern: 0.15
    assert abs(saved_report['pattern']['mean_lpips'] - 0.15) < 0.001
    
    # Texture class: Should only have sample_005
    assert 'texture' in saved_report
    assert saved_report['texture']['sample_count'] == 1
    # Mean LPIPS for texture: 0.05
    assert abs(saved_report['texture']['mean_lpips'] - 0.05) < 0.001

def test_aggregate_scores_by_class():
    # Test the aggregation logic directly
    valid_ids = {"s1", "s2"}
    scores = [
        {"sample_id": "s1", "lpips": 0.1, "ssim": 0.9, "feature_class": "color"},
        {"sample_id": "s2", "lpips": 0.2, "ssim": 0.8, "feature_class": "color"},
        {"sample_id": "s3", "lpips": 0.3, "ssim": 0.7, "feature_class": "pattern"}, # Invalid ID
        {"sample_id": "s1", "lpips": 0.4, "ssim": 0.6, "feature_class": "pattern"}  # Duplicate ID, different class
    ]
    
    result = aggregate_scores_by_class(valid_ids, scores)
    
    assert "color" in result
    assert len(result["color"]) == 2
    assert "pattern" in result
    assert len(result["pattern"]) == 1 # s3 excluded, s1 included

def test_calculate_relative_loss():
    # Test relative loss calculation
    scores = [
        {"lpips": 0.1, "baseline_lpips": 0.05},
        {"lpips": 0.2, "baseline_lpips": 0.1}
    ]
    
    # Loss 1: (0.1 - 0.05) / 0.05 = 1.0 (100%)
    # Loss 2: (0.2 - 0.1) / 0.1 = 1.0 (100%)
    # Average: 100%
    loss = calculate_relative_loss(scores)
    assert abs(loss - 100.0) < 0.001
    
    # Test with SSIM
    scores_ssim = [
        {"ssim": 0.9, "baseline_ssim": 0.95},
        {"ssim": 0.8, "baseline_ssim": 0.9}
    ]
    # Loss 1: (0.95 - 0.9) / 0.95 = 0.0526...
    # Loss 2: (0.9 - 0.8) / 0.9 = 0.1111...
    # Average: (0.0526 + 0.1111) / 2 * 100 = ~8.19%
    loss_ssim = calculate_relative_loss(scores_ssim)
    expected = ((0.95 - 0.9) / 0.95 + (0.9 - 0.8) / 0.9) / 2 * 100
    assert abs(loss_ssim - expected) < 0.01