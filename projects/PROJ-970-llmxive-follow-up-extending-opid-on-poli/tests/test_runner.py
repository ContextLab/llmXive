import pytest
from experiments.runner import ExperimentRunner, ExperimentConfig

def test_runner_creates_results():
    config = ExperimentConfig(
        tiers=[1],
        thresholds=[0.5],
        episodes_per_setting=5,
        seed=42
    )
    runner = ExperimentRunner(config)
    results = runner.run()
    
    assert len(results) == 5
    assert all(r.tier == 1 for r in results)
    assert all(r.threshold == 0.5 for r in results)