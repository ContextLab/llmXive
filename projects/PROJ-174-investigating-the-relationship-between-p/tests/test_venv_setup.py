import subprocess
import sys
from pathlib import Path

def test_venv_exists():
    """Test that the virtual environment directory exists."""
    code_dir = Path(__file__).parent.parent
    venv_path = code_dir / '.venv'
    assert venv_path.exists(), f"Virtual environment not found at {venv_path}"
    assert (venv_path / 'bin' / 'python').exists(), f"Python executable not found in {venv_path}"

def test_python_version():
    """Test that the virtual environment uses Python 3.11.x."""
    code_dir = Path(__file__).parent.parent
    python_path = code_dir / '.venv' / 'bin' / 'python'
    
    result = subprocess.run(
        [str(python_path), '--version'],
        check=True,
        capture_output=True,
        text=True
    )
    
    version_output = result.stdout.strip()
    assert 'Python 3.11' in version_output, f"Expected Python 3.11.x, got: {version_output}"

def test_dependencies_installed():
    """Test that key dependencies are installed in the virtual environment."""
    code_dir = Path(__file__).parent.parent
    python_path = code_dir / '.venv' / 'bin' / 'python'
    
    # List of packages that should be installed according to requirements.txt
    required_packages = [
        'pandas', 'numpy', 'scipy', 'statsmodels', 'scikit-learn',
        'mne', 'pyyaml', 'tqdm', 'requests', 'datasets', 'python-dotenv'
    ]
    
    for package in required_packages:
        result = subprocess.run(
            [str(python_path), '-c', f'import {package}'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Package {package} is not installed or importable"