import sys
import subprocess
from pathlib import Path
import argparse
import logging

def get_installed_packages():
    """
    Get the list of installed packages and their versions using pip.
    Returns a list of strings in 'package==version' format.
    """
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'list', '--format=freeze'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to run pip list: {e}")
        return []

def filter_packages(packages):
    """
    Filter the list of packages to include only those relevant to the project.
    Currently, we include all packages but could add specific filtering logic here.
    """
    # Basic filter: exclude local paths or editable installs if necessary
    return [pkg for pkg in packages if pkg and not pkg.startswith('-e')]

def generate_requirements(output_path, packages):
    """
    Write the filtered packages to the requirements.txt file.
    """
    try:
        with open(output_path, 'w') as f:
            f.write('\n'.join(packages))
            f.write('\n')
        logging.info(f"Successfully wrote {len(packages)} packages to {output_path}")
    except IOError as e:
        logging.error(f"Failed to write requirements file: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Generate requirements.txt from installed packages.")
    parser.add_argument(
        '--output',
        type=str,
        default='requirements.txt',
        help='Path to the output requirements file (default: requirements.txt)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

    # Check if requirements.txt exists; if not, we will create it, but if the task
    # implies a check for existence before proceeding in a larger context, we log it.
    # However, the task specifically asks for error handling *if* it is missing in a context
    # where it is expected to exist (e.g., for report generation).
    # Since this script *creates* the file, we proceed.
    # If this script is called by a process that *expects* the file to already exist
    # (which contradicts the purpose of this script), the caller should handle that.
    # Here, we implement the generation logic.

    logging.info("Gathering installed packages...")
    packages = get_installed_packages()

    if not packages:
        logging.warning("No packages found. The requirements file may be empty.")

    filtered = filter_packages(packages)

    output_path = Path(args.output)
    # Ensure the directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generate_requirements(output_path, filtered)

if __name__ == '__main__':
    main()