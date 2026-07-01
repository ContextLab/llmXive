"""
Tests for the environment setup script.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

# Add the parent directory of 'tests' to the path so we can import 'code'
code_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_env import ensure_venv, ensure_pip

class TestSetupEnv(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_venv_creation(self):
        """Test that a venv is created if it doesn't exist."""
        venv_path = Path(self.temp_dir) / "venv"
        self.assertFalse(venv_path.exists())
        
        # We need to mock the project root logic since ensure_venv looks at __file__
        # For this test, we will just check the subprocess logic by calling the function
        # in a controlled way. However, ensure_venv relies on __file__.resolve().parent.parent
        # which points to the actual project structure.
        # To test properly without mocking __file__, we will run the script as a subprocess
        # in the temp dir.
        
        script_path = code_dir / "setup_env.py"
        # Copy script to temp dir to make path resolution work for the test
        temp_script = Path(self.temp_dir) / "setup_env.py"
        shutil.copy(script_path, temp_script)
        
        result = subprocess.run(
            [sys.executable, str(temp_script)],
            capture_output=True,
            text=True,
            cwd=self.temp_dir
        )
        
        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")
        self.assertTrue(venv_path.exists(), "Virtual environment was not created")

    def test_venv_exists_no_recreation(self):
        """Test that the script does not fail if venv already exists."""
        venv_path = Path(self.temp_dir) / "venv"
        venv_path.mkdir(parents=True)
        
        script_path = code_dir / "setup_env.py"
        temp_script = Path(self.temp_dir) / "setup_env.py"
        shutil.copy(script_path, temp_script)
        
        result = subprocess.run(
            [sys.executable, str(temp_script)],
            capture_output=True,
            text=True,
            cwd=self.temp_dir
        )
        
        self.assertEqual(result.returncode, 0, f"Script failed when venv exists: {result.stderr}")
        self.assertIn("already exists", result.stdout)

    def test_pip_availability(self):
        """Test that pip is available after running the script."""
        venv_path = Path(self.temp_dir) / "venv"
        pip_path = venv_path / "Scripts" / "pip.exe" if os.name == "nt" else venv_path / "bin" / "pip"
        
        script_path = code_dir / "setup_env.py"
        temp_script = Path(self.temp_dir) / "setup_env.py"
        shutil.copy(script_path, temp_script)
        
        result = subprocess.run(
            [sys.executable, str(temp_script)],
            capture_output=True,
            text=True,
            cwd=self.temp_dir
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertTrue(pip_path.exists(), "Pip executable not found in venv")

if __name__ == "__main__":
    unittest.main()
