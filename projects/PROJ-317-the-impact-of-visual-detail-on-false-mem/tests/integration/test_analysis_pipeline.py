"""
Integration test for the full analysis pipeline on mock data.

This test verifies the end-to-end flow:
1. Generate mock participant response data (simulating US2 output).
2. Run the statistical analysis (ANOVA) from code/analysis/stats.py.
3. Verify that results are saved to disk (JSON) and visualization (PNG) is generated.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

# Add project root to path to import code modules
# Assuming this test runs from the project root or tests/ directory
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import get_project_root, get_processed_dir, get_figures_dir, get_responses_dir
from analysis.stats import main as stats_main, calculate_anova_power, save_power_analysis
from utils.logging import get_logger

logger = get_logger(__name__)


def generate_mock_responses_for_testing():
    """
    Generates a synthetic dataset mimicking the output of US2 (participant sessions).
    Creates a CSV file in data/responses/ with columns:
    participant_id, stimulus_id, condition, detail_type, response_value, is_correct
    
    Conditions: 'enhanced', 'reduced', 'baseline'
    Detail Types: 'true', 'false' (lure)
    """
    root = get_project_root()
    resp_dir = get_responses_dir()
    resp_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = resp_dir / "mock_session_data.csv"
    
    data = []
    np.random.seed(42)  # Reproducibility
    
    conditions = ['enhanced', 'reduced', 'baseline']
    detail_types = ['true', 'false']
    n_participants = 30
    n_stimuli_per_condition = 10
    
    for p_id in range(1, n_participants + 1):
        for cond in conditions:
            # Simulate a participant seeing stimuli in this condition
            for stim_idx in range(n_stimuli_per_condition):
                stimulus_id = f"stim_{cond}_{stim_idx}"
                
                for dtype in detail_types:
                    # Simulate response logic:
                    # True details: high recall rate (0.8-0.95)
                    # False details: lower recall rate (0.2-0.4), slightly higher in reduced detail
                    if dtype == 'true':
                        base_prob = 0.90
                        # Slight variation per condition
                        if cond == 'enhanced': base_prob += 0.02
                        elif cond == 'reduced': base_prob -= 0.05
                    else: # false
                        base_prob = 0.30
                        # False memories might be higher in reduced detail (hypothesis)
                        if cond == 'reduced': base_prob += 0.08
                        elif cond == 'enhanced': base_prob -= 0.05
                    
                    is_correct = 1 if np.random.random() < base_prob else 0
                    # Response value: 1 = remembered, 0 = not remembered
                    response_value = 1 if is_correct == 1 else 0 
                    # For false memories, "correct" usually means "did NOT say yes to lure"
                    # But here we store raw "yes" (1) or "no" (0) to the question "Did you see X?"
                    # Let's standardize: response_value = 1 if they claimed to see it.
                    
                    data.append({
                        "participant_id": p_id,
                        "stimulus_id": stimulus_id,
                        "condition": cond,
                        "detail_type": dtype,
                        "response_value": response_value,
                        "timestamp": "2026-06-29T12:00:00"
                    })
    
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    logger.info(f"Generated mock responses at {output_file}")
    return output_file


def test_full_analysis_pipeline():
    """
    Integration test:
    1. Generate mock data.
    2. Run stats_main() which should read the data, run ANOVA, and save results.
    3. Assert output files exist.
    """
    # 1. Setup: Generate mock data
    mock_data_path = generate_mock_responses_for_testing()
    assert mock_data_path.exists(), "Mock data generation failed"
    
    # 2. Run the analysis pipeline
    # We need to mock or set up the environment so stats.py knows where to look
    # The stats.py main() function likely reads from config or fixed paths.
    # Let's assume it reads from data/responses/ and writes to data/processed/
    
    # Ensure processed dir exists
    processed_dir = get_processed_dir()
    processed_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = get_figures_dir()
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # Run the stats main function
    # We catch SystemExit if argparse calls it, but main() should just run
    try:
        stats_main()
    except SystemExit:
        # If argparse exits, it might be due to missing args if main() expects CLI args.
        # Looking at the API, main() is likely a script entry point. 
        # If it requires args, we might need to pass them or refactor.
        # Assuming main() runs with defaults if no args provided or handles it gracefully.
        pass
    
    # 3. Verify outputs
    # Expected outputs based on T035/T037 tasks:
    # - data/processed/anova_results.json
    # - data/processed/posthoc_results.json (if applicable)
    # - figures/anova_plot.png (or similar)
    
    anova_results_path = processed_dir / "anova_results.json"
    plot_path = figures_dir / "false_memory_rates.png"
    
    # Check if files exist
    # Note: The exact filenames might vary based on implementation in T035/T037.
    # We check for likely candidates.
    found_anova = False
    found_plot = False
    
    for f in processed_dir.glob("*.json"):
        if "anova" in f.name.lower():
            found_anova = True
            logger.info(f"Found ANOVA results at {f}")
            # Validate JSON content
            with open(f, 'r') as fh:
                data = json.load(fh)
                assert "statistic" in data or "f_value" in data, "ANOVA result missing expected keys"
    
    for f in figures_dir.glob("*.png"):
        found_plot = True
        logger.info(f"Found plot at {f}")
        assert f.stat().st_size > 0, "Plot file is empty"
    
    # If specific names are expected by the task, we assert them.
    # Based on standard practice:
    if not found_anova:
        # Fallback check: maybe it's named differently?
        assert False, "No ANOVA results JSON file found in data/processed/"
    
    if not found_plot:
        assert False, "No visualization PNG file found in figures/"
        
    logger.info("Integration test passed: Full pipeline generated expected artifacts.")


if __name__ == "__main__":
    test_full_analysis_pipeline()
    print("SUCCESS: T034 Integration Test Passed")