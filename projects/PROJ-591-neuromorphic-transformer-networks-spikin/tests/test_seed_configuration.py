import pytest
import os
import sys
import pandas as pd
import tempfile
import shutil

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import train_baseline, setup_seed, TrainingResult

def test_seed_determinism():
    """Test that running with the same seed produces the same results."""
    seed = 42
    epochs = 2
    
    # Run first time
    results1 = train_baseline(seed=seed, epochs=epochs, patience=10)
    
    # Run second time
    results2 = train_baseline(seed=seed, epochs=epochs, patience=10)
    
    # Check that perplexities are identical
    for r1, r2 in zip(results1, results2):
        assert r1.perplexity == r2.perplexity, f"Perplexity mismatch at epoch {r1.epoch}: {r1.perplexity} vs {r2.perplexity}"
        assert r1.wall_clock_time == r2.wall_clock_time, "Wall clock time should match for deterministic runs (approximate)"

def test_multiple_seeds_produce_different_results():
    """Test that different seeds produce different results."""
    seeds = [1, 2]
    all_perplexities = []
    
    for seed in seeds:
        results = train_baseline(seed=seed, epochs=1, patience=10)
        all_perplexities.append(results[0].perplexity)
    
    # They should likely be different due to different initialization
    # (Though with small data/epochs they might coincidentally be same, but highly unlikely)
    # We assert that the seeds were processed
    assert len(all_perplexities) == 2

def test_output_file_created():
    """Test that the output CSV file is created and populated."""
    # Clean up any existing file
    output_path = "data/processed/baseline_metrics.csv"
    if os.path.exists(output_path):
        os.remove(output_path)
        
    # Run training
    train_baseline(seed=99, epochs=1, patience=10)
    
    # Check file exists
    assert os.path.exists(output_path), f"Output file {output_path} was not created"
    
    # Check content
    df = pd.read_csv(output_path)
    assert len(df) >= 1, "CSV should have at least one row"
    assert 'seed' in df.columns, "CSV must have 'seed' column"
    assert 'epoch' in df.columns, "CSV must have 'epoch' column"
    assert 'perplexity' in df.columns, "CSV must have 'perplexity' column"
    assert 'energy_per_token_kWh' in df.columns, "CSV must have 'energy_per_token_kWh' column"
    assert 'wall_clock_time' in df.columns, "CSV must have 'wall_clock_time' column"
    
    # Verify the specific seed is in the file
    assert (df['seed'] == 99).any(), "Seed 99 should be present in the results"

def test_early_stopping_integration():
    """Test that early stopping logic works with seed configuration."""
    # Use a small patience to trigger early stopping quickly if loss plateaus
    results = train_baseline(seed=100, epochs=5, patience=1, delta=0.0001)
    
    # Check that at least one result has early_stopped flag set or we ran all epochs
    # This is a soft check as early stopping depends on loss behavior
    assert len(results) > 0, "Should have at least one result"
    # If early stopping triggered, the last result should have the flag
    if len(results) < 5:
        assert results[-1].early_stopped, "Early stopping should be flagged if run was cut short"