#!/usr/bin/env python
"""Run the full llmXive pipeline test."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

if __name__ == "__main__":
    # Check if a scenario path was provided as command line argument
    if len(sys.argv) > 1:
        scenario_path = Path(sys.argv[1])
    else:
        # Default to the standard test scenario
        scenario_path = Path(__file__).parent / "tests" / "scenarios" / "full_pipeline_test.yaml"
    
    if not scenario_path.exists():
        print(f"❌ Scenario file not found: {scenario_path}")
        sys.exit(1)
    
    # Import and run the main function
    from testing.pipeline_test_runner import main
    
    # Set up arguments
    sys.argv = [
        "run_full_pipeline_test.py",
        str(scenario_path),
        "--work-dir", "test_output/full_pipeline_test",
        "--save-artifacts",
        "--output", "test_output/full_pipeline_test/results.json",
        "-v"  # Verbose
    ]
    
    print("🚀 Running full llmXive pipeline test...")
    print(f"Scenario: {scenario_path}")
    print("-" * 80)
    
    # Run the test
    main()