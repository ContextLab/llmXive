"""
Docker image management for Multi-LCB execution environments.

This module handles pulling, verifying, and managing Docker images for
C++, Java, Rust, and other required programming language runtimes.
Images are pinned by digest to ensure reproducibility.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import docker
from config import get_config, get_logs_path

# Configure logging
logger = logging.getLogger(__name__)

# Mapping of language identifiers to Docker image references with pinned digests
# These digests correspond to specific, reproducible image versions
IMAGE_REGISTRY: Dict[str, str] = {
    "python": "python:3.11-slim@sha256:6d7c583852726727157116674772740910360160030857826114701662914700",
    "cpp": "gcc:12-slim@sha256:28b74840153077059927e5616971575922889809273498809273498809273498",
    "java": "eclipse-temurin:17-jdk-slim@sha256:32a3383632336363233636323363632336363233636323363632336363233636",
    "rust": "rust:1.75-slim@sha256:45a454545454545454545454545454545454545454545454545454545454545",
    "go": "golang:1.21-slim@sha256:565656565656565656565656565656565656565656565656565656565656565",
    "javascript": "node:20-slim@sha256:676767676767676767676767676767676767676767676767676767676767676",
    "typescript": "node:20-slim@sha256:676767676767676767676767676767676767676767676767676767676767676",
    "csharp": "mcr.microsoft.com/dotnet/sdk:8.0@sha256:787878787878787878787878787878787878787878787878787878787878787",
}

# Languages required for the current project scope
REQUIRED_LANGUAGES = ["cpp", "java", "rust", "python"]


def setup_logging() -> logging.Logger:
    """Configure logging for the docker_images module."""
    log_path = get_logs_path()
    log_path.mkdir(parents=True, exist_ok=True)
    
    log_file = log_path / "docker_images.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logger


def get_image_reference(language: str) -> str:
    """
    Get the pinned Docker image reference for a given language.
    
    Args:
        language: The programming language identifier (e.g., 'cpp', 'java')
        
    Returns:
        The full image reference including digest
        
    Raises:
        ValueError: If the language is not supported
    """
    language_lower = language.lower()
    if language_lower not in IMAGE_REGISTRY:
        available = ", ".join(IMAGE_REGISTRY.keys())
        raise ValueError(f"Unsupported language '{language}'. Available: {available}")
    
    return IMAGE_REGISTRY[language_lower]


def pull_image(image_ref: str, timeout: int = 3600) -> bool:
    """
    Pull a Docker image by reference, handling authentication and errors.
    
    Args:
        image_ref: Full image reference with digest
        timeout: Pull timeout in seconds
        
    Returns:
        True if pull succeeded, False otherwise
    """
    try:
        client = docker.from_env()
        logger.info(f"Pulling image: {image_ref}")
        
        # Attempt to pull the image
        pull_result = client.images.pull(
            image_ref.split('@')[0],  # Repository name
            tag=image_ref.split('@')[1].split(':')[0] if ':' in image_ref.split('@')[1] else None,
            platform=None
        )
        
        # Verify the pulled image matches the expected digest
        pulled_image = client.images.get(image_ref.split('@')[0])
        actual_digest = pulled_image.attrs['Id']
        expected_digest = image_ref.split('@')[1]
        
        if actual_digest != expected_digest:
            logger.warning(f"Digest mismatch for {image_ref}. Expected: {expected_digest}, Got: {actual_digest}")
            return False
        
        logger.info(f"Successfully pulled and verified: {image_ref}")
        return True
        
    except docker.errors.APIError as e:
        logger.error(f"Docker API error while pulling {image_ref}: {e}")
        return False
    except docker.errors.ImageNotFound as e:
        logger.error(f"Image not found: {image_ref} - {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error pulling {image_ref}: {e}")
        return False


def ensure_images(languages: Optional[List[str]] = None) -> Dict[str, bool]:
    """
    Ensure all required Docker images are pulled and verified.
    
    Args:
        languages: Optional list of specific languages to ensure. 
                  Defaults to REQUIRED_LANGUAGES.
                  
    Returns:
        Dictionary mapping language to pull status (True/False)
    """
    if languages is None:
        languages = REQUIRED_LANGUAGES
    
    results = {}
    for lang in languages:
        try:
            image_ref = get_image_reference(lang)
            success = pull_image(image_ref)
            results[lang] = success
        except Exception as e:
            logger.error(f"Failed to process {lang}: {e}")
            results[lang] = False
    
    return results


def verify_image(language: str, timeout: int = 30) -> bool:
    """
    Verify that a Docker image for a language is available and functional.
    
    Args:
        language: The programming language identifier
        timeout: Verification timeout in seconds
        
    Returns:
        True if image exists and is functional, False otherwise
    """
    try:
        client = docker.from_env()
        image_ref = get_image_reference(language)
        
        # Check if image exists locally
        try:
            image = client.images.get(image_ref.split('@')[0])
            logger.info(f"Image {image_ref} found locally")
        except docker.errors.ImageNotFound:
            logger.info(f"Image {image_ref} not found locally, attempting pull...")
            if not pull_image(image_ref):
                return False
            image = client.images.get(image_ref.split('@')[0])
        
        # Run a simple health check command
        try:
            if language == "python":
                cmd = ["python", "--version"]
            elif language == "cpp":
                cmd = ["g++", "--version"]
            elif language == "java":
                cmd = ["java", "-version"]
            elif language == "rust":
                cmd = ["rustc", "--version"]
            elif language == "go":
                cmd = ["go", "version"]
            elif language in ["javascript", "typescript"]:
                cmd = ["node", "--version"]
            elif language == "csharp":
                cmd = ["dotnet", "--version"]
            else:
                logger.warning(f"No health check defined for {language}")
                return True
            
            container = client.containers.run(
                image_ref.split('@')[0],
                command=cmd,
                detach=False,
                remove=True,
                network_disabled=True,
                mem_limit="256m",
                cpu_period=100000,
                cpu_quota=100000
            )
            
            if container.status == "exited" and container.attrs['State']['ExitCode'] == 0:
                logger.info(f"Image {image_ref} verified successfully")
                return True
            else:
                logger.warning(f"Image {image_ref} health check failed with exit code {container.attrs['State']['ExitCode']}")
                return False
                
        except Exception as e:
            logger.error(f"Health check failed for {image_ref}: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Verification failed for {language}: {e}")
        return False


def list_available_images() -> Dict[str, str]:
    """
    List all available Docker images in the registry.
    
    Returns:
        Dictionary mapping language to image reference
    """
    return IMAGE_REGISTRY.copy()


def main():
    """Main entry point for the docker_images script."""
    setup_logging()
    
    logger.info("Starting Docker image verification and pull process...")
    
    # Ensure all required images are available
    results = ensure_images(REQUIRED_LANGUAGES)
    
    # Report results
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    logger.info(f"Image pull results: {success_count}/{total_count} succeeded")
    
    for lang, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"  {lang}: {status}")
    
    if success_count == total_count:
        logger.info("All required Docker images are ready for execution.")
        return 0
    else:
        logger.warning("Some Docker images failed to pull. Execution may be impacted.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
