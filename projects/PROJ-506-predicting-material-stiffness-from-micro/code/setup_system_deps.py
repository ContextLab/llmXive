"""
System Dependency Checker for PROJ-506.
Verifies the presence of libfftw3 via ldconfig on Linux systems.
"""
import platform
import subprocess
import sys
import logging

# Configure logging to output to stdout for visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_fftw3_availability() -> bool:
    """
    Checks if libfftw3 is available in the system linker cache.
    
    Returns:
        bool: True if fftw3 is found, False otherwise.
    """
    current_platform = platform.system()
    
    if current_platform != "Linux":
        logger.warning(f"Platform is {current_platform}. This check is specific to Linux.")
        return False

    try:
        # Run ldconfig -p to list available shared libraries
        result = subprocess.run(
            ['ldconfig', '-p'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error("Failed to execute 'ldconfig -p'.")
            return False

        # Check for fftw3 in the output
        if b'fftw3' in result.stdout.encode() or 'fftw3' in result.stdout:
            logger.info("SUCCESS: libfftw3 found in system linker cache.")
            return True
        else:
            logger.error("FAILURE: libfftw3 NOT found in system linker cache.")
            logger.error("Please install it using: sudo apt-get install libfftw3-dev (Debian/Ubuntu)")
            return False

    except FileNotFoundError:
        logger.error("FAILURE: 'ldconfig' command not found. This is expected on non-Linux systems.")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False

def main():
    """
    Main entry point for the system dependency check.
    Exits with code 0 on success, 1 on failure.
    """
    logger.info("Starting system dependency verification for PROJ-506...")
    logger.info("Checking for libfftw3 (required for pyfftw)...")

    if check_fftw3_availability():
        logger.info("System dependency check PASSED.")
        sys.exit(0)
    else:
        logger.error("System dependency check FAILED. The pipeline cannot proceed without libfftw3.")
        sys.exit(1)

if __name__ == "__main__":
    main()
