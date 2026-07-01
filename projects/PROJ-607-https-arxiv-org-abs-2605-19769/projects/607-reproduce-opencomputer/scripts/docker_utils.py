"""
Docker utility functions for the OpenComputer reproduction pipeline.

Provides error handling wrappers for Docker operations (image build, container run, cleanup)
and disk quota checks.
"""
from __future__ import annotations

import os
import json
import logging
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path

import docker
from docker.errors import DockerException, ImageNotFound, NotFound, APIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
DISK_QUOTA_GB = 14.0
RESULTS_DIR = Path("projects/607-reproduce-opencomputer/results")
LOGS_DIR = Path("projects/607-reproduce-opencomputer/logs")


@dataclass
class Task:
    """Represents a task definition from task.schema.yaml."""
    task_id: str
    name: str
    command: str
    image: Optional[str] = None
    timeout: int = 300
    dependencies: List[str] = None

    def __post_init__(self) -> None:
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class DockerResult:
    """Standardized result container for Docker operations."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    container_id: Optional[str] = None
    error_message: Optional[str] = None

def get_client() -> docker.DockerClient:
    """
    Initialize and return a Docker client.
    
    Returns:
        docker.DockerClient: Initialized Docker client.
        
    Raises:
        RuntimeError: If Docker daemon is not available.
    """
    try:
        client = docker.from_env()
        # Verify connectivity
        client.ping()
        logger.info("Docker client initialized successfully.")
        return client
    except DockerException as e:
        logger.error(f"Failed to initialize Docker client: {e}")
        raise RuntimeError(f"Docker daemon not available: {e}") from e


def check_disk_quota() -> Tuple[bool, float]:
    """
    Check if available disk space is below the quota threshold.
    
    Returns:
        Tuple[bool, float]: (is_below_quota, available_space_gb)
    """
    try:
        # Get disk usage info from Docker
        client = get_client()
        info = client.info()
        
        # Attempt to get disk usage from the Docker daemon info
        # This varies by OS and Docker setup; fallback to os.statvfs if needed
        if "DockerRootDir" in info:
            root_dir = info["DockerRootDir"]
            stat = os.statvfs(root_dir)
            available_bytes = stat.f_bavail * stat.f_frsize
            available_gb = available_bytes / (1024 ** 3)
        else:
            # Fallback to current directory if DockerRootDir not available
            stat = os.statvfs(".")
            available_bytes = stat.f_bavail * stat.f_frsize
            available_gb = available_bytes / (1024 ** 3)
        
        is_below = available_gb < DISK_QUOTA_GB
        logger.info(f"Disk check: {available_gb:.2f} GB available (quota: {DISK_QUOTA_GB} GB)")
        return is_below, available_gb
        
    except Exception as e:
        logger.warning(f"Could not check disk quota: {e}")
        # Fail safely by assuming quota exceeded if we can't check
        return True, 0.0


def build_image(
    image_name: str,
    dockerfile_path: str,
    build_args: Optional[Dict[str, str]] = None,
    timeout: int = 600
) -> DockerResult:
    """
    Build a Docker image with error handling and logging.
    
    Args:
        image_name: Name for the built image.
        dockerfile_path: Path to the Dockerfile.
        build_args: Optional build arguments.
        timeout: Maximum build time in seconds.
        
    Returns:
        DockerResult: Standardized result object.
    """
    logger.info(f"Building image: {image_name}")
    start_time = time.time()
    
    try:
        client = get_client()
        
        # Check disk quota before building
        is_below, available_gb = check_disk_quota()
        if is_below:
            return DockerResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr="",
                error_message=f"Disk quota exceeded: {available_gb:.2f} GB available < {DISK_QUOTA_GB} GB required"
            )
        
        build_kwargs = {
            "path": dockerfile_path,
            "tag": image_name,
            "rm": True,
            "decode": True
        }
        
        if build_args:
            build_kwargs["buildargs"] = build_args
        
        # Stream build output
        for chunk in client.api.build(**build_kwargs):
            if "stream" in chunk:
                logger.info(f"Build: {chunk['stream'].strip()}")
            elif "error" in chunk:
                logger.error(f"Build error: {chunk['error']}")
                return DockerResult(
                    success=False,
                    exit_code=1,
                    stdout="",
                    stderr=chunk["error"],
                    error_message=chunk["error"]
                )
        
        duration = time.time() - start_time
        logger.info(f"Image built successfully in {duration:.2f}s: {image_name}")
        
        return DockerResult(
            success=True,
            exit_code=0,
            stdout=f"Image {image_name} built successfully",
            stderr="",
            error_message=None
        )
        
    except APIError as e:
        duration = time.time() - start_time
        logger.error(f"Docker API error during build: {e}")
        return DockerResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr=str(e),
            error_message=f"API Error: {e}"
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Unexpected error during build: {e}")
        return DockerResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr=str(e),
            error_message=f"Unexpected error: {e}"
        )


def run_container(
    image_name: str,
    task: Task,
    volumes: Optional[Dict[str, Dict[str, str]]] = None,
    environment: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None
) -> DockerResult:
    """
    Run a Docker container with error handling and automatic cleanup.
    
    Args:
        image_name: Name of the image to run.
        task: Task definition object.
        volumes: Optional volume mounts.
        environment: Optional environment variables.
        timeout: Override timeout for this run.
        
    Returns:
        DockerResult: Standardized result object.
    """
    effective_timeout = timeout if timeout is not None else task.timeout
    logger.info(f"Running container for task {task.task_id} with timeout {effective_timeout}s")
    
    client = get_client()
    container = None
    
    try:
        # Check if image exists
        try:
            client.images.get(image_name)
        except ImageNotFound:
            logger.warning(f"Image {image_name} not found, attempting to build...")
            # Attempt to find Dockerfile in expected locations
            possible_paths = [
                f"projects/607-reproduce-opencomputer/Dockerfile",
                f"projects/607-reproduce-opencomputer/{task.task_id}/Dockerfile",
                "Dockerfile"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    result = build_image(image_name, path)
                    if not result.success:
                        return result
                    break
            else:
                return DockerResult(
                    success=False,
                    exit_code=1,
                    stdout="",
                    stderr=f"Image {image_name} not found and no Dockerfile found",
                    error_message=f"Image {image_name} not found"
                )
        
        run_kwargs = {
            "image": image_name,
            "command": task.command,
            "remove": True,  # Auto-remove container after execution
            "detach": False,
            "stdout": True,
            "stderr": True
        }
        
        if volumes:
            run_kwargs["volumes"] = volumes
        if environment:
            run_kwargs["environment"] = environment
        
        # Run container
        output = client.containers.run(**run_kwargs)
        
        # Output is bytes, decode to string
        stdout_str = output.decode("utf-8") if isinstance(output, bytes) else str(output)
        
        logger.info(f"Container completed successfully for task {task.task_id}")
        
        return DockerResult(
            success=True,
            exit_code=0,
            stdout=stdout_str,
            stderr="",
            error_message=None
        )
        
    except NotFound as e:
        logger.error(f"Container or resource not found: {e}")
        return DockerResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr=str(e),
            error_message=f"Resource not found: {e}"
        )
    except APIError as e:
        logger.error(f"Docker API error during run: {e}")
        return DockerResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr=str(e),
            error_message=f"API Error: {e}"
        )
    except Exception as e:
        logger.error(f"Unexpected error running container: {e}")
        return DockerResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr=str(e),
            error_message=f"Unexpected error: {e}"
        )
    finally:
        # Cleanup any dangling containers if detach was used
        if container and container.id:
            try:
                container.remove(force=True)
                logger.info(f"Cleaned up container {container.id}")
            except Exception as e:
                logger.warning(f"Failed to remove container {container.id}: {e}")


def cleanup_images(images_to_remove: List[str]) -> int:
    """
    Remove specified Docker images.
    
    Args:
        images_to_remove: List of image names to remove.
        
    Returns:
        int: Number of images successfully removed.
    """
    client = get_client()
    removed_count = 0
    
    for image_name in images_to_remove:
        try:
            client.images.remove(image_name, force=True)
            logger.info(f"Removed image: {image_name}")
            removed_count += 1
        except NotFound:
            logger.warning(f"Image not found, skipping: {image_name}")
        except APIError as e:
            logger.error(f"Failed to remove image {image_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error removing image {image_name}: {e}")
    
    return removed_count


def load_task_from_json(json_path: str) -> Task:
    """
    Load a Task definition from a JSON file.
    
    Args:
        json_path: Path to the JSON file containing task definition.
        
    Returns:
        Task: Deserialized Task object.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return Task(
        task_id=data["task_id"],
        name=data["name"],
        command=data["command"],
        image=data.get("image"),
        timeout=data.get("timeout", 300),
        dependencies=data.get("dependencies", [])
    )


def ensure_directories() -> None:
    """Ensure required result and log directories exist."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Ensured directory structure exists.")