import pytest
from analysis.stats import calculate_statistical_significance
from pathlib import Path
import json

def test_fisher_exact_vs_ztest_logic():
    """Verify Fisher's Exact Test is used for n < 30."""
    # Create mock log files with n < 30
    baseline_data = [
        {'status': 'success' if i % 2 == 0 else 'failure'} for i in range(10)
    ]
    augmented_data = [
        {'status': 'success' if i % 2 == 0 else 'failure'} for i in range(10)
    ]
    
    # Write to temp files
    baseline_path = Path('data/logs/baseline_execution.jsonl')
    augmented_path = Path('data/logs/augmented_execution.jsonl')
    
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(baseline_path, 'w') as f:
        for item in baseline_data:
            f.write(json.dumps(item) + '\n')
    
    with open(augmented_path, 'w') as f:
        for item in augmented_data:
            f.write(json.dumps(item) + '\n')
    
    # Run analysis
    result = calculate_statistical_significance(baseline_path, augmented_path)
    
    # Verify Fisher's Exact was used
    assert "Fisher's Exact Test" in result['test_type']
    
    # Cleanup
    baseline_path.unlink()
    augmented_path.unlink()
