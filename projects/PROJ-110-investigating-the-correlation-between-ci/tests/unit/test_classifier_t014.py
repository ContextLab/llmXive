import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the function to test
# Assuming the project structure allows relative imports or installed package
# In the actual runner, this will be `from code.data.classifier import classify_metabolic_status`
# We use a relative import path compatible with pytest running from project root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.classifier import classify_metabolic_status

class TestClassifyMetabolicStatus:
    """Tests for T014: Implement classify_metabolic_status applying strict ATP-III thresholds."""

    def test_classifies_metabolic_syndrome_correctly(self):
        """Test that samples meeting >=3 criteria are classified as MetS."""
        # Create a DataFrame with a sample that meets 3 criteria
        # BMI >= 30, TG >= 150, Glucose >= 100
        data = {
            'BMI': [31.0],
            'TG': [160.0],
            'HDL': [55.0], # Normal for female
            'BP_Sys': [120.0],
            'BP_Dia': [80.0],
            'Glucose': [110.0],
            'Sex': ['Female']
        }
        df = pd.DataFrame(data)
        
        result = classify_metabolic_status(df)
        
        assert result['MetS_Status'].iloc[0] == 'MetS'
        assert result['MetS_Criteria_Count'].iloc[0] == 3

    def test_classifies_control_correctly(self):
        """Test that samples meeting <3 criteria are classified as Control."""
        # Create a DataFrame with a sample meeting only 1 criterion
        data = {
            'BMI': [25.0],
            'TG': [100.0],
            'HDL': [60.0],
            'BP_Sys': [120.0],
            'BP_Dia': [80.0],
            'Glucose': [90.0],
            'Sex': ['Male']
        }
        df = pd.DataFrame(data)
        
        result = classify_metabolic_status(df)
        
        assert result['MetS_Status'].iloc[0] == 'Control'
        assert result['MetS_Criteria_Count'].iloc[0] == 0

    def test_boundary_conditions_bmi(self):
        """Test strict threshold for BMI (29.9 vs 30.0)."""
        data = {
            'BMI': [29.9, 30.0, 30.1],
            'TG': [100.0, 100.0, 100.0],
            'HDL': [60.0, 60.0, 60.0],
            'BP_Sys': [120.0, 120.0, 120.0],
            'BP_Dia': [80.0, 80.0, 80.0],
            'Glucose': [90.0, 90.0, 90.0],
            'Sex': ['Male', 'Male', 'Male']
        }
        df = pd.DataFrame(data)
        result = classify_metabolic_status(df)
        
        # 29.9 should be < 30 (no obesity criterion)
        # 30.0 should be >= 30 (obesity criterion)
        # 30.1 should be >= 30 (obesity criterion)
        # Since other criteria are 0, count is 0, 1, 1
        assert result['MetS_Criteria_Count'].iloc[0] == 0
        assert result['MetS_Criteria_Count'].iloc[1] == 1
        assert result['MetS_Criteria_Count'].iloc[2] == 1

    def test_hdl_sex_dependent(self):
        """Test that HDL thresholds are sex-dependent."""
        # Male: < 40 is low
        # Female: < 50 is low
        data = {
            'BMI': [25.0, 25.0],
            'TG': [100.0, 100.0],
            'HDL': [39.0, 45.0], # 39 is low for male, 45 is low for female
            'BP_Sys': [120.0, 120.0],
            'BP_Dia': [80.0, 80.0],
            'Glucose': [90.0, 90.0],
            'Sex': ['Male', 'Female']
        }
        df = pd.DataFrame(data)
        result = classify_metabolic_status(df)
        
        # Male with HDL 39: 1 criterion
        # Female with HDL 45: 1 criterion
        assert result['MetS_Criteria_Count'].iloc[0] == 1
        assert result['MetS_Criteria_Count'].iloc[1] == 1

    def test_missing_columns_raises_error(self):
        """Test that missing required columns raise ValueError."""
        data = {
            'BMI': [25.0],
            'TG': [100.0]
            # Missing HDL, BP_Sys, BP_Dia, Glucose, Sex
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="Missing required columns"):
            classify_metabolic_status(df)

    def test_output_file_written(self):
        """Test that the function writes the output CSV if path is provided."""
        data = {
            'BMI': [31.0],
            'TG': [160.0],
            'HDL': [55.0],
            'BP_Sys': [120.0],
            'BP_Dia': [80.0],
            'Glucose': [110.0],
            'Sex': ['Female']
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_labels.csv"
            result = classify_metabolic_status(df, output_path=str(output_path))
            
            assert output_path.exists()
            written_df = pd.read_csv(output_path)
            assert 'MetS_Status' in written_df.columns
            assert len(written_df) == 1
            assert written_df['MetS_Status'].iloc[0] == 'MetS'

    def test_missing_data_handling_in_logic(self):
        """
        Test that the classification logic handles NaNs gracefully in the criteria calculation.
        Note: The task T015 handles the exclusion of rows with NaNs. 
        Here we test that the classification function doesn't crash on NaNs in specific columns 
        (though T015 will likely filter them before this function is called in the full pipeline).
        The current implementation returns False for NaN in HDL check, but we should ensure it doesn't crash.
        """
        data = {
            'BMI': [31.0, np.nan], # NaN BMI
            'TG': [160.0, 160.0],
            'HDL': [55.0, 55.0],
            'BP_Sys': [120.0, 120.0],
            'BP_Dia': [80.0, 80.0],
            'Glucose': [110.0, 110.0],
            'Sex': ['Female', 'Female']
        }
        df = pd.DataFrame(data)
        
        # This should not raise an error, but the criteria count might be NaN or 0 depending on implementation
        # Our implementation uses >= which returns False for NaN, so it should be safe.
        result = classify_metabolic_status(df)
        
        # The first row (BMI 31) should have 1 criterion (if others are 0) -> Count 1
        # The second row (BMI NaN) -> BMI >= 30 is False -> Count 0
        # We just verify it runs without crashing
        assert 'MetS_Status' in result.columns
        assert len(result) == 2