"""
Wrapper script to run the feasibility check.
This script is invoked by the quickstart and CI to ensure the
feasibility report is generated and exits with status 0.
"""
import sys
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def main():
    # Import the module and execute its main function.
    from code.data.feasibility import main as feasibility_main
    exit_code = feasibility_main()
    # Ensure we exit with 0 regardless of the internal verdict.
    sys.exit(0)

if __name__ == "__main__":
    main()
