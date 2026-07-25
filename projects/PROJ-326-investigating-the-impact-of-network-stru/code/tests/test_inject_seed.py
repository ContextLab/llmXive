"""
Tests for the seed injection and verification logic (T004b).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.src.utils.config import load_config
from code.scripts.inject_seed import verify_seeds, load_existing_log, main
from code.src.utils.reproducibility import generate_run_id

def test_verify_seeds_pass():
    """Test that verify_seeds returns PASS when seeds match config."""
    config = {
        "global_seed": 42,
        "generator_seed": 123,
        "simulation_seed": 456
    }
    seeds = {
        "global": 42,
        "generator": 123,
        "simulation": 456
    }
    assert verify_seeds(config, seeds) == "PASS"

def test_verify_seeds_fail_missing_key():
    """Test that verify_seeds returns FAIL when a seed key is missing."""
    config = {
        "global_seed": 42,
        "generator_seed": 123,
        "simulation_seed": 456
    }
    seeds = {
        "global": 42,
        "generator": 123
        # Missing 'simulation'
    }
    assert verify_seeds(config, seeds) == "FAIL"

def test_verify_seeds_fail_mismatch():
    """Test that verify_seeds returns FAIL when a seed value mismatches."""
    config = {
        "global_seed": 42,
        "generator_seed": 123,
        "simulation_seed": 456
    }
    seeds = {
        "global": 42,
        "generator": 999, # Mismatch
        "simulation": 456
    }
    assert verify_seeds(config, seeds) == "FAIL"

def test_verify_seeds_fail_missing_config():
    """Test that verify_seeds returns FAIL when config is missing keys."""
    config = {
        "global_seed": 42
        # Missing others
    }
    seeds = {
        "global": 42,
        "generator": 123,
        "simulation": 456
    }
    assert verify_seeds(config, seeds) == "FAIL"

def test_load_existing_log_creates_new():
    """Test that load_existing_log returns empty dict for non-existent file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent = Path(tmpdir) / "non_existent.json"
        result = load_existing_log(non_existent)
        assert result == {}

def test_load_existing_log_reads_valid():
    """Test that load_existing_log reads valid JSON correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_log.json"
        data = {"test": "value"}
        with open(log_path, 'w') as f:
            json.dump(data, f)
        
        result = load_existing_log(log_path)
        assert result == data

def test_generate_run_id_format():
    """Test that generated run ID has the expected format."""
    run_id = generate_run_id()
    parts = run_id.split('_')
    assert len(parts) >= 2
    # Check timestamp part (YYYYMMDD_HHMMSS)
    assert len(parts[0]) == 8
    assert len(parts[1]) == 6

def test_main_integration(tmp_path):
    """Integration test for main function with temporary files."""
    # Create a temporary config file
    config_content = """
    global_seed: 100
    generator_seed: 200
    simulation_seed: 300
    log_level: INFO
    topology_targets: {}
    simulation_params: {}
    analysis_params: {}
    simulation_timeout_seconds: 3600
    max_batch_size: 100
    data_dir: data
    figures_dir: paper
    results_dir: data/analysis
    """
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_content)
    
    log_path = tmp_path / "run_log.json"
    
    # Mock sys.argv to simulate command line arguments
    with patch('sys.argv', ['inject_seed.py', '--config', str(config_path), '--output', str(log_path)]):
        try:
            main()
        except SystemExit as e:
            assert e.code == 0, "main() should exit with 0 on success"
    
    # Verify log file was created
    assert log_path.exists(), "Log file should be created"
    
    # Verify content
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    assert isinstance(log_data, list), "Log should be a list"
    assert len(log_data) == 1, "Should have one entry"
    
    entry = log_data[0]
    assert "run_id" in entry
    assert "seeds" in entry
    assert entry["seeds"]["global"] == 100
    assert entry["seeds"]["generator"] == 200
    assert entry["seeds"]["simulation"] == 300
    assert entry["verification_status"] == "PASS"
    assert "timestamp" in entry

def test_main_fails_on_missing_config():
    """Test that main fails when config file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent_config = Path(tmpdir) / "missing.yaml"
        log_path = Path(tmpdir) / "log.json"
        
        with patch('sys.argv', ['inject_seed.py', '--config', str(non_existent_config), '--output', str(log_path)]):
            try:
                main()
            except SystemExit as e:
                assert e.code == 1, "main() should exit with 1 on failure"

def test_main_fails_on_seed_mismatch(tmp_path):
    """Test that main fails when seeds in config don't match expected logic (simulated)."""
    # This test verifies the logic flow, though in practice the script 
    # generates seeds FROM config, so mismatch only happens if config is malformed
    config_content = """
    global_seed: 100
    # Missing generator_seed and simulation_seed
    log_level: INFO
    topology_targets: {}
    simulation_params: {}
    analysis_params: {}
    simulation_timeout_seconds: 3600
    max_batch_size: 100
    data_dir: data
    figures_dir: paper
    results_dir: data/analysis
    """
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_content)
    log_path = tmp_path / "run_log.json"
    
    with patch('sys.argv', ['inject_seed.py', '--config', str(config_path), '--output', str(log_path)]):
        try:
            main()
        except SystemExit as e:
            assert e.code == 1, "main() should exit with 1 when config is incomplete"