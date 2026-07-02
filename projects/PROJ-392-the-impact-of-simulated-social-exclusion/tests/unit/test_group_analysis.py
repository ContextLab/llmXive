import pytest
import pandas as pd
import numpy as np
import os
import sys
import tempfile
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.group_analysis import (
    load_beta_estimates,
    group_by_roi_event,
    perform_two_sample_ttest,
    bonferroni_correction,
    run_group_analysis,
    save_results
)

class TestGroupAnalysis:
    
    @pytest.fixture
    def sample_beta_data(self):
        """Create a mock beta estimates dataframe."""
        data = {
            'participant_id': [f'sub-{i:03d}' for i in range(1, 21)] * 2,
            'group': ['excluded'] * 10 + ['included'] * 10 + ['excluded'] * 10 + ['included'] * 10,
            'roi': ['VS'] * 20 + ['OFC'] * 20,
            'event_type': ['anticipation'] * 20 + ['receipt'] * 20,
            'beta_value': (
                [0.5] * 10 + [0.8] * 10 +  # VS Anticipation
                [0.6] * 10 + [0.9] * 10 +  # VS Receipt
                [0.4] * 10 + [0.7] * 10 +  # OFC Anticipation
                [0.5] * 10 + [0.8] * 10    # OFC Receipt
            )
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_csv_file(self, sample_beta_data):
        """Create a temporary CSV file with sample data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_beta_data.to_csv(f, index=False)
            yield f.name
        os.unlink(f.name)

    def test_load_beta_estimates(self, temp_csv_file):
        """Test loading beta estimates from CSV."""
        df = load_beta_estimates(temp_csv_file)
        assert len(df) == 40
        assert 'beta_value' in df.columns
        assert df['group'].unique().tolist() == ['excluded', 'included']

    def test_group_by_roi_event(self, sample_beta_data):
        """Test grouping by ROI and event type."""
        groups = group_by_roi_event(sample_beta_data)
        # Should have 4 groups: VS-anticipation, VS-receipt, OFC-anticipation, OFC-receipt
        assert len(groups) == 4
        assert ('VS', 'anticipation') in groups

    def test_perform_two_sample_ttest(self, sample_beta_data):
        """Test the t-test function."""
        excluded = sample_beta_data[sample_beta_data['group'] == 'excluded']['beta_value'].iloc[:10]
        included = sample_beta_data[sample_beta_data['group'] == 'included']['beta_value'].iloc[:10]
        
        result = perform_two_sample_ttest(excluded, included)
        
        assert 't_statistic' in result
        assert 'p_value' in result
        assert 'cohen_d' in result
        assert result['n_a'] == 10
        assert result['n_b'] == 10
        assert result['mean_a'] < result['mean_b'] # In our mock, excluded < included

    def test_bonferroni_correction(self):
        """Test Bonferroni correction logic."""
        p_values = [0.01, 0.02, 0.05]
        corrected = bonferroni_correction(p_values)
        
        assert len(corrected) == 3
        # Corrected values should be larger
        assert corrected[0] == min(0.01 * 3, 1.0)
        assert corrected[1] == min(0.02 * 3, 1.0)
        assert corrected[2] == min(0.05 * 3, 1.0)

    def test_run_group_analysis(self, sample_beta_data):
        """Test the full group analysis pipeline."""
        results = run_group_analysis(sample_beta_data)
        
        assert len(results) == 4
        # Check that corrected p-values are present
        for res in results:
            assert 'corrected_p_value' in res
            assert 'stars' in res
            assert 'is_significant' in res

    def test_save_results(self, sample_beta_data):
        """Test saving results to CSV."""
        results = run_group_analysis(sample_beta_data)
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            output_path = f.name
        
        try:
            save_results(results, output_path)
            
            assert os.path.exists(output_path)
            df = pd.read_csv(output_path)
            assert len(df) == 4
            assert 'roi' in df.columns
            assert 'corrected_p_value' in df.columns
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_empty_groups_handling(self, sample_beta_data):
        """Test handling of missing data in one group."""
        # Remove all 'included' data
        df = sample_beta_data[sample_beta_data['group'] == 'excluded'].copy()
        # Add a new row to trigger a group that might be empty
        df.loc[len(df)] = ['sub-999', 'included', 'VS', 'anticipation', 0.5]
        
        # This should not crash, but log a warning
        # We expect the function to handle the missing 'excluded' data for the new row
        # by skipping that specific combination if it results in an empty group
        # Note: The current implementation groups by (roi, event) then splits by group.
        # If one split is empty, perform_two_sample_ttest raises ValueError.
        # We need to ensure run_group_analysis handles this gracefully or the test reflects the current behavior.
        # Based on current code: perform_two_sample_ttest raises ValueError if len == 0.
        # Let's adjust the test to match the current strict behavior or verify the fix.
        # Current code: if len(excluded) == 0 or len(included) == 0: raise ValueError
        
        # To test the "skip" logic, we need the function to catch it. 
        # The current run_group_analysis does NOT catch the ValueError from perform_two_sample_ttest.
        # It calls perform_two_sample_ttest directly.
        # So this test should actually expect an error or we must modify the code to handle it.
        # Given the task is to implement the logic, and the logic says "compare groups",
        # if a group is missing, we cannot compare. 
        # However, robust code should handle this.
        # Let's verify the current implementation behavior:
        # In run_group_analysis:
        #   if len(excluded) == 0 or len(included) == 0:
        #       logger.warning(...)
        #       continue
        # So it DOES handle it.
        
        # Let's re-verify the logic in the fixture:
        # We have 'included' only for the new row, no 'excluded' for that specific ROI/Event.
        # So the group (VS, anticipation) will have 11 rows: 10 excluded (original) + 1 included (new).
        # Wait, the original data has 10 excluded and 10 included for VS-anticipation.
        # If we filter to only excluded, we lose the original includeds.
        # Then we add one included.
        # So for (VS, anticipation): 10 excluded, 1 included.
        # This is valid (non-zero).
        
        # Let's create a case where one group is truly empty.
        df_empty = sample_beta_data[sample_beta_data['group'] == 'excluded'].copy()
        # Add a new ROI/Event that only has 'included'
        df_empty.loc[len(df_empty)] = ['sub-999', 'included', 'NewROI', 'NewEvent', 0.5]
        
        # Now 'NewROI'/'NewEvent' has 0 excluded and 1 included.
        # This should trigger the warning and skip.
        results = run_group_analysis(df_empty)
        # The NewROI/NewEvent combination should NOT be in results
        roi_events = [(r['roi'], r['event_type']) for r in results]
        assert ('NewROI', 'NewEvent') not in roi_events