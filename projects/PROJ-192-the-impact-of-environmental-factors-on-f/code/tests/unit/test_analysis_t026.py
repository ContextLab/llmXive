import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from src.pipelines.analysis import perform_power_check, run_stratification_pipeline

@pytest.fixture
def sample_data():
    """Create a sample dataframe with varying biome sizes."""
    data = {
        'sample_id': [f's{i}' for i in range(20)],
        'biome': ['Forest'] * 15 + ['Grassland'] * 3 + ['Desert'] * 2,
        'pH': [6.5] * 20,
        'nutrients': [100.0] * 20
    }
    return pd.DataFrame(data)

def test_perform_power_check_basic(sample_data, tmp_path):
    """Test that power check correctly identifies and logs small strata."""
    log_file = tmp_path / "skipped_strata.log"
    
    valid, skipped = perform_power_check(
        sample_data.groupby('biome').apply(lambda x: x.reset_index(drop=True)).to_dict(),
        min_samples=10,
        log_path=str(log_file)
    )
    
    # Forest (15) should be valid
    # Grassland (3) and Desert (2) should be skipped
    assert 'Forest' in valid
    assert 'Grassland' in skipped
    assert 'Desert' in skipped
    
    # Verify log file contents
    assert log_file.exists()
    log_content = log_file.read_text()
    assert 'Grassland' in log_content
    assert 'Desert' in log_content
    assert 'SKIPPED' in log_content

def test_perform_power_check_all_valid(sample_data, tmp_path):
    """Test when all strata meet the threshold."""
    # Modify data to have enough samples in all groups
    data = {
        'sample_id': [f's{i}' for i in range(30)],
        'biome': ['Forest'] * 10 + ['Grassland'] * 10 + ['Desert'] * 10,
        'pH': [6.5] * 30,
        'nutrients': [100.0] * 30
    }
    df = pd.DataFrame(data)
    stratified = {k: v for k, v in df.groupby('biome')}
    
    log_file = tmp_path / "skipped_strata.log"
    valid, skipped = perform_power_check(stratified, min_samples=10, log_path=str(log_file))
    
    assert len(valid) == 3
    assert len(skipped) == 0
    assert log_file.exists()
    # Log file might be empty or contain only success messages depending on implementation
    # Our implementation only writes on skip.
    assert len(log_file.read_text()) == 0

def test_run_stratification_pipeline_integration(sample_data, tmp_path):
    """Integration test for the stratification pipeline."""
    # Save sample data
    csv_path = tmp_path / "cleaned_metadata.csv"
    sample_data.to_csv(csv_path, index=False)
    
    output_dir = tmp_path / "results"
    
    result = run_stratification_pipeline(
        data_path=str(csv_path),
        biome_col='biome',
        min_samples=10,
        output_dir=str(output_dir)
    )
    
    assert 'valid_strata' in result
    assert 'skipped_strata' in result
    assert 'Forest' in result['valid_strata']
    assert 'Grassland' in result['skipped_strata']
    assert 'Desert' in result['skipped_strata']
    
    # Verify log file was created
    log_path = output_dir / "skipped_strata.log"
    assert log_path.exists()
    content = log_path.read_text()
    assert 'Grassland' in content
    assert 'Desert' in content

def test_perform_power_check_empty_input(tmp_path):
    """Test power check with empty input."""
    stratified = {}
    log_file = tmp_path / "skipped_strata.log"
    
    valid, skipped = perform_power_check(stratified, min_samples=10, log_path=str(log_file))
    
    assert len(valid) == 0
    assert len(skipped) == 0
    assert log_file.exists()