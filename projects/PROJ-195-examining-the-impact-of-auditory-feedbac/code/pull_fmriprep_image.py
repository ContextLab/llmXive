import sys
import subprocess

# Stable version tag for fmriprep as of late 2023/early 2024
# This ensures deterministic behavior across runs
FMRIPREP_VERSION = "23.1.3"
IMAGE_NAME = f"nipreps/fmriprep:{FMRIPREP_VERSION}"

def pull_fmriprep_image():
    """
    Pulls the specific fmriprep Docker image required for the project.
    
    Raises:
        subprocess.CalledProcessError: If docker pull fails.
        FileNotFoundError: If docker is not installed or not in PATH.
    """
    print(f"Ensuring fmriprep image {IMAGE_NAME} is available...")
    try:
        # Check if image exists locally first
        result = subprocess.run(
            ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
            capture_output=True,
            text=True,
            check=True
        )
        if IMAGE_NAME in result.stdout:
            print(f"Image {IMAGE_NAME} already exists locally.")
            return True

        # If not found, pull it
        print(f"Pulling {IMAGE_NAME}...")
        subprocess.run(
            ["docker", "pull", IMAGE_NAME],
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        print(f"Successfully pulled {IMAGE_NAME}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to pull or verify Docker image {IMAGE_NAME}.")
        print(f"Details: {e}")
        raise
    except FileNotFoundError:
        print("ERROR: Docker is not installed or not found in PATH.")
        raise

def main():
    """Entry point for the script."""
    try:
        pull_fmriprep_image()
        print("Docker image verification complete.")
    except Exception as e:
        print(f"Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()