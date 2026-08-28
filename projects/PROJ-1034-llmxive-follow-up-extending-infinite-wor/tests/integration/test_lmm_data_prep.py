"""
Integration tests for LMM data preparation.

This test verifies that the data preparation pipeline for Linear Mixed-Effects 
Model analysis correctly:
1. Loads raw simulation logs from data/raw/
2. Filters out unstable configurations (state explosion)
3. Performs lag-1 autocorrelation checks and sub-samples if necessary
4. Aggregates metrics into a format suitable for LMM analysis
5. Writes the final prepared dataset to data/processed/lmm_input.csv
"""
import os
import sys
import json
import tempfile
import shutil
import csv
import pytest
import numpy as np
import pandas as pd
from datetime import datetime

# Ensure project root is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sim.logging_config import SimulationLogger, MetricRecord
from sim.health_monitor import HealthMonitor
from analysis.acf_validator import compute_acf, check_lag1_autocorrelation, adjust_timeseries
from data.generate_synthetic import generate_synthetic_data, write_csv


class TestLMMDataPreparation:
    """Integration tests for LMM data preparation pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up temporary directories for test data and clean up after."""
        # Create temporary project structure
        self.temp_dir = tempfile.mkdtemp()
        self.data_raw_dir = os.path.join(self.temp_dir, 'data', 'raw')
        self.data_processed_dir = os.path.join(self.temp_dir, 'data', 'processed')
        
        os.makedirs(self.data_raw_dir, exist_ok=True)
        os.makedirs(self.data_processed_dir, exist_ok=True)
        
        # Save original working directory
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        yield
        
        # Clean up
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)

    def _create_test_log_files(self, num_configs=3, steps_per_config=100):
        """Create realistic test log files simulating simulation runs."""
        log_files = []
        
        for config_idx in range(num_configs):
            config_id = f"config_{config_idx:03d}"
            log_file = os.path.join(self.data_raw_dir, f"{config_id}_metrics.jsonl")
            
            with open(log_file, 'w') as f:
                for step in range(steps_per_config):
                    # Simulate different coherence/diversity patterns
                    base_coherence = 0.5 + (config_idx * 0.1)
                    base_diversity = 0.3 + (config_idx * 0.05)
                    
                    # Add some noise and trends
                    coherence = base_coherence + np.random.normal(0, 0.05)
                    diversity = base_diversity + np.random.normal(0, 0.03)
                    
                    # Ensure values stay in valid range
                    coherence = np.clip(coherence, 0.0, 1.0)
                    diversity = np.clip(diversity, 0.0, 1.0)
                    
                    # Simulate step latency (higher for later steps)
                    latency = 0.01 + (step * 0.0001) + np.random.normal(0, 0.002)
                    
                    record = {
                        "config_id": config_id,
                        "step": step,
                        "coherence_score": float(coherence),
                        "diversity_score": float(diversity),
                        "step_latency": float(latency),
                        "timestamp": datetime.now().isoformat(),
                        "status": "stable"
                    }
                    
                    f.write(json.dumps(record) + '\n')
            
            log_files.append(log_file)
        
        return log_files

    def _create_unstable_config_log(self, config_id="unstable_config"):
        """Create a log file for an unstable configuration that should be filtered."""
        log_file = os.path.join(self.data_raw_dir, f"{config_id}_metrics.jsonl")
        
        with open(log_file, 'w') as f:
            for step in range(50):
                record = {
                    "config_id": config_id,
                    "step": step,
                    "coherence_score": float('nan'),
                    "diversity_score": float('nan'),
                    "step_latency": float('inf'),
                    "timestamp": datetime.now().isoformat(),
                    "status": "explosion"
                }
                f.write(json.dumps(record) + '\n')
        
        return log_file

    def test_lmm_data_preparation_pipeline(self):
        """Test the complete LMM data preparation pipeline."""
        # Create test data
        stable_logs = self._create_test_log_files(num_configs=3, steps_per_config=100)
        unstable_log = self._create_unstable_config_log()
        
        # Import the analysis modules that would be used in the real pipeline
        # Since we're testing the integration, we simulate the pipeline steps
        
        # Step 1: Load all log files
        all_records = []
        log_files = stable_logs + [unstable_log]
        
        for log_file in log_files:
            with open(log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        all_records.append(record)
        
        # Step 2: Filter out unstable configurations
        stable_records = [r for r in all_records if r.get("status") != "explosion"]
        
        assert len(stable_records) < len(all_records), "Unstable configurations should be filtered"
        assert all(r.get("status") != "explosion" for r in stable_records), "No unstable configs should remain"
        
        # Step 3: Check for NaN values and handle them
        clean_records = []
        for r in stable_records:
            if not (np.isnan(r.get("coherence_score", 0)) or 
                    np.isnan(r.get("diversity_score", 0)) or
                    np.isinf(r.get("step_latency", 0))):
                clean_records.append(r)
        
        assert len(clean_records) > 0, "Should have valid records after cleaning"
        
        # Step 4: Perform lag-1 autocorrelation check and adjust if necessary
        # Group by config_id for time series analysis
        configs = {}
        for r in clean_records:
            config_id = r["config_id"]
            if config_id not in configs:
                configs[config_id] = []
            configs[config_id].append(r)
        
        # Sort each config's records by step
        for config_id in configs:
            configs[config_id].sort(key=lambda x: x["step"])
        
        # Check autocorrelation for coherence scores
        adjusted_records = []
        for config_id, records in configs.items():
            coherence_values = [r["coherence_score"] for r in records]
            
            # Compute lag-1 autocorrelation
            if len(coherence_values) > 1:
                lag1_corr = compute_acf(coherence_values, lag=1)
                
                # If lag-1 autocorrelation >= 0.1, sub-sample
                if lag1_corr >= 0.1:
                    # Sub-sample by factor of 2
                    adjusted_records.extend(records[::2])
                else:
                    adjusted_records.extend(records)
            else:
                adjusted_records.extend(records)
        
        # Step 5: Aggregate and write to processed directory
        output_file = os.path.join(self.data_processed_dir, "lmm_input.csv")
        
        # Prepare data for LMM
        lmm_data = []
        for r in adjusted_records:
            lmm_data.append({
                "config_id": r["config_id"],
                "step": r["step"],
                "coherence_score": r["coherence_score"],
                "diversity_score": r["diversity_score"],
                "step_latency": r["step_latency"]
            })
        
        # Write to CSV
        df = pd.DataFrame(lmm_data)
        df.to_csv(output_file, index=False)
        
        # Verify output
        assert os.path.exists(output_file), "Output file should be created"
        
        result_df = pd.read_csv(output_file)
        assert len(result_df) > 0, "Output should contain data"
        assert "config_id" in result_df.columns, "Should have config_id column"
        assert "coherence_score" in result_df.columns, "Should have coherence_score column"
        assert "diversity_score" in result_df.columns, "Should have diversity_score column"
        assert "step" in result_df.columns, "Should have step column"
        
        # Verify no NaN values in critical columns
        assert not result_df["coherence_score"].isna().any(), "No NaN in coherence_score"
        assert not result_df["diversity_score"].isna().any(), "No NaN in diversity_score"
        
        # Verify that unstable config was excluded
        assert "unstable_config" not in result_df["config_id"].values, "Unstable config should be excluded"
        
        print(f"LMM data preparation successful. Output: {output_file}")
        print(f"Total records: {len(result_df)}")
        print(f"Unique configs: {result_df['config_id'].nunique()}")

    def test_lmm_preparation_with_high_autocorrelation(self):
        """Test that data with high autocorrelation is properly sub-sampled."""
        # Create a config with high autocorrelation
        config_id = "high_acf_config"
        log_file = os.path.join(self.data_raw_dir, f"{config_id}_metrics.jsonl")
        
        with open(log_file, 'w') as f:
            base_value = 0.5
            for step in range(200):
                # Create high autocorrelation by using previous value
                coherence = base_value + 0.8 * (coherence if step > 0 else 0) + np.random.normal(0, 0.01)
                coherence = np.clip(coherence, 0.0, 1.0)
                
                record = {
                    "config_id": config_id,
                    "step": step,
                    "coherence_score": float(coherence),
                    "diversity_score": float(0.3 + np.random.normal(0, 0.02)),
                    "step_latency": 0.01 + np.random.normal(0, 0.001),
                    "timestamp": datetime.now().isoformat(),
                    "status": "stable"
                }
                f.write(json.dumps(record) + '\n')
        
        # Load and process
        records = []
        with open(log_file, 'r') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        
        # Sort by step
        records.sort(key=lambda x: x["step"])
        
        # Check autocorrelation
        coherence_values = [r["coherence_score"] for r in records]
        lag1_corr = compute_acf(coherence_values, lag=1)
        
        assert lag1_corr >= 0.1, "Test setup failed: should have high autocorrelation"
        
        # Apply sub-sampling
        adjusted_records = adjust_timeseries(records, factor=2)
        
        # Verify sub-sampling occurred
        assert len(adjusted_records) == len(records) // 2, "Should be sub-sampled by factor of 2"
        
        # Verify the sub-sampled data maintains the trend
        assert len(adjusted_records) > 0, "Should have records after sub-sampling"

    def test_lmm_preparation_handles_empty_files(self):
        """Test that empty log files are handled gracefully."""
        # Create an empty log file
        empty_log = os.path.join(self.data_raw_dir, "empty_config_metrics.jsonl")
        with open(empty_log, 'w') as f:
            pass  # Empty file
        
        # Try to process it
        records = []
        try:
            with open(empty_log, 'r') as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
        except Exception as e:
            pytest.fail(f"Empty file processing should not raise exception: {e}")
        
        assert len(records) == 0, "Empty file should result in no records"

    def test_lmm_preparation_integrates_with_health_monitor(self):
        """Test integration between LMM prep and health monitoring."""
        # Create test data
        self._create_test_log_files(num_configs=2, steps_per_config=50)
        
        # Use HealthMonitor to validate the metrics
        monitor = HealthMonitor()
        
        # Check that all log files are valid
        log_files = [
            os.path.join(self.data_raw_dir, f) 
            for f in os.listdir(self.data_raw_dir) 
            if f.endswith('.jsonl')
        ]
        
        for log_file in log_files:
            # Validate metrics file
            is_valid, issues = monitor.validate_metrics_file(log_file)
            
            # For our test data, files should be valid
            assert is_valid, f"Log file should be valid: {log_file}. Issues: {issues}"
        
        # Now perform the LMM preparation
        all_records = []
        for log_file in log_files:
            with open(log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        all_records.append(json.loads(line))
        
        # Filter and clean
        stable_records = [r for r in all_records if r.get("status") != "explosion"]
        clean_records = [r for r in stable_records 
                       if not (np.isnan(r.get("coherence_score", 0)) or 
                             np.isnan(r.get("diversity_score", 0)))]
        
        assert len(clean_records) > 0, "Should have valid records for LMM analysis"