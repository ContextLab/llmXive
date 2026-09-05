import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any

def get_docker_run_command(
    raw_dir: str,
    derivatives_dir: str,
    participant_label: Optional[str] = None,
    mem_limit: str = "4g"
) -> str:
    """
    Constructs the docker run command string for fmriprep.
    
    Args:
        raw_dir: Path to the raw BIDS dataset (mounted as /data:ro).
        derivatives_dir: Path to output derivatives (mounted as /out).
        participant_label: Optional single subject label (e.g., 'sub-01').
        mem_limit: Docker memory limit (e.g., '4g', '8g').
        
    Returns:
        The full docker run command as a string.
    """
    # Ensure directories exist and are absolute for clarity
    raw_path = Path(raw_dir).resolve()
    deriv_path = Path(derivatives_dir).resolve()
    
    # Base command
    cmd_parts = [
        "docker", "run", "--rm",
        "-v", f"{raw_path}:/data:ro",
        "-v", f"{deriv_path}:/out",
        "-e", "OMP_NUM_THREADS=1",
        "--memory", mem_limit,
        "--cpus", "2",
        "nipreps/fmriprep:latest"
    ]
    
    # Arguments for fmriprep
    fmriprep_args = [
        "/data", "/out", "participant",
        "--output-spaces", "MNI152NLin2009cAsym",
        "--fs-no-reconall",
        "--skip_bids_validation"  # Optional: if BIDS validation is handled elsewhere
    ]
    
    if participant_label:
        fmriprep_args.extend(["--participant-label", participant_label])
        
    cmd_parts.extend(fmriprep_args)
    
    return " ".join(cmd_parts)

def validate_docker_installation() -> bool:
    """
    Checks if Docker is installed and the daemon is running.
    
    Returns:
        True if Docker is valid, False otherwise.
    """
    try:
        result = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def pull_fmriprep_image(tag: str = "latest") -> bool:
    """
    Pulls the specified fmriprep Docker image.
    
    Args:
        tag: The image tag (default: 'latest').
        
    Returns:
        True if successful, False otherwise.
    """
    image_name = f"nipreps/fmriprep:{tag}"
    try:
        subprocess.run(
            ["docker", "pull", image_name],
            check=True
        )
        print(f"Successfully pulled {image_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to pull {image_name}: {e}")
        return False

def generate_config_file(
    raw_dir: str = "./data/raw",
    derivatives_dir: str = "./data/derivatives",
    output_path: str = "docker_fmriprep_config.yml"
) -> str:
    """
    Generates a YAML configuration file for Docker Compose to run fmriprep.
    
    Note: fmriprep is typically run via 'docker run' rather than 'docker-compose'
    for single jobs, but this provides a compose file for orchestration if needed.
    
    Args:
        raw_dir: Path to raw data.
        derivatives_dir: Path to derivatives.
        output_path: Path to save the YAML config.
        
    Returns:
        The path to the generated config file.
    """
    # Ensure directories exist
    Path(raw_dir).mkdir(parents=True, exist_ok=True)
    Path(derivatives_dir).mkdir(parents=True, exist_ok=True)
    
    config_content = f"""
version: '3.8'

services:
  fmriprep:
    image: nipreps/fmriprep:latest
    container_name: fmriprep_job
    environment:
- OMP_NUM_THREADS=1
    deploy:
resources:
  limits:
    memory: 4G
    volumes:
- {raw_dir}:/data:ro
- {derivatives_dir}:/out
    command:
- /data
- /out
- participant
- --output-spaces
- MNI152NLin2009cAsym
- --fs-no-reconall
- --skip_bids_validation
    # Note: Add --participant-label SUBJ_ID to the command list for specific subjects
"""
    
    with open(output_path, 'w') as f:
        f.write(config_content.strip())
        
    print(f"Docker Compose configuration written to {output_path}")
    return output_path

def main():
    """
    Main entry point to demonstrate Docker configuration for fmriprep.
    """
    if not validate_docker_installation():
        print("Error: Docker is not installed or the daemon is not running.")
        sys.exit(1)
    
    # Configuration parameters
    raw_dir = "./data/raw"
    derivatives_dir = "./data/derivatives"
    
    # Generate the docker-compose.yml file
    config_file = generate_config_file(raw_dir, derivatives_dir)
    
    # Also print the docker run command equivalent for manual execution
    run_cmd = get_docker_run_command(raw_dir, derivatives_dir)
    print("\nDocker Run Command Equivalent:")
    print(run_cmd)
    
    print(f"\nConfiguration file generated: {config_file}")
    print("To run with docker-compose: docker-compose -f {config_file} run --rm fmriprep")
    print("To run with docker: " + run_cmd)

if __name__ == "__main__":
    main()