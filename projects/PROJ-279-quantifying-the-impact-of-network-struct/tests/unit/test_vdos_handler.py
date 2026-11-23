import pytest
import numpy as np
from pathlib import Path
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

from vdos_handler import (
    load_vdos,
    calculate_participation_ratios,
    process_configs_with_vdos,
    save_vdos_missing_report,
    check_vdos_availability
)
from models.atomic_config import AtomicConfiguration
from config.env_config import get_processed_dir

class TestLoadVDOS:
    """Tests for load_vdos function"""
    
    def test_load_vdos_success(self, tmp_path):
        """Test successful loading of VDOS data"""
        # Setup
        vdos_dir = tmp_path / "vdos"
        vdos_dir.mkdir()
        config_id = "test_config_001"
        vdos_file = vdos_dir / f"vdos_{config_id}.npy"
        
        # Create dummy VDOS data
        dummy_vdos = np.random.rand(100, 50)
        np.save(vdos_file, dummy_vdos)
        
        # Mock get_processed_dir to return our temp path
        with patch('vdos_handler.get_processed_dir', return_value=tmp_path):
            result = load_vdos(config_id)
            
            assert result is not None
            assert result.shape == dummy_vdos.shape
            np.testing.assert_array_equal(result, dummy_vdos)
    
    def test_load_vdos_missing_file(self, tmp_path):
        """Test loading VDOS when file is missing"""
        vdos_dir = tmp_path / "vdos"
        vdos_dir.mkdir()
        config_id = "missing_config"
        
        with patch('vdos_handler.get_processed_dir', return_value=tmp_path):
            with pytest.raises(FileNotFoundError, match="VDOS data missing"):
                load_vdos(config_id)
    
    def test_load_vdos_corrupted_file(self, tmp_path):
        """Test loading VDOS when file is corrupted"""
        vdos_dir = tmp_path / "vdos"
        vdos_dir.mkdir()
        config_id = "corrupted_config"
        vdos_file = vdos_dir / f"vdos_{config_id}.npy"
        
        # Create a corrupted file (not a valid numpy array)
        vdos_file.write_text("not a numpy file")
        
        with patch('vdos_handler.get_processed_dir', return_value=tmp_path):
            with pytest.raises(Exception):
                load_vdos(config_id)

class TestCalculateParticipationRatios:
    """Tests for calculate_participation_ratios function"""
    
    def test_calculate_pr_basic(self):
        """Test basic PR calculation"""
        # Create simple test data
        vdos_data = np.array([
            [1.0, 0.0, 0.0],  # Localized mode
            [0.5, 0.5, 0.5],  # Extended mode
        ])
        frequencies = np.array([10.0, 20.0])
        
        pr_values = calculate_participation_ratios(vdos_data, frequencies)
        
        assert len(pr_values) == 2
        assert pr_values[0] <= 1.0  # Localized mode should have low PR
        assert pr_values[1] <= 1.0  # Extended mode should have higher PR
        
    def test_calculate_pr_zero_atoms(self):
        """Test PR calculation with zero atoms"""
        vdos_data = np.array([]).reshape(0, 0)
        frequencies = np.array([])
        
        with pytest.raises(ValueError):
            calculate_participation_ratios(vdos_data, frequencies)
            
    def test_calculate_pr_1d_array(self):
        """Test PR calculation with 1D array (should fail)"""
        vdos_data = np.array([1.0, 2.0, 3.0])
        frequencies = np.array([10.0])
        
        with pytest.raises(ValueError):
            calculate_participation_ratios(vdos_data, frequencies)

class TestProcessConfigsWithVDOS:
    """Tests for process_configs_with_vdos function"""
    
    def test_process_configs_mixed_results(self, tmp_path):
        """Test processing configs with some having VDOS and some missing"""
        # Setup
        vdos_dir = tmp_path / "vdos"
        vdos_dir.mkdir()
        
        # Create VDOS for one config
        config_id_1 = "config_with_vdos"
        vdos_file_1 = vdos_dir / f"vdos_{config_id_1}.npy"
        np.save(vdos_file_1, np.random.rand(10, 5))
        
        # Create configs
        config1 = AtomicConfiguration(
            id=config_id_1,
            atoms=np.random.rand(5, 3),
            metadata={}
        )
        config2 = AtomicConfiguration(
            id="config_without_vdos",
            atoms=np.random.rand(5, 3),
            metadata={}
        )
        
        configs = [config1, config2]
        
        with patch('vdos_handler.get_processed_dir', return_value=tmp_path):
            successful, missing_report = process_configs_with_vdos(configs)
            
            # Check results
            assert len(successful) == 1
            assert successful[0].id == config_id_1
            assert 'vdos_loaded' in successful[0].metadata
            assert successful[0].metadata['vdos_loaded'] is True
            
            assert len(missing_report['missing_ids']) == 1
            assert missing_report['missing_ids'][0] == "config_without_vdos"
    
    def test_process_configs_all_missing(self, tmp_path):
        """Test processing when all configs are missing VDOS"""
        config1 = AtomicConfiguration(id="c1", atoms=np.random.rand(5, 3), metadata={})
        config2 = AtomicConfiguration(id="c2", atoms=np.random.rand(5, 3), metadata={})
        
        with patch('vdos_handler.get_processed_dir', return_value=tmp_path):
            successful, missing_report = process_configs_with_vdos([config1, config2])
            
            assert len(successful) == 0
            assert len(missing_report['missing_ids']) == 2

class TestSaveVDOSMissingReport:
    """Tests for save_vdos_missing_report function"""
    
    def test_save_report_creates_file(self, tmp_path):
        """Test that report file is created"""
        report_data = {
            "total_configs": 5,
            "missing_vdos": [{"config_id": "c1", "reason": "missing"}],
            "missing_ids": ["c1"]
        }
        
        output_path = tmp_path / "vdos_missing_report.json"
        
        with patch('vdos_handler.get_processed_dir', return_value=tmp_path):
            result_path = save_vdos_missing_report(report_data, output_path)
            
            assert result_path.exists()
            assert result_path == output_path
            
            # Verify content
            with open(result_path, 'r') as f:
                saved_data = json.load(f)
                assert saved_data['total_configs'] == 5
                assert len(saved_data['missing_ids']) == 1

class TestCheckVDOSAvailability:
    """Tests for check_vdos_availability function"""
    
    def test_check_availability_mixed(self, tmp_path):
        """Test availability check with mixed results"""
        vdos_dir = tmp_path / "vdos"
        vdos_dir.mkdir()
        
        # Create VDOS for one config
        vdos_file = vdos_dir / "vdos_available.npy"
        np.save(vdos_file, np.random.rand(10, 5))
        
        config1 = AtomicConfiguration(id="available", atoms=np.random.rand(5, 3), metadata={})
        config2 = AtomicConfiguration(id="missing", atoms=np.random.rand(5, 3), metadata={})
        
        with patch('vdos_handler.get_processed_dir', return_value=tmp_path):
            result = check_vdos_availability([config1, config2])
            
            assert result['available'] == 1
            assert result['missing'] == 1
            assert 'available' in result['available_ids']
            assert 'missing' in result['missing_ids']
            assert result['availability_rate'] == 0.5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
