"""
Script to orchestrate the metrics calculation and save to JSON.
This script calls the main function in metrics.py which performs the analysis.
"""
import sys
import os

# Add the parent directory to the path if running as a script
# This ensures imports work correctly regardless of how the script is invoked
if __name__ == "__main__":
    # Ensure we are in the project root or code directory
    # The metrics.py main function handles the logic
    from metrics import main
    
    print("Starting metrics calculation and save process...")
    main()
    print("Metrics calculation and save process completed.")
