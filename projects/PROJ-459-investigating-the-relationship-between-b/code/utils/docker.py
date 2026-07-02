"""
Docker environment validation utilities for fMRIPrep readiness.

This module provides functions to validate the Docker daemon and ensure
the required fMRIPrep image is available before running heavy compute tasks.
"""

import subprocess
import sys
from typing import Tuple, Optional

# Default fMRIPrep image as per project configuration
FMRIPREP_IMAGE = "nipreps/fmriprep:23.1.3"

def validate_docker_daemon() -> Tuple[bool, str]:
    """
    Check if the Docker daemon is running and accessible.
    
    Returns:
        Tuple[bool, str]: (is_valid, message)
        - is_valid: True if Docker daemon is running
        - message: Human-readable status message
    """
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return True, "Docker daemon is running and accessible."
        else:
            return False, f"Docker command failed: {result.stderr.strip()}"
            
    except FileNotFoundError:
        return False, "Docker is not installed or not in PATH."
    except subprocess.TimeoutExpired:
        return False, "Docker daemon response timed out."
    except Exception as e:
        return False, f"Unexpected error checking Docker daemon: {str(e)}"

def check_fmriprep_image(required_image: Optional[str] = None) -> Tuple[bool, str]:
    """
    Check if the required fMRIPrep Docker image is available locally.
    
    Args:
        required_image: The Docker image to check. Defaults to FMRIPREP_IMAGE.
        
    Returns:
        Tuple[bool, str]: (is_available, message)
        - is_available: True if image exists locally
        - message: Human-readable status message
    """
    image_name = required_image or FMRIPREP_IMAGE
    
    try:
        # List images and check if our required image exists
        result = subprocess.run(
            ["docker", "images", image_name, "--format", "{{.Repository}}:{{.Tag}}"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return False, f"Failed to list Docker images: {result.stderr.strip()}"
        
        available_images = result.stdout.strip().split('\n')
        available_images = [img for img in available_images if img]
        
        if image_name in available_images:
            return True, f"fMRIPrep image '{image_name}' is available locally."
        else:
            return False, (
                f"fMRIPrep image '{image_name}' not found locally. "
                f"Run 'docker pull {image_name}' to download it."
            )
            
    except FileNotFoundError:
        return False, "Docker is not installed or not in PATH."
    except subprocess.TimeoutExpired:
        return False, "Docker image check timed out."
    except Exception as e:
        return False, f"Unexpected error checking fMRIPrep image: {str(e)}"

def pull_fmriprep_image(required_image: Optional[str] = None) -> Tuple[bool, str]:
    """
    Pull the required fMRIPrep Docker image if not present.
    
    Args:
        required_image: The Docker image to pull. Defaults to FMRIPREP_IMAGE.
        
    Returns:
        Tuple[bool, str]: (success, message)
        - success: True if pull succeeded or image already exists
        - message: Human-readable status message
    """
    image_name = required_image or FMRIPREP_IMAGE
    
    # First check if image exists
    exists, msg = check_fmriprep_image(image_name)
    if exists:
        return True, msg
    
    # Image not found, attempt to pull
    try:
        print(f"Pulling fMRIPrep image: {image_name}...")
        result = subprocess.run(
            ["docker", "pull", image_name],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout for large image
        )
        
        if result.returncode == 0:
            return True, f"Successfully pulled fMRIPrep image '{image_name}'."
        else:
            return False, f"Failed to pull image: {result.stderr.strip()}"
            
    except FileNotFoundError:
        return False, "Docker is not installed or not in PATH."
    except subprocess.TimeoutExpired:
        return False, f"Timeout while pulling image '{image_name}'."
    except Exception as e:
        return False, f"Unexpected error pulling image: {str(e)}"

def validate_environment(required_image: Optional[str] = None) -> Tuple[bool, str]:
    """
    Perform full environment validation: Docker daemon + fMRIPrep image.
    
    Args:
        required_image: The Docker image to check. Defaults to FMRIPREP_IMAGE.
        
    Returns:
        Tuple[bool, str]: (is_valid, message)
        - is_valid: True if all checks pass
        - message: Comprehensive status message
    """
    daemon_valid, daemon_msg = validate_docker_daemon()
    if not daemon_valid:
        return False, f"Docker daemon check failed: {daemon_msg}"
    
    image_valid, image_msg = check_fmriprep_image(required_image)
    if not image_valid:
        return False, f"fMRIPrep image check failed: {image_msg}"
    
    return True, "Environment validation passed. Docker and fMRIPrep are ready."

def main():
    """CLI entry point for Docker environment validation."""
    print("=== fMRIPrep Docker Environment Validation ===\n")
    
    daemon_valid, daemon_msg = validate_docker_daemon()
    print(f"Docker Daemon: {'✓' if daemon_valid else '✗'} {daemon_msg}")
    
    if daemon_valid:
        image_valid, image_msg = check_fmriprep_image()
        print(f"fMRIPrep Image: {'✓' if image_valid else '✗'} {image_msg}")
        
        if not image_valid:
            print("\nAttempting to pull missing image...")
            pull_valid, pull_msg = pull_fmriprep_image()
            print(f"Pull Result: {'✓' if pull_valid else '✗'} {pull_msg}")
    else:
        print("\nCannot check fMRIPrep image without Docker daemon.")
        sys.exit(1)
    
    print("\n=== Validation Complete ===")
    sys.exit(0 if daemon_valid else 1)

if __name__ == "__main__":
    main()