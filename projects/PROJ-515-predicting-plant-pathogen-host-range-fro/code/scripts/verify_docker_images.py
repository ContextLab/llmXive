"""
Script to verify and pull required Docker images for the pipeline.
This script ensures EffectorP and antiSMASH images are present before execution.
"""
import subprocess
import sys
import time
import yaml
import os
from pathlib import Path


def check_image_exists(image_name: str) -> bool:
    """Check if a Docker image is present locally."""
    try:
        result = subprocess.run(
            ["docker", "images", "-q", image_name],
            capture_output=True,
            text=True,
            check=True
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False


def pull_image(image_name: str, timeout: int = 300) -> bool:
    """Pull a Docker image with a timeout."""
    print(f"Pulling image: {image_name}")
    try:
        # Use a timeout to prevent hanging indefinitely
        result = subprocess.run(
            ["docker", "pull", image_name],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode != 0:
            print(f"Error pulling {image_name}: {result.stderr}")
            return False
        print(f"Successfully pulled {image_name}")
        return True
    except subprocess.TimeoutExpired:
        print(f"Timeout pulling {image_name}")
        return False
    except FileNotFoundError:
        print("Error: Docker is not installed or not in PATH")
        return False


def verify_images(images: list, timeout: int = 300) -> bool:
    """Verify all required images are present, pulling if necessary."""
    all_verified = True
    for image in images:
        if not check_image_exists(image):
            if not pull_image(image, timeout):
                all_verified = False
        else:
            print(f"Image already present: {image}")
    
    return all_verified


def main():
    """Main entry point for Docker image verification."""
    # Load the docker-compose.yml to get required images
    compose_path = Path(__file__).parent.parent / "docker-compose.yml"
    
    if not compose_path.exists():
        print(f"Error: {compose_path} not found")
        sys.exit(1)
    
    with open(compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Extract images from services
    required_images = []
    if 'services' in compose_config:
        for service_name, service_config in compose_config['services'].items():
            if 'image' in service_config:
                required_images.append(service_config['image'])
    
    if not required_images:
        print("No images found in docker-compose.yml")
        sys.exit(1)
    
    print(f"Verifying {len(required_images)} Docker images...")
    if verify_images(required_images):
        print("All required Docker images are ready.")
        sys.exit(0)
    else:
        print("Failed to verify all required Docker images.")
        sys.exit(1)


if __name__ == "__main__":
    main()
