import pandas as pd
import numpy as np
import os
import sys
import json
import tempfile
import shutil

# Add parent directory to path to import code modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.preprocess import (
    clean_data, 
    normalize_and_flag_outliers, 
    extract_features, 
    save_preprocessed_data, 
    run_preprocessing
)

def test_extract_features():
    """
    Test T022: Feature Extraction.
    Verifies that mean_rt and avg_mood are computed correctly per participant/condition.
    """
    # Create a mock dataset with known values
    data = {
        'Participant ID': [1, 1, 1, 2, 2, 2],
        'Condition': ['Rejection', 'Control', 'Rejection', 'Control', 'Rejection', 'Control'],
        'Reaction Time': [100, 120, 110, 130, 140, 150],
        'Mood': [3.0, 5.0, 4.0, 4.5, 2.0, 6.0]
    }
    df = pd.DataFrame(data)
    
    # Run extraction
    result = extract_features(df)
    
    # Verify columns
    assert 'Participant ID' in result.columns
    assert 'Condition' in result.columns
    assert 'mean_rt' in result.columns
    assert 'avg_mood' in result.columns
    
    # Verify calculations for Participant 1, Rejection
    # RT: (100 + 110) / 2 = 105
    # Mood: (3.0 + 4.0) / 2 = 3.5
    p1_rej = result[(result['Participant ID'] == 1) & (result['Condition'] == 'Rejection')]
    assert not p1_rej.empty
    assert p1_rej['mean_rt'].values[0] == 105.0
    assert p1_rej['avg_mood'].values[0] == 3.5
    
    # Verify calculations for Participant 2, Control
    # RT: 150
    # Mood: 6.0
    p2_ctrl = result[(result['Participant ID'] == 2) & (result['Condition'] == 'Control')]
    assert not p2_ctrl.empty
    assert p2_ctrl['mean_rt'].values[0] == 150.0
    assert p2_ctrl['avg_mood'].values[0] == 6.0
    
    print("T022 Feature Extraction test passed.")

def test_extract_features_no_participant_id():
    """
    Test T022 fallback: Aggregation by Condition only when Participant ID is missing.
    """
    data = {
        'Condition': ['Rejection', 'Control', 'Rejection', 'Control'],
        'Reaction Time': [100, 120, 110, 130],
        'Mood': [3.0, 5.0, 4.0, 4.5]
    }
    df = pd.DataFrame(data)
    
    result = extract_features(df)
    
    assert 'Participant ID' not in result.columns
    assert 'Condition' in result.columns
    assert len(result) == 2  # One row per condition
    
    # Rejection: RT mean = (100+110)/2 = 105, Mood mean = 3.5
    rej_row = result[result['Condition'] == 'Rejection']
    assert abs(rej_row['mean_rt'].values[0] - 105.0) < 0.01
    assert abs(rej_row['avg_mood'].values[0] - 3.5) < 0.01
    
    print("T022 Fallback (no Participant ID) test passed.")

def test_run_preprocessing_integration():
    """
    Integration test for the full pipeline including T022 feature extraction.
    Verifies that output files are created on disk.
    """
    # Setup temp directory
    temp_dir = tempfile.mkdtemp()
    try:
        input_file = os.path.join(temp_dir, 'input.csv')
        output_file = os.path.join(temp_dir, 'output.csv')
        
        # Create input data
        data = {
            'Participant ID': [1, 1, 2, 2],
            'Condition': ['Rejection', 'Control', 'Rejection', 'Control'],
            'Reaction Time': [100.0, 120.0, 110.0, 130.0],
            'Mood': [3.0, 5.0, 4.0, 4.5]
        }
        pd.DataFrame(data).to_csv(input_file, index=False)
        
        # Run pipeline
        result = run_preprocessing(input_file, output_file, 'Within-Subjects')
        
        # Verify output file exists
        assert os.path.exists(output_file), f"Output file {output_file} was not created"
        
        # Verify metadata file exists
        metadata_file = output_file.replace('.csv', '_metadata.json')
        assert os.path.exists(metadata_file), f"Metadata file {metadata_file} was not created"
        
        # Verify content of output
        output_df = pd.read_csv(output_file)
        assert 'mean_rt' in output_df.columns
        assert 'avg_mood' in output_df.columns
        assert len(output_df) == 4  # 2 participants * 2 conditions
        
        print("T022 Integration test passed.")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_extract_features()
    test_extract_features_no_participant_id()
    test_run_preprocessing_integration()
    print("All T022 tests passed.")