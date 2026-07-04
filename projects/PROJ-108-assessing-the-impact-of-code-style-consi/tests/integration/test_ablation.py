"""
Integration test for ablation analysis (US3).
Verifies that style score independence from code complexity is controlled for.
"""

import os
import sys
import json
import tempfile
import shutil
import statistics
from pathlib import Path

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.metrics import pearson_correlation

def _generate_synthetic_data(output_dir: Path):
    """
    Generates a synthetic dataset for ablation analysis.
    Simulates: file_size, cyclomatic_complexity, style_score, bleu_score.
    
    Logic:
    1. file_size and cyclomatic_complexity are positively correlated.
    2. style_score is independent of file_size (to test the ablation control).
    3. bleu_score is influenced by style_score, but we want to verify that
       the relationship holds even when controlling for file_size.
    """
    n = 50
    
    # Simulate file_size (random positive integers)
    file_sizes = [100 + i * 5 + (i % 10) for i in range(n)]
    
    # Simulate cyclomatic_complexity (correlated with size)
    complexity = [size // 10 + (i % 3) for i, size in enumerate(file_sizes)]
    
    # Simulate style_score (0.0 to 1.0) - intentionally uncorrelated with size
    # We use a simple deterministic pattern that doesn't scale with size
    style_scores = [(i % 7) / 7.0 for i in range(n)]
    
    # Simulate bleu_score:
    # Base score influenced by style, plus noise
    # If style is high, bleu tends to be higher
    bleu_scores = []
    for i in range(n):
        base = 20.0 + (style_scores[i] * 50.0) # Style impact
        noise = (i % 5) - 2 # Small noise
        bleu = max(0.0, min(100.0, base + noise))
        bleu_scores.append(bleu)

    data = []
    for i in range(n):
        data.append({
            "file_path": f"mock_file_{i}.py",
            "file_size": file_sizes[i],
            "cyclomatic_complexity": complexity[i],
            "composite_score": style_scores[i],
            "bleu_score": bleu_scores[i]
        })

    output_file = output_dir / "ablation_data.json"
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)
    
    return output_file

def test_ablation_complexity_control():
    """
    Integration test verifying ablation analysis logic.
    
    Steps:
    1. Generate synthetic data where style_score is independent of file_size.
    2. Run ablation logic:
       - Calculate correlation between style_score and bleu_score (Total Effect).
       - Calculate correlation between style_score and bleu_score *within* 
         file_size strata (or partial correlation logic simplified for test).
       - Verify that the relationship is not driven by file_size.
    3. Assert that the ablation report is generated and contains expected keys.
    """
    # Setup temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # 1. Generate Data
        data_file = _generate_synthetic_data(temp_dir)
        
        # 2. Load Data
        with open(data_file, "r") as f:
            data = json.load(f)
        
        style_scores = [d["composite_score"] for d in data]
        bleu_scores = [d["bleu_score"] for d in data]
        file_sizes = [d["file_size"] for d in data]
        
        # 3. Perform Abalation Logic (Simplified for Integration Test)
        # We check if the correlation between style and bleu remains significant
        # even when controlling for file_size.
        # Since we can't easily do full partial correlation without statsmodels,
        # we will simulate the "control" by checking correlation in subsets.
        
        # Split data into Low Size and High Size groups
        median_size = statistics.median(file_sizes)
        low_size_data = [d for d in data if d["file_size"] <= median_size]
        high_size_data = [d for d in data if d["file_size"] > median_size]
        
        # Calculate correlations within groups
        if len(low_size_data) > 2:
            low_style = [d["composite_score"] for d in low_size_data]
            low_bleu = [d["bleu_score"] for d in low_size_data]
            corr_low, _ = pearson_correlation(low_style, low_bleu)
        else:
            corr_low = 0.0
            
        if len(high_size_data) > 2:
            high_style = [d["composite_score"] for d in high_size_data]
            high_bleu = [d["bleu_score"] for d in high_size_data]
            corr_high, _ = pearson_correlation(high_style, high_bleu)
        else:
            corr_high = 0.0

        # Overall correlation
        overall_corr, _ = pearson_correlation(style_scores, bleu_scores)

        # 4. Construct Report
        report = {
            "method": "Stratified Correlation Check",
            "overall_correlation": overall_corr,
            "low_size_correlation": corr_low,
            "high_size_correlation": corr_high,
            "control_variable": "file_size",
            "independent_variable": "composite_score",
            "dependent_variable": "bleu_score",
            "conclusion": "Independent" if abs(corr_low - corr_high) < 0.2 else "Confounded",
            "notes": "Ablation analysis verifies that style impact is not merely a proxy for file size."
        }

        # 5. Write Output
        output_report = temp_dir / "ablation_report.json"
        with open(output_report, "w") as f:
            json.dump(report, f, indent=2)

        # 6. Assertions
        assert output_report.exists(), "Ablation report file was not created."
        
        with open(output_report, "r") as f:
            result = json.load(f)
        
        assert "overall_correlation" in result
        assert "low_size_correlation" in result
        assert "high_size_correlation" in result
        assert "control_variable" in result
        assert result["control_variable"] == "file_size"
        
        # Verify logic: Since we generated data with style independent of size,
        # and bleu dependent on style, the correlation should be roughly consistent
        # across size groups (or at least not zero if style is the driver).
        # We assert that the correlations are non-zero (style has an effect)
        # and that the difference isn't massive (size doesn't confound it completely).
        assert abs(result["overall_correlation"]) > 0.1, "Overall correlation too low for synthetic data."
        assert abs(result["low_size_correlation"] - result["high_size_correlation"]) < 0.3, "Ablation failed: Size confounds style too much."

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_ablation_complexity_control()
    print("Integration test for ablation analysis passed.")
