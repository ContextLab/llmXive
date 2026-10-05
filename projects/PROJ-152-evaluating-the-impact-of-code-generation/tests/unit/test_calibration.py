"""
Unit tests for code/calibration.py (T022c)
"""
import csv
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from calibration import load_csv, calculate_fpr_and_kappa

class TestCalibrationMetrics:
    def setup_method(self):
        """Setup temporary data for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        
        # Mock data: 10 snippets
        # 5 Vulnerable (Human=1), 5 Clean (Human=0)
        # Scanner A flags 3 of the 5 vulnerable (TP=3, FN=2)
        # Scanner A flags 2 of the 5 clean (FP=2, TN=3)
        # Scanner B flags 4 of the 5 vulnerable (TP=4, FN=1)
        # Scanner B flags 1 of the 5 clean (FP=1, TN=4)
        
        self.findings_data = [
            # Vulnerable snippets (Human=1)
            {'snippet_id': 's1', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_a', 'severity': 'high'},
            {'snippet_id': 's1', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_b', 'severity': 'high'},
            
            {'snippet_id': 's2', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_a', 'severity': 'high'},
            {'snippet_id': 's2', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_b', 'severity': 'high'},
            
            {'snippet_id': 's3', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_a', 'severity': 'high'},
            {'snippet_id': 's3', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_b', 'severity': 'high'},
            
            {'snippet_id': 's4', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_b', 'severity': 'high'}, # TP for B, FN for A
            {'snippet_id': 's5', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_b', 'severity': 'high'}, # TP for B, FN for A
            
            # Clean snippets (Human=0)
            {'snippet_id': 's6', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_a', 'severity': 'low'}, # FP
            {'snippet_id': 's6', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_b', 'severity': 'low'}, # FP
            {'snippet_id': 's7', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_a', 'severity': 'low'}, # FP
            {'snippet_id': 's8', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_b', 'severity': 'low'}, # FP (Wait, logic check: s8 should be TN for A if not flagged)
        ]
        
        # Correcting mock data for clarity:
        # Vulnerable (s1-s5): 
        #   scanner_a flags s1, s2, s3 (TP=3). Misses s4, s5 (FN=2).
        #   scanner_b flags s1, s2, s3, s4, s5 (TP=5).
        # Clean (s6-s10):
        #   scanner_a flags s6, s7 (FP=2). Misses s8, s9, s10 (TN=3).
        #   scanner_b flags s6 (FP=1). Misses s7, s8, s9, s10 (TN=4).
        
        self.findings_data = [
            # Vulnerable
            {'snippet_id': 's1', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_a', 'severity': 'high'},
            {'snippet_id': 's1', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_b', 'severity': 'high'},
            {'snippet_id': 's2', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_a', 'severity': 'high'},
            {'snippet_id': 's2', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_b', 'severity': 'high'},
            {'snippet_id': 's3', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_a', 'severity': 'high'},
            {'snippet_id': 's3', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_b', 'severity': 'high'},
            {'snippet_id': 's4', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_b', 'severity': 'high'},
            {'snippet_id': 's5', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_b', 'severity': 'high'},
            
            # Clean
            {'snippet_id': 's6', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_a', 'severity': 'low'},
            {'snippet_id': 's6', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_b', 'severity': 'low'},
            {'snippet_id': 's7', 'model': 'm1', 'prompt_id': 'p1', 'scanner': 'scanner_a', 'severity': 'low'},
        ]

        self.labels_data = [
            {'snippet_id': 's1', 'model': 'm1', 'prompt_id': 'p1', 'human_label': '1'},
            {'snippet_id': 's2', 'model': 'm1', 'prompt_id': 'p1', 'human_label': '1'},
            {'snippet_id': 's3', 'model': 'm1', 'prompt_id': 'p1', 'human_label': '1'},
            {'snippet_id': 's4', 'model': 'm1', 'prompt_id': 'p1', 'human_label': '1'},
            {'snippet_id': 's5', 'model': 'm1', 'prompt_id': 'p1', 'human_label': '1'},
            {'snippet_id': 's6', 'model': 'm1', 'prompt_id': 'p1', 'human_label': '0'},
            {'snippet_id': 's7', 'model': 'm1', 'prompt_id': 'p1', 'human_label': '0'},
            {'snippet_id': 's8', 'model': 'm1', 'prompt_id': 'p1', 'human_label': '0'},
            {'snippet_id': 's9', 'model': 'm1', 'prompt_id': 'p1', 'human_label': '0'},
            {'snippet_id': 's10', 'model': 'm1', 'prompt_id': 'p1', 'human_label': '0'},
        ]

    def teardown_method(self):
        self.temp_dir.cleanup()

    def test_fpr_calculation(self):
        # Construct findings dict
        findings = {}
        for row in self.findings_data:
            key = (row['snippet_id'], row['model'], row['prompt_id'])
            if key not in findings: findings[key] = {}
            findings[key][row['scanner']] = row['severity']

        # Construct labels dict
        labels = {}
        for row in self.labels_data:
            key = (row['snippet_id'], row['model'], row['prompt_id'])
            labels[key] = row['human_label'] == '1'

        fpr_results, kappa_results = calculate_fpr_and_kappa(findings, labels)

        # Scanner A:
        # TP=3 (s1,s2,s3), FN=2 (s4,s5)
        # FP=2 (s6,s7), TN=3 (s8,s9,s10)
        # FPR_A = 2 / (2+3) = 0.4
        assert 'scanner_a' in fpr_results
        assert 'm1' in fpr_results['scanner_a']
        assert abs(fpr_results['scanner_a']['m1'] - 0.4) < 0.001

        # Scanner B:
        # TP=5 (s1..s5), FN=0
        # FP=1 (s6), TN=4 (s7..s10)
        # FPR_B = 1 / (1+4) = 0.2
        assert 'scanner_b' in fpr_results
        assert 'm1' in fpr_results['scanner_b']
        assert abs(fpr_results['scanner_b']['m1'] - 0.2) < 0.001

    def test_kappa_calculation(self):
        # Construct findings dict
        findings = {}
        for row in self.findings_data:
            key = (row['snippet_id'], row['model'], row['prompt_id'])
            if key not in findings: findings[key] = {}
            findings[key][row['scanner']] = row['severity']

        # Construct labels dict
        labels = {}
        for row in self.labels_data:
            key = (row['snippet_id'], row['model'], row['prompt_id'])
            labels[key] = row['human_label'] == '1'

        fpr_results, kappa_results = calculate_fpr_and_kappa(findings, labels)

        # Scanner A:
        # TP=3, TN=3, FP=2, FN=2. Total=10.
        # Po = (3+3)/10 = 0.6
        # P_pred_pos = (3+2)/10 = 0.5
        # P_pred_neg = (2+3)/10 = 0.5
        # P_true_pos = (3+2)/10 = 0.5
        # P_true_neg = (2+3)/10 = 0.5
        # Pe = (0.5*0.5) + (0.5*0.5) = 0.25 + 0.25 = 0.5
        # Kappa = (0.6 - 0.5) / (1 - 0.5) = 0.1 / 0.5 = 0.2
        assert abs(kappa_results['scanner_a']['m1'] - 0.2) < 0.001

        # Scanner B:
        # TP=5, TN=4, FP=1, FN=0. Total=10.
        # Po = (5+4)/10 = 0.9
        # P_pred_pos = (5+1)/10 = 0.6
        # P_pred_neg = (0+4)/10 = 0.4
        # P_true_pos = (5+0)/10 = 0.5
        # P_true_neg = (1+4)/10 = 0.5
        # Pe = (0.6*0.5) + (0.4*0.5) = 0.3 + 0.2 = 0.5
        # Kappa = (0.9 - 0.5) / (1 - 0.5) = 0.4 / 0.5 = 0.8
        assert abs(kappa_results['scanner_b']['m1'] - 0.8) < 0.001

if __name__ == '__main__':
    pytest.main([__file__, '-v'])