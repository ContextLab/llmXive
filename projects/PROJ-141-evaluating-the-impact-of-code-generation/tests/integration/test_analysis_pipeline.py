"""
Integration test for the full statistical analysis pipeline on sample data.

This test verifies that:
1. Real data can be loaded from the database (or a generated sample if DB is empty)
2. Statistical tests (paired t-test, Wilcoxon, Cohen's d) run correctly
3. Multiple comparison corrections (Bonferroni, Holm) are applied
4. Results are exported with valid trace_ids
5. The full pipeline executes end-to-end without errors
"""
import os
import sys
import json
import tempfile
import shutil
import unittest
from datetime import datetime, timezone
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.db_schema import get_connection, init_schema, verify_schema
from data.models import Participant, Session, Problem, Submission, Metric, Condition, ProblemSource
from analysis.data_loader import load_paired_data
from analysis.statistical_tests import (
    paired_ttest,
    wilcoxon_signed_rank,
    cohen_d,
    compute_effect_size_ci
)
from analysis.correction import bonferroni_correct, holm_correct
from analysis.traceability import generate_trace_id
from analysis.export import export_results
from config.settings import get_config


class TestAnalysisPipeline(unittest.TestCase):
    """Integration tests for the full analysis pipeline."""

    def setUp(self):
        """Set up a temporary database and populate with sample data."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_analysis.db')
        
        # Initialize schema
        conn = get_connection(self.db_path)
        init_schema(conn)
        conn.close()

        # Populate with realistic sample data
        self._populate_sample_data()

    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _populate_sample_data(self):
        """Populate the database with sample participant data for testing."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        # Create 5 participants with complete within-subject data
        for i in range(1, 6):
            participant_id = f"TEST_PART_{i:03d}"
            
            # Insert participant
            cursor.execute("""
                INSERT INTO participants (participant_id, email, experience_years, consent_date, irb_approval_id)
                VALUES (?, ?, ?, ?, ?)
            """, (participant_id, f"test{i}@example.com", 3, datetime.now(timezone.utc).isoformat(), "IRB-2024-001"))

            # Create two sessions (one per condition)
            for cond_idx, condition in enumerate([Condition.LLM_ASSISTED, Condition.BASELINE]):
                session_id = f"{participant_id}_S{cond_idx+1}"
                cursor.execute("""
                    INSERT INTO sessions (session_id, participant_id, condition, start_time, end_time, seed)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    participant_id,
                    condition.value,
                    datetime.now(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).isoformat(),
                    42 + i * 10
                ))

                # Add 3 problems per session
                for prob_idx in range(3):
                    problem_id = f"{session_id}_P{prob_idx+1}"
                    cursor.execute("""
                        INSERT INTO problems (problem_id, session_id, source, problem_name, difficulty, estimated_time)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        problem_id,
                        session_id,
                        ProblemSource.HUMANEVAL.value,
                        f"HumanEval_{prob_idx+1}",
                        "medium",
                        300
                    ))

                    # Add submission
                    submission_id = f"{problem_id}_SUB"
                    code = "def solution():\n    return True\n" if i % 2 == 0 else "def solution():\n    pass\n"
                    cursor.execute("""
                        INSERT INTO submissions (submission_id, problem_id, code, submission_time, is_valid)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        submission_id,
                        problem_id,
                        code,
                        datetime.now(timezone.utc).isoformat(),
                        True
                    ))

                    # Add metrics
                    # Simulate realistic: LLM-assisted is faster (lower time) and slightly better quality
                    if condition == Condition.LLM_ASSISTED:
                        time_val = 180.0 + i * 10  # Faster
                        pass_rate = 0.85 + i * 0.02
                        complexity = 5
                        warnings = 2
                    else:
                        time_val = 240.0 + i * 15  # Slower
                        pass_rate = 0.75 + i * 0.02
                        complexity = 7
                        warnings = 4

                    cursor.execute("""
                        INSERT INTO metrics (submission_id, time_seconds, pass_rate, cyclomatic_complexity, 
                                            test_coverage, static_warnings)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        submission_id,
                        time_val,
                        pass_rate,
                        complexity,
                        0.80,
                        warnings
                    ))

        conn.commit()
        conn.close()

    def test_01_load_paired_data(self):
        """Test loading paired participant data from the database."""
        data = load_paired_data(self.db_path)
        
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0, "Should load at least one participant pair")
        
        # Check structure
        for record in data:
            self.assertIn('participant_id', record)
            self.assertIn('condition_llm', record)
            self.assertIn('condition_baseline', record)
            
            llm_metrics = record['condition_llm']
            base_metrics = record['condition_baseline']
            
            self.assertIn('time_seconds', llm_metrics)
            self.assertIn('pass_rate', llm_metrics)
            self.assertIn('time_seconds', base_metrics)
            self.assertIn('pass_rate', base_metrics)

    def test_02_statistical_tests(self):
        """Test statistical test computations on loaded data."""
        data = load_paired_data(self.db_path)
        
        # Extract paired time values
        llm_times = [r['condition_llm']['time_seconds'] for r in data]
        base_times = [r['condition_baseline']['time_seconds'] for r in data]
        
        self.assertEqual(len(llm_times), len(base_times), "Paired data must have equal length")
        
        # Test paired t-test
        t_stat, p_val = paired_ttest(llm_times, base_times)
        self.assertIsInstance(t_stat, float)
        self.assertIsInstance(p_val, float)
        self.assertGreater(t_stat, 0, "LLM should be faster (positive t-stat)")
        
        # Test Wilcoxon
        z_stat, p_wilcox = wilcoxon_signed_rank(llm_times, base_times)
        self.assertIsInstance(z_stat, float)
        self.assertIsInstance(p_wilcox, float)
        
        # Test Cohen's d
        d, ci_lower, ci_upper = cohen_d(llm_times, base_times)
        self.assertIsInstance(d, float)
        self.assertGreater(d, 0, "Effect size should be positive")
        self.assertLess(ci_lower, d)
        self.assertGreater(ci_upper, d)

    def test_03_multiple_comparison_correction(self):
        """Test multiple comparison correction methods."""
        # Create a list of p-values (simulating multiple metrics)
        p_values = [0.01, 0.03, 0.04, 0.02, 0.06]
        
        # Bonferroni
        corrected_bonf = bonferroni_correct(p_values, alpha=0.05)
        self.assertIsInstance(corrected_bonf, list)
        self.assertEqual(len(corrected_bonf), len(p_values))
        self.assertTrue(all(0 <= p <= 1 for p in corrected_bonf))
        
        # Holm
        corrected_holm = holm_correct(p_values, alpha=0.05)
        self.assertIsInstance(corrected_holm, list)
        self.assertEqual(len(corrected_holm), len(p_values))
        self.assertTrue(all(0 <= p <= 1 for p in corrected_holm))
        
        # Verify Holm is less conservative than Bonferroni
        for i in range(len(p_values)):
            self.assertGreaterEqual(corrected_holm[i], corrected_bonf[i],
                                  "Holm correction should be less conservative")

    def test_04_traceability_generation(self):
        """Test trace_id generation for results."""
        trace_id = generate_trace_id(
            data_row_id="TEST_PART_001",
            code_block_file="test_analysis_pipeline.py",
            code_block_line=100,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        self.assertIsInstance(trace_id, str)
        self.assertEqual(len(trace_id), 64)  # SHA-256 hex length
        self.assertTrue(all(c in '0123456789abcdef' for c in trace_id))

    def test_05_full_pipeline_execution(self):
        """Test the full analysis pipeline end-to-end."""
        output_file = os.path.join(self.temp_dir, 'analysis_results.json')
        
        # Load data
        data = load_paired_data(self.db_path)
        
        # Run statistical tests
        results = []
        for record in data:
            llm_time = record['condition_llm']['time_seconds']
            base_time = record['condition_baseline']['time_seconds']
            
            t_stat, p_val = paired_ttest([llm_time], [base_time])
            d, ci_l, ci_u = cohen_d([llm_time], [base_time])
            
            results.append({
                'participant_id': record['participant_id'],
                'metric': 'time_seconds',
                't_statistic': t_stat,
                'p_value': p_val,
                'cohen_d': d,
                'ci_lower': ci_l,
                'ci_upper': ci_u,
                'trace_id': generate_trace_id(
                    record['participant_id'],
                    'test_analysis_pipeline.py',
                    200,
                    datetime.now(timezone.utc).isoformat()
                )
            })
        
        # Apply correction
        p_values = [r['p_value'] for r in results]
        corrected = bonferroni_correct(p_values, alpha=0.05)
        for i, r in enumerate(results):
            r['p_value_corrected'] = corrected[i]
        
        # Export results
        export_results(results, output_file)
        
        # Verify output file exists and is valid JSON
        self.assertTrue(os.path.exists(output_file), "Output file should be created")
        
        with open(output_file, 'r') as f:
            exported = json.load(f)
        
        self.assertIsInstance(exported, list)
        self.assertEqual(len(exported), len(results))
        
        # Verify structure
        for item in exported:
            self.assertIn('participant_id', item)
            self.assertIn('p_value_corrected', item)
            self.assertIn('trace_id', item)
            self.assertEqual(len(item['trace_id']), 64)

    def test_06_non_normal_distribution_handling(self):
        """Test that Wilcoxon test handles non-normal data correctly."""
        # Create skewed data
        llm_times = [100, 110, 120, 130, 1000]  # Outlier
        base_times = [150, 160, 170, 180, 190]
        
        # Wilcoxon should handle this gracefully
        z_stat, p_val = wilcoxon_signed_rank(llm_times, base_times)
        
        self.assertIsInstance(z_stat, float)
        self.assertIsInstance(p_val, float)
        self.assertGreater(p_val, 0)
        self.assertLessEqual(p_val, 1)


if __name__ == '__main__':
    unittest.main()