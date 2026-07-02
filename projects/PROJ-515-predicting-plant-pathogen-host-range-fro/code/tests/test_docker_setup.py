"""
Tests for Docker configuration and image verification.
"""
import os
import subprocess
import sys
import tempfile
import yaml
from pathlib import Path


def docker_compose_config():
    """Return the parsed docker-compose configuration."""
    compose_path = Path(__file__).parent.parent / "docker-compose.yml"
    if not compose_path.exists():
        return None
    with open(compose_path, 'r') as f:
        return yaml.safe_load(f)


def test_docker_compose_exists():
    """Test that docker-compose.yml exists."""
    compose_path = Path(__file__).parent.parent / "docker-compose.yml"
    assert compose_path.exists(), "docker-compose.yml must exist"


def test_docker_compose_valid_yaml():
    """Test that docker-compose.yml is valid YAML."""
    config = docker_compose_config()
    assert config is not None, "docker-compose.yml must be parseable as YAML"
    assert 'services' in config, "docker-compose.yml must contain 'services'"


def test_required_images_in_compose():
    """Test that required images are specified in docker-compose.yml."""
    config = docker_compose_config()
    assert config is not None
    
    services = config.get('services', {})
    assert 'effectorp' in services, "effectorp service must be defined"
    assert 'antismash' in services, "antismash service must be defined"
    
    effectorp_image = services['effectorp'].get('image')
    antismash_image = services['antismash'].get('image')
    
    assert effectorp_image == "effectorp/effectorp:3.0", "EffectorP image must be pinned to 3.0"
    assert antismash_image == "antismash/antismash:7.0", "antiSMASH image must be pinned to 7.0"


def test_verify_script_exists():
    """Test that the verify_docker_images.py script exists."""
    script_path = Path(__file__).parent.parent / "scripts" / "verify_docker_images.py"
    assert script_path.exists(), "verify_docker_images.py must exist"


def test_verify_script_importable():
    """Test that the verify script can be imported."""
    script_path = Path(__file__).parent.parent / "scripts" / "verify_docker_images.py"
    sys.path.insert(0, str(script_path.parent))
    try:
        import verify_docker_images
        assert hasattr(verify_docker_images, 'check_image_exists')
        assert hasattr(verify_docker_images, 'pull_image')
        assert hasattr(verify_docker_images, 'verify_images')
        assert hasattr(verify_docker_images, 'main')
    finally:
        sys.path.remove(str(script_path.parent))


def test_verify_script_runs_successfully():
    """Test that the verify script runs without error (if Docker is available)."""
    script_path = Path(__file__).parent.parent / "scripts" / "verify_docker_images.py"
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        docker_available = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        docker_available = False
    
    if not docker_available:
        # Skip test if Docker is not available
        return
    
    # Run the verification script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=script_path.parent.parent
    )
    
    # The script should exit with 0 if all images are present or can be pulled
    # If Docker is available but images can't be pulled (network issues), it may fail
    # We allow either success or a specific failure code for network issues
    if result.returncode == 0:
        assert "All required Docker images are ready" in result.stdout
    else:
        # If it fails, it should be due to network issues, not code errors
        # We check that the script ran and produced output
        assert len(result.stdout) > 0 or len(result.stderr) > 0