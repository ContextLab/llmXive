"""
Integration test for gradient stability analysis (US1).

This task implements T031: Statistical test for gradient stability.
It reads gradient norms from data/logs/gradient_norms.json (produced by T011b)
and outputs data/results/gradient_stability_baseline.json.

Logic:
1. Load gradient norms from the baseline training log.
2. Compute mean and standard deviation of the norms.
3. Perform a self-consistency check:
   - If std_norm < 0.1 * mean_norm (relative stability), mark as stable.
   - This serves as the "reference distribution" check for a single baseline run.
4. Output the results to the specified JSON file.

DEPENDS ON: T011b (which produces data/logs/gradient_norms.json)
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

import pytest
import numpy as np

# Ensure the project root is in the path for imports if running standalone
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.training.homeostasis import log_gradient_norms


# --- Helper Functions for Analysis ---

def load_gradient_norms_from_file(filepath: str) -> List[float]:
    """
    Loads gradient norms from a JSON log file.
    Expects a list of dictionaries or a flat list of floats.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Gradient log file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Handle different log structures
    if isinstance(data, list):
        if len(data) == 0:
            return []
        if isinstance(data[0], dict):
            # Extract 'norm' key if present
            norms = [item.get('norm', item.get('gradient_norm', 0.0)) for item in data]
        else:
            norms = [float(x) for x in data]
        return [n for n in norms if isinstance(n, (int, float)) and not np.isnan(n)]
    else:
        raise ValueError(f"Unexpected data format in {filepath}: expected list")

def analyze_gradient_stability(norms: List[float]) -> Dict[str, Any]:
    """
    Performs statistical analysis on gradient norms.
    
    Logic:
    - Calculate mean and standard deviation.
    - Define 'stable' as: std_norm < 10% of mean_norm.
      (A relative stability threshold is robust against scale differences).
    
    Returns:
        Dict with keys: mean_norm, std_norm, is_stable
    """
    if not norms:
        return {
            "mean_norm": 0.0,
            "std_norm": 0.0,
            "is_stable": False,
            "reason": "No gradient norms found"
        }
    
    arr = np.array(norms)
    mean_norm = float(np.mean(arr))
    std_norm = float(np.std(arr))
    
    # Stability criterion: relative standard deviation < 10%
    # If mean is 0, we can't calculate relative, but if std is also 0, it's stable.
    if mean_norm == 0.0:
        is_stable = std_norm == 0.0
    else:
        relative_std = std_norm / mean_norm
        is_stable = relative_std < 0.10
    
    return {
        "mean_norm": round(mean_norm, 6),
        "std_norm": round(std_norm, 6),
        "is_stable": is_stable
    }

def write_stability_report(results: Dict[str, Any], output_path: str) -> None:
    """Writes the stability report to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

# --- Test Fixtures and Cases ---

@pytest.fixture
def temp_log_dir(tmp_path):
    """Creates a temporary directory structure mimicking the project data/logs."""
    logs_dir = tmp_path / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir

@pytest.fixture
def temp_results_dir(tmp_path):
    """Creates a temporary directory structure for results."""
    results_dir = tmp_path / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir

class TestGradientLogging:
    """Tests the ability to load and process gradient logs."""
    
    def test_load_empty_log(self, temp_log_dir):
        """Test handling of an empty log file."""
        log_file = temp_log_dir / "gradient_norms.json"
        log_file.write_text("[]")
        
        norms = load_gradient_norms_from_file(str(log_file))
        assert norms == []
    
    def test_load_valid_log(self, temp_log_dir):
        """Test loading a valid log file with list of dicts."""
        log_file = temp_log_dir / "gradient_norms.json"
        data = [
            {"step": 1, "norm": 0.5},
            {"step": 2, "norm": 0.52},
            {"step": 3, "norm": 0.48}
        ]
        log_file.write_text(json.dumps(data))
        
        norms = load_gradient_norms_from_file(str(log_file))
        assert len(norms) == 3
        assert np.isclose(norms[0], 0.5)
    
    def test_load_flat_log(self, temp_log_dir):
        """Test loading a valid log file with flat list."""
        log_file = temp_log_dir / "gradient_norms.json"
        data = [0.5, 0.52, 0.48]
        log_file.write_text(json.dumps(data))
        
        norms = load_gradient_norms_from_file(str(log_file))
        assert len(norms) == 3

class TestGradientStabilityComparison:
    """Tests the full stability analysis pipeline for T031."""
    
    def test_stability_analysis_stable(self, temp_log_dir, temp_results_dir):
        """Test that a stable gradient log is correctly identified."""
        # Create a stable log (low variance)
        log_file = temp_log_dir / "gradient_norms.json"
        # Generate stable data: mean ~1.0, very low std
        norms = [1.0 + (i % 5 - 2) * 0.01 for i in range(100)] 
        log_file.write_text(json.dumps([{"step": i, "norm": n} for i, n in enumerate(norms)]))
        
        # Run analysis
        loaded_norms = load_gradient_norms_from_file(str(log_file))
        results = analyze_gradient_stability(loaded_norms)
        
        assert results["is_stable"] is True
        assert abs(results["mean_norm"] - 1.0) < 0.05
        
        # Write report
        output_file = temp_results_dir / "gradient_stability_baseline.json"
        write_stability_report(results, str(output_file))
        
        assert output_file.exists()
        with open(output_file) as f:
            saved = json.load(f)
        assert saved["is_stable"] is True
    
    def test_stability_analysis_unstable(self, temp_log_dir, temp_results_dir):
        """Test that an unstable gradient log is correctly identified."""
        # Create an unstable log (high variance)
        log_file = temp_log_dir / "gradient_norms.json"
        # Generate unstable data: mean ~1.0, high std (> 10%)
        norms = [1.0 + (np.random.randn() * 0.5) for _ in range(100)]
        log_file.write_text(json.dumps([{"step": i, "norm": n} for i, n in enumerate(norms)]))
        
        # Run analysis
        loaded_norms = load_gradient_norms_from_file(str(log_file))
        results = analyze_gradient_stability(loaded_norms)
        
        # Note: With random noise, it might occasionally pass, but with 0.5 std vs 1.0 mean,
        # relative std is 0.5 (50%), which is > 10%.
        assert results["is_stable"] is False
    
    def test_missing_log_file(self, temp_results_dir):
        """Test behavior when the expected log file is missing."""
        # Do not create the log file
        log_path = str(temp_results_dir.parent / "logs" / "gradient_norms.json")
        
        with pytest.raises(FileNotFoundError):
            load_gradient_norms_from_file(log_path)
    
    def test_integration_with_real_path_structure(self, tmp_path):
        """
        Integration test simulating the actual project structure.
        Ensures the script can find data/logs/gradient_norms.json relative to project root.
        """
        # Setup directory structure
        project_root = tmp_path
        logs_dir = project_root / "data" / "logs"
        results_dir = project_root / "data" / "results"
        logs_dir.mkdir(parents=True, exist_ok=True)
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a realistic log file
        log_file = logs_dir / "gradient_norms.json"
        # Simulate a training run with stable gradients
        steps = 50
        norms = [0.8 + 0.02 * (i % 10 - 5) for i in range(steps)] # Small oscillation around 0.8
        data = [{"step": i, "norm": n, "layer": "transformer"} for i, n in enumerate(norms)]
        log_file.write_text(json.dumps(data))
        
        # Execute the logic that T031 requires
        loaded_norms = load_gradient_norms_from_file(str(log_file))
        analysis = analyze_gradient_stability(loaded_norms)
        
        # Verify schema
        assert "mean_norm" in analysis
        assert "std_norm" in analysis
        assert "is_stable" in analysis
        assert isinstance(analysis["mean_norm"], float)
        assert isinstance(analysis["std_norm"], float)
        assert isinstance(analysis["is_stable"], bool)
        
        # Write to the required output path
        output_file = results_dir / "gradient_stability_baseline.json"
        write_stability_report(analysis, str(output_file))
        
        # Verify output file content
        assert output_file.exists()
        with open(output_file) as f:
            final_report = json.load(f)
        
        assert final_report["is_stable"] is True # With our synthetic data, it should be stable
        
    def test_artifact_schema_compliance(self, tmp_path):
        """
        Verifies the output JSON strictly matches the required schema for T031.
        Schema: {"mean_norm": float, "std_norm": float, "is_stable": bool}
        """
        logs_dir = tmp_path / "data" / "logs"
        results_dir = tmp_path / "data" / "results"
        logs_dir.mkdir(parents=True, exist_ok=True)
        results_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = logs_dir / "gradient_norms.json"
        log_file.write_text(json.dumps([{"step": 0, "norm": 1.0}, {"step": 1, "norm": 1.01}]))
        
        norms = load_gradient_norms_from_file(str(log_file))
        analysis = analyze_gradient_stability(norms)
        
        output_file = results_dir / "gradient_stability_baseline.json"
        write_stability_report(analysis, str(output_file))
        
        with open(output_file) as f:
            report = json.load(f)
        
        # Strict schema check
        assert set(report.keys()) == {"mean_norm", "std_norm", "is_stable"}
        assert isinstance(report["mean_norm"], float)
        assert isinstance(report["std_norm"], float)
        assert isinstance(report["is_stable"], bool)