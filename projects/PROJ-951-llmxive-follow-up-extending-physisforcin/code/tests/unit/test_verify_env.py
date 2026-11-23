"""
Unit tests for environment verification utilities.
"""
import pytest
import sys
from unittest.mock import patch, MagicMock
import importlib

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.verify_env import (
    check_package_installed,
    verify_pybullet_cpu_only,
    verify_mujoco_cpu_only,
    verify_pytorch_cpu_only,
    verify_cpu_only_environment
)
from pathlib import Path

class TestCheckPackageInstalled:
    def test_existing_package(self):
        """Test checking for a package that exists."""
        # os is always available
        assert check_package_installed('os') is True

    def test_nonexistent_package(self):
        """Test checking for a package that doesn't exist."""
        assert check_package_installed('nonexistent_package_xyz') is False

class TestVerifyPybulletCpuOnly:
    def test_pybullet_not_installed(self):
        """Test when PyBullet is not installed."""
        with patch('src.utils.verify_env.check_package_installed', return_value=False):
            success, msg = verify_pybullet_cpu_only()
            assert success is False
            assert "not installed" in msg

    @patch('src.utils.verify_env.importlib')
    @patch('src.utils.verify_env.subprocess')
    def test_pybullet_installed_but_connection_fails(self, mock_subprocess, mock_importlib):
        """Test when PyBullet is installed but connection fails."""
        mock_importlib.import_module.return_value = MagicMock()
        
        # Mock pybullet module
        mock_p = MagicMock()
        mock_p.connect.return_value = -1  # Connection failure
        
        with patch.dict(sys.modules, {'pybullet': mock_p}):
            success, msg = verify_pybullet_cpu_only()
            assert success is False
            assert "Failed to connect" in msg

    @patch('src.utils.verify_env.importlib')
    def test_pybullet_success(self, mock_importlib):
        """Test successful PyBullet verification."""
        mock_importlib.import_module.return_value = MagicMock()
        
        # Mock pybullet module with successful connection
        mock_p = MagicMock()
        mock_p.connect.return_value = 0  # Success
        mock_p.DIRECT = 0
        
        with patch.dict(sys.modules, {'pybullet': mock_p}):
            success, msg = verify_pybullet_cpu_only()
            assert success is True
            assert "PyBullet CPU mode verified" in msg

class TestVerifyMujocoCpuOnly:
    def test_mujoco_not_installed(self):
        """Test when MuJoCo is not installed."""
        with patch('src.utils.verify_env.check_package_installed', return_value=False):
            success, msg = verify_mujoco_cpu_only()
            assert success is False
            assert "not installed" in msg

    @patch('src.utils.verify_env.importlib')
    def test_mujoco_success(self, mock_importlib):
        """Test successful MuJoCo verification."""
        mock_importlib.import_module.return_value = MagicMock()
        
        # Mock mujoco and numpy
        mock_mujoco = MagicMock()
        mock_model = MagicMock()
        mock_data = MagicMock()
        
        mock_mujoco.MjModel.from_xml_string.return_value = mock_model
        mock_mujoco.MjData.return_value = mock_data
        
        with patch.dict(sys.modules, {'mujoco': mock_mujoco, 'numpy': MagicMock()}):
            success, msg = verify_mujoco_cpu_only()
            assert success is True
            assert "MuJoCo CPU mode verified" in msg

class TestVerifyPytorchCpuOnly:
    def test_pytorch_not_installed(self):
        """Test when PyTorch is not installed."""
        with patch('src.utils.verify_env.check_package_installed', return_value=False):
            success, msg = verify_pytorch_cpu_only()
            assert success is False
            assert "not installed" in msg

    def test_cuda_detected(self):
        """Test when CUDA is detected (should fail)."""
        with patch('src.utils.verify_env.check_package_installed', return_value=True):
            mock_torch = MagicMock()
            mock_torch.cuda.is_available.return_value = True
            mock_torch.cuda.get_device_name.return_value = "TestGPU"
            
            with patch.dict(sys.modules, {'torch': mock_torch}):
                success, msg = verify_pytorch_cpu_only()
                assert success is False
                assert "CUDA is detected" in msg

    def test_pytorch_cpu_success(self):
        """Test successful PyTorch CPU verification."""
        with patch('src.utils.verify_env.check_package_installed', return_value=True):
            mock_torch = MagicMock()
            mock_torch.cuda.is_available.return_value = False
            
            # Mock tensor operations
            mock_tensor = MagicMock()
            mock_tensor.__mul__.return_value.sum.return_value.item.return_value = 12.0
            mock_torch.tensor.return_value = mock_tensor
            
            with patch.dict(sys.modules, {'torch': mock_torch}):
                success, msg = verify_pytorch_cpu_only()
                assert success is True
                assert "PyTorch CPU-only mode verified" in msg

class TestVerifyCpuOnlyEnvironment:
    @patch('src.utils.verify_env.verify_pybullet_cpu_only')
    @patch('src.utils.verify_env.verify_mujoco_cpu_only')
    @patch('src.utils.verify_env.verify_pytorch_cpu_only')
    def test_all_pass(self, mock_torch, mock_mujoco, mock_pybullet):
        """Test when all checks pass."""
        mock_pybullet.return_value = (True, "PyBullet OK")
        mock_mujoco.return_value = (True, "MuJoCo OK")
        mock_torch.return_value = (True, "PyTorch OK")
        
        results = verify_cpu_only_environment()
        
        assert results['overall']['status'] == 'PASS'
        assert results['pybullet']['status'] == 'PASS'
        assert results['mujoco']['status'] == 'PASS'
        assert results['pytorch']['status'] == 'PASS'

    @patch('src.utils.verify_env.verify_pybullet_cpu_only')
    @patch('src.utils.verify_env.verify_mujoco_cpu_only')
    @patch('src.utils.verify_env.verify_pytorch_cpu_only')
    def test_one_fails(self, mock_torch, mock_mujoco, mock_pybullet):
        """Test when one check fails."""
        mock_pybullet.return_value = (False, "PyBullet failed")
        mock_mujoco.return_value = (True, "MuJoCo OK")
        mock_torch.return_value = (True, "PyTorch OK")
        
        results = verify_cpu_only_environment()
        
        assert results['overall']['status'] == 'FAIL'
        assert results['pybullet']['status'] == 'FAIL'
        assert results['mujoco']['status'] == 'PASS'
        assert results['pytorch']['status'] == 'PASS'