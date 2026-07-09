"""
Unit tests for code/features/validity.py
Specifically testing missing value flagging logic.
"""
import pytest
import numpy as np
import pandas as pd
from features.validity import identify_missing_sensor_epochs, flag_missing_sensors

def test_identify_missing_sensor_epochs_below_threshold():
    """
    Test that epochs with missing data below the 5% threshold are NOT flagged.
    """
    # Create a synthetic epoch with 100 time points and 10 channels
    # 2 missing values out of 1000 total = 0.2% missing (well below 5%)
    data = np.random.rand(10, 100)
    # Introduce 2 NaNs
    data[0, 0] = np.nan
    data[5, 50] = np.nan

    df = pd.DataFrame(data.T, columns=[f'ch{i}' for i in range(10)])
    # Add an epoch_id column for context (though the function might not strictly need it if passed as array)
    df['epoch_id'] = 1

    # Threshold is 5% (0.05)
    threshold = 0.05
    
    # Identify epochs exceeding the threshold
    flagged_epochs = identify_missing_sensor_epochs(df, threshold)
    
    # Since 0.2% < 5%, the list should be empty
    assert len(flagged_epochs) == 0, "Epochs with < 5% missing data should not be flagged."

def test_identify_missing_sensor_epochs_above_threshold():
    """
    Test that epochs with missing data above the 5% threshold ARE flagged.
    """
    # Create a synthetic epoch with 100 time points and 10 channels
    # 1000 total values. We need > 50 missing values to exceed 5%.
    data = np.random.rand(10, 100)
    
    # Introduce 60 NaNs (6% missing)
    count = 0
    for r in range(10):
        for c in range(100):
            if count < 60:
                data[r, c] = np.nan
                count += 1

    df = pd.DataFrame(data.T, columns=[f'ch{i}' for i in range(10)])
    df['epoch_id'] = 101

    threshold = 0.05
    flagged_epochs = identify_missing_sensor_epochs(df, threshold)

    # Since 6% > 5%, this epoch should be flagged
    assert 101 in flagged_epochs, "Epochs with > 5% missing data should be flagged."
    assert len(flagged_epochs) == 1

def test_identify_missing_sensor_epochs_multiple_epochs():
    """
    Test identification across multiple epochs with varying missing data.
    """
    # Epoch 1: 0% missing
    data1 = np.random.rand(10, 100)
    df1 = pd.DataFrame(data1.T, columns=[f'ch{i}' for i in range(10)])
    df1['epoch_id'] = 1

    # Epoch 2: 10% missing (100 NaNs out of 1000)
    data2 = np.random.rand(10, 100)
    for r in range(10):
        for c in range(10): # 10 * 10 = 100 NaNs
            data2[r, c] = np.nan
    df2 = pd.DataFrame(data2.T, columns=[f'ch{i}' for i in range(10)])
    df2['epoch_id'] = 2

    # Epoch 3: 4% missing (40 NaNs)
    data3 = np.random.rand(10, 100)
    for r in range(4):
        for c in range(10): # 4 * 10 = 40 NaNs
            data3[r, c] = np.nan
    df3 = pd.DataFrame(data3.T, columns=[f'ch{i}' for i in range(10)])
    df3['epoch_id'] = 3

    # Combine
    combined_df = pd.concat([df1, df2, df3], ignore_index=True)

    threshold = 0.05
    flagged_epochs = identify_missing_sensor_epochs(combined_df, threshold)

    # Expected: Only epoch 2 (10% missing)
    assert sorted(flagged_epochs) == [2], f"Expected [2], got {sorted(flagged_epochs)}"

def test_flag_missing_sensors():
    """
    Test that specific sensors are correctly identified as missing across the dataset.
    """
    data = np.random.rand(10, 100)
    # Make channel 0 and channel 5 completely missing (all NaN)
    data[0, :] = np.nan
    data[5, :] = np.nan

    df = pd.DataFrame(data.T, columns=[f'ch{i}' for i in range(10)])
    df['epoch_id'] = 1

    missing_sensors = flag_missing_sensors(df, threshold=0.9) # 90% missing means effectively missing

    # ch0 and ch5 should be in the list
    assert 'ch0' in missing_sensors, "ch0 should be flagged as missing."
    assert 'ch5' in missing_sensors, "ch5 should be flagged as missing."
    assert len(missing_sensors) == 2

def test_flag_missing_sensors_partial():
    """
    Test that sensors with partial missing data are flagged if above threshold.
    """
    data = np.random.rand(10, 100)
    # Make channel 2 have 60% missing
    data[2, :60] = np.nan

    df = pd.DataFrame(data.T, columns=[f'ch{i}' for i in range(10)])
    df['epoch_id'] = 1

    # Threshold 0.5 (50%)
    missing_sensors = flag_missing_sensors(df, threshold=0.5)

    assert 'ch2' in missing_sensors, "ch2 should be flagged (>50% missing)."
    assert len(missing_sensors) == 1