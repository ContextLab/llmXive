"""
Tests for data processing logic, specifically focusing on trial filtering,
D-score calculation, and participant exclusion criteria.
"""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

# Import the functions under test
from code.data.process import filter_trials, calculate_d_score, aggregate_d_scores
from code.data.models import ParticipantResponse, AggregatedScore


class TestParticipantExclusion:
    """
    Integration test for participant exclusion logic when valid trials < 10.
    
    This test verifies that:
    1. Participants with fewer than 10 valid trials are excluded from the final aggregation.
    2. The exclusion is correctly flagged in the status field.
    3. The d_score is set to NaN for excluded participants.
    """

    def _generate_trial_data(
        self, 
        participant_id: str, 
        session_id: str, 
        n_trials: int, 
        include_errors: bool = False
    ) -> List[Dict[str, Any]]:
        """Helper to generate synthetic trial data."""
        trials = []
        for i in range(n_trials):
            # Create valid reaction times (between 300ms and 10000ms)
            rt = 500 + (i * 10) 
            is_error = include_errors and (i % 5 == 0)
            
            trial = {
                "participant_id": participant_id,
                "session_id": session_id,
                "trial_number": i,
                "reaction_time": rt,
                "is_error": is_error,
                "block_type": "practice" if i < 10 else "test",
                "timestamp": datetime.now().isoformat()
            }
            trials.append(trial)
        return trials

    def test_exclusion_threshold_boundary(self):
        """
        Test that a participant with exactly 9 valid trials is excluded,
        while one with 10 valid trials is included.
        """
        # Create data for a participant with 9 valid trials
        # We'll generate 9 trials, all within valid range
        low_count_trials = self._generate_trial_data(
            participant_id="P_LOW", 
            session_id="S1", 
            n_trials=9
        )
        
        # Create data for a participant with 10 valid trials
        valid_count_trials = self._generate_trial_data(
            participant_id="P_VALID", 
            session_id="S1", 
            n_trials=10
        )

        # Combine into a single list of dicts for the aggregate function
        all_trials = low_count_trials + valid_count_trials

        # Aggregate the data
        result_df = aggregate_d_scores(all_trials)

        # Verify results
        assert len(result_df) == 2, "Should have two participant-session records"

        # Check the excluded participant
        low_record = result_df[result_df['participant_id'] == 'P_LOW'].iloc[0]
        assert pd.isna(low_record['d_score']), "Excluded participant should have NaN d_score"
        assert low_record['status'] == 'excluded', "Status should be 'excluded' for <10 trials"
        assert low_record['n_trials_valid'] == 9, "Valid trial count should be 9"

        # Check the included participant
        valid_record = result_df[result_df['participant_id'] == 'P_VALID'].iloc[0]
        assert not pd.isna(valid_record['d_score']), "Valid participant should have a calculated d_score"
        assert valid_record['status'] == 'valid', "Status should be 'valid' for >=10 trials"
        assert valid_record['n_trials_valid'] == 10, "Valid trial count should be 10"

    def test_exclusion_with_filtering(self):
        """
        Test exclusion when initial trials are reduced by filtering (e.g., errors or latency bounds).
        
        Scenario: Participant has 15 trials, but 6 are errors. 
        Valid trials = 9. Should be excluded.
        """
        trials = self._generate_trial_data(
            participant_id="P_FILTERED", 
            session_id="S1", 
            n_trials=15, 
            include_errors=True
        )
        
        # Manually inject some out-of-bounds latencies to ensure they are filtered
        # Trials 0, 1, 2 will be < 300ms (invalid)
        for i in range(3):
            trials[i]['reaction_time'] = 100 

        # Total raw: 15
        # Errors (i%5==0): 0, 5, 10, 15 (but 15 is out of range, so 0, 5, 10) -> 3 errors
        # Latency < 300: 0, 1, 2 -> 3 trials
        # Note: Trial 0 is both error and low latency. 
        # Expected valid: 15 - 3 (errors) - 3 (latency) + 1 (overlap) = 10? 
        # Let's be precise:
        # 0: Error + Low (Invalid)
        # 1: Low (Invalid)
        # 2: Low (Invalid)
        # 3: Valid
        # 4: Valid
        # 5: Error (Invalid)
        # 6: Valid
        # 7: Valid
        # 8: Valid
        # 9: Valid
        # 10: Error (Invalid)
        # 11: Valid
        # 12: Valid
        # 13: Valid
        # 14: Valid
        # Total Valid: 3,4,6,7,8,9,11,12,13,14 -> 10 valid.
        # Wait, I need < 10 valid to trigger exclusion. 
        # Let's make 4 errors and 3 low latency (no overlap) -> 15 - 7 = 8 valid.
        
        # Reset trials for clarity
        trials = []
        for i in range(15):
            rt = 500 + (i * 10)
            is_error = False
            if i < 4: 
                is_error = True # 4 errors
            elif i < 7:
                rt = 100 # 3 low latency, no overlap with errors
            
            trials.append({
                "participant_id": "P_EXCLUDE",
                "session_id": "S1",
                "trial_number": i,
                "reaction_time": rt,
                "is_error": is_error,
                "block_type": "test",
                "timestamp": datetime.now().isoformat()
            })

        result_df = aggregate_d_scores(trials)
        
        assert len(result_df) == 1
        record = result_df.iloc[0]
        
        # 15 total - 4 errors - 3 low latency = 8 valid
        assert record['n_trials_valid'] == 8, f"Expected 8 valid trials, got {record['n_trials_valid']}"
        assert pd.isna(record['d_score']), "Participant with <10 valid trials should have NaN d_score"
        assert record['status'] == 'excluded', "Status should be 'excluded'"

    def test_edge_case_exact_ten(self):
        """
        Test that exactly 10 valid trials results in inclusion (status='valid').
        """
        trials = self._generate_trial_data(
            participant_id="P_EXACT", 
            session_id="S1", 
            n_trials=10
        )
        
        # Remove 1 trial by making it an error, leaving 9 valid -> Excluded
        trials[0]['is_error'] = True
        
        result_df = aggregate_d_scores(trials)
        record = result_df.iloc[0]
        
        assert record['n_trials_valid'] == 9
        assert record['status'] == 'excluded'

        # Now add one more valid trial to make it 10
        trials.append({
            "participant_id": "P_EXACT",
            "session_id": "S1",
            "trial_number": 10,
            "reaction_time": 600,
            "is_error": False,
            "block_type": "test",
            "timestamp": datetime.now().isoformat()
        })
        
        result_df = aggregate_d_scores(trials)
        record = result_df.iloc[0]
        
        assert record['n_trials_valid'] == 10
        assert record['status'] == 'valid'
        assert not pd.isna(record['d_score'])