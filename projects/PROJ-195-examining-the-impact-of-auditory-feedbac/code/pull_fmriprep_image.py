"""
Script to pull a specific stable release of the fmriprep Docker image.

This task (T008b) specifies the Docker image tag for determinism.
It pulls 'nipreps/fmriprep:23.1.3', a stable LTS release compatible
with current BIDS standards and nilearn workflows.
"""
import sys
import subprocess

# Specific stable tag for determinism (T008b requirement)
FMRI_PREP_TAG = "23.1.3"
IMAGE_NAME = f"nipreps/fmriprep:{FMRI_PREP_TAG}"

def pull_fmriprep_image(image_name: str) -> bool:
    """
    Pulls the specified fmriprep Docker image.
    
    Args:
        image_name: The full Docker image name with tag.
        
    Returns:
        True if the pull was successful, False otherwise.
    """
    print(f"Pulling {image_name}...")
    try:
        result = subprocess.run(
            ["docker", "pull", image_name],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        print("Pull successful.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to pull Docker image '{image_name}'.")
        print(f"Output: {e.output}")
        return False
    except FileNotFoundError:
        print("ERROR: 'docker' command not found. Please ensure Docker is installed and running.")
        return False

def main():
    """Entry point for the script."""
    success = pull_fmriprep_image(IMAGE_NAME)
    if not success:
        sys.exit(1)
    print(f"Successfully prepared image: {IMAGE_NAME}")

if __name__ == "__main__":
    main()
