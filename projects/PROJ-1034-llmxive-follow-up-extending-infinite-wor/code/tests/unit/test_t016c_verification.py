import pytest
import os
import json
import tempfile
import pandas as pd
from pathlib import Path
from src.cli.run_simulation import (
    load_target_steps_from_config,
    verify_step_count,
    run_simulation_with_timeout,
    SimulationResult
)
from src.sim.eco_director import run_simulation as run_eco_simulation
from src.sim.neural_baseline import run_neural_baseline_proxy

class TestT016cVerification:
    
    def test_load_target_steps_from_config_exists(self, tmp_path):
        """Test loading target_steps from existing config file"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("target_steps: 1500\n")
        
        steps = load_target_steps_from_config(str(config_file))
        assert steps == 1500
    
    def test_load_target_steps_from_config_missing(self):
        """Test default value when config is missing"""
        steps = load_target_steps_from_config("nonexistent.yaml")
        assert steps == 1000  # Default fallback
    
    def test_load_target_steps_deferred(self, tmp_path):
        """Test handling of [deferred] value"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("target_steps: [deferred]\n")
        
        steps = load_target_steps_from_config(str(config_file))
        assert steps == 1000  # Should default to 1000
    
    def test_verify_step_count_met(self):
        """Test step count verification when met"""
        assert verify_step_count(1500, 1000) is True
        assert verify_step_count(1000, 1000) is True
    
    def test_verify_step_count_not_met(self):
        """Test step count verification when not met"""
        assert verify_step_count(500, 1000) is False
    
    def test_run_simulation_creates_parquet(self, tmp_path):
        """Test that simulation creates parquet file"""
        output_dir = str(tmp_path / "data")
        
        # Run a short simulation
        result = run_simulation_with_timeout(
            agent_type="ca_eco_director",
            target_steps=100,
            seed=42,
            time_limit=60,
            memory_limit_mb=1000,
            output_dir=output_dir
        )
        
        # Check parquet file exists
        parquet_file = Path(output_dir) / "simulation_results.parquet"
        assert parquet_file.exists(), f"Parquet file not found at {parquet_file}"
        
        # Verify content
        df = pd.read_parquet(parquet_file)
        assert len(df) > 0
        assert "step" in df.columns
        assert "coherence" in df.columns
    
    def test_run_simulation_time_bound_flag(self, tmp_path):
        """Test that Time-Bound flag is set when simulation times out"""
        output_dir = str(tmp_path / "data")
        
        # Run with very short timeout to force timeout
        result = run_simulation_with_timeout(
            agent_type="ca_eco_director",
            target_steps=10000,  # Large target
            seed=42,
            time_limit=1,  # Very short timeout
            memory_limit_mb=1000,
            output_dir=output_dir
        )
        
        assert "Time-Bound" in result.flags or result.status == "time-bound"
        
        # Check that partial parquet was created
        parquet_file = Path(output_dir) / "baseline_partial.parquet"
        if parquet_file.exists():
            df = pd.read_parquet(parquet_file)
            assert "flags" in df.columns or "status" in df.columns
    
    def test_status_log_created(self, tmp_path):
        """Test that status log JSON is created"""
        output_dir = str(tmp_path / "data")
        
        result = run_simulation_with_timeout(
            agent_type="neural_baseline",
            target_steps=50,
            seed=42,
            time_limit=60,
            memory_limit_mb=1000,
            output_dir=output_dir
        )
        
        # Find status log file
        log_files = list(Path(output_dir).glob("*_status.json"))
        assert len(log_files) > 0, "No status log file found"
        
        with open(log_files[0]) as f:
            log_data = json.load(f)
        
        assert "run_id" in log_data
        assert "steps_completed" in log_data
        assert "flags" in log_data
        assert "status" in log_data
    
    def test_step_count_verification_in_result(self, tmp_path):
        """Test that step count verification is reflected in result"""
        output_dir = str(tmp_path / "data")
        
        result = run_simulation_with_timeout(
            agent_type="ca_eco_director",
            target_steps=100,
            seed=42,
            time_limit=60,
            memory_limit_mb=1000,
            output_dir=output_dir
        )
        
        # If steps completed is less than target and not time-bound, 
        # Step-Constraint-Not-Met flag should be present
        if result.steps_completed < 100 and "Time-Bound" not in result.flags:
            assert "Step-Constraint-Not-Met" in result.flags