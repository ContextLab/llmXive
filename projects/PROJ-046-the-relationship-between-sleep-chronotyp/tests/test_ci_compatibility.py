"""
Unit tests for CI compatibility verification.
These tests mock the system checks to ensure the logic handles various scenarios correctly.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

# We need to import the actual functions from the module we are testing
# Since the module is named 07_verify_ci_compatibility.py, we import from it
import importlib.util
spec = importlib.util.spec_from_file_location("verify_ci", code_dir / "07_verify_ci_compatibility.py")
verify_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_module)

check_cpu_cores = verify_module.check_cpu_cores
check_ram_gb = verify_module.check_ram_gb
check_gpu = verify_module.check_gpu
check_r_installed = verify_module.check_r_installed
check_renv_initialized = verify_module.check_renv_initialized
main = verify_module.main

class TestCpuCheck(unittest.TestCase):
    def test_cpu_count_success(self):
        with patch("os.cpu_count", return_value=4):
            passed, count = check_cpu_cores()
            self.assertTrue(passed)
            self.assertEqual(count, 4)

    def test_cpu_count_insufficient(self):
        with patch("os.cpu_count", return_value=1):
            passed, count = check_cpu_cores()
            self.assertFalse(passed)
            self.assertEqual(count, 1)

    def test_cpu_count_fallback_nproc(self):
        with patch("os.cpu_count", return_value=None):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(stdout="2\n", returncode=0)
                passed, count = check_cpu_cores()
                self.assertTrue(passed)
                self.assertEqual(count, 2)

    def test_cpu_count_all_fallback(self):
        with patch("os.cpu_count", return_value=None):
            with patch("subprocess.run", side_effect=FileNotFoundError()):
                passed, count = check_cpu_cores()
                self.assertFalse(passed) # Falls back to 1, which is < 2
                self.assertEqual(count, 1)

class TestRamCheck(unittest.TestCase):
    def test_ram_linux_success(self):
        meminfo_content = "MemTotal:       16384000 kB"
        with patch("sys.platform", "linux"):
            with patch("builtins.open", mock_open(read_data=meminfo_content)):
                passed, total_gb = check_ram_gb()
                self.assertTrue(passed)
                self.assertAlmostEqual(total_gb, 15.63, places=1)

    def test_ram_linux_insufficient(self):
        meminfo_content = "MemTotal:       4096000 kB"
        with patch("sys.platform", "linux"):
            with patch("builtins.open", mock_open(read_data=meminfo_content)):
                passed, total_gb = check_ram_gb()
                self.assertFalse(passed)
                self.assertAlmostEqual(total_gb, 3.9, places=1)

    def test_ram_macos_success(self):
        with patch("sys.platform", "darwin"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(stdout="17179869184\n", returncode=0) # 16GB
                passed, total_gb = check_ram_gb()
                self.assertTrue(passed)
                self.assertAlmostEqual(total_gb, 16.0, places=1)

    def test_ram_windows_fallback(self):
        with patch("sys.platform", "win32"):
            passed, total_gb = check_ram_gb()
            self.assertFalse(passed) # Fallback returns False

    def test_ram_psutil_success(self):
        with patch("sys.platform", "linux"):
            with patch.dict("sys.modules", {"psutil": MagicMock()}):
                import psutil
                psutil.virtual_memory.return_value = MagicMock(total=8 * 1024**3)
                passed, total_gb = check_ram_gb()
                self.assertTrue(passed)
                self.assertAlmostEqual(total_gb, 8.0, places=1)

class TestGpuCheck(unittest.TestCase):
    def test_no_gpu(self):
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            passed, info = check_gpu()
            self.assertTrue(passed)
            self.assertEqual(info, "None")

    def test_nvidia_gpu_detected(self):
        with patch("subprocess.run") as mock_run:
            # First call (nvidia-smi) succeeds
            mock_run.side_effect = [
                MagicMock(stdout="0, NVIDIA GeForce RTX 3080, 10240", returncode=0),
                MagicMock(stdout="Apple M1", returncode=0) # Fallback for darwin check if needed, but we mock run
            ]
            # Actually, we only need to mock nvidia-smi
            mock_run.return_value = MagicMock(stdout="0, NVIDIA GeForce RTX 3080, 10240", returncode=0)
            passed, info = check_gpu()
            self.assertFalse(passed)
            self.assertIn("NVIDIA", info)

    def test_apple_silicon_detected(self):
        with patch("sys.platform", "darwin"):
            with patch("subprocess.run") as mock_run:
                # nvidia-smi fails
                mock_run.side_effect = [FileNotFoundError(), MagicMock(stdout="Apple M1", returncode=0)]
                passed, info = check_gpu()
                self.assertFalse(passed)
                self.assertIn("Apple", info)

class TestRCheck(unittest.TestCase):
    def test_r_installed_success(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="R version 4.3.0 (2023-04-21) -- \"Beagle Scouts\"\n", returncode=0)
            passed, version = check_r_installed()
            self.assertTrue(passed)
            self.assertEqual(version, "4.3.0")

    def test_r_not_installed(self):
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            passed, version = check_r_installed()
            self.assertFalse(passed)
            self.assertIsNone(version)

class TestRenvCheck(unittest.TestCase):
    def test_renv_initialized(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "renv.lock").touch()
            (project_root / "renv").mkdir()
            result = check_renv_initialized(project_root)
            self.assertTrue(result)

    def test_renv_not_initialized(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            result = check_renv_initialized(project_root)
            self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()