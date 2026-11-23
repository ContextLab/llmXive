import sys
import re
import logging

def main():
    """
    Verify that the running Python version is 3.11.x.
    Exits with code 1 if the version is not supported.
    """
    version = sys.version_info
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    if version.major == 3 and version.minor == 11:
        logging.info(f"Python version {version.major}.{version.minor}.{version.micro} is supported.")
        return 0
    else:
        logging.error(f"Python version {version.major}.{version.minor}.{version.micro} is not supported. Requires 3.11.x.")
        return 1

if __name__ == "__main__":
    sys.exit(main())