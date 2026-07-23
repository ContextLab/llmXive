import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

def run_6_hour_stress_test():
    """
    Execute the full pipeline on a standard runner and verify it completes within 6 hours.
    """
    start_time = time.time()
    
    # Import and run the main pipeline
    from main import main as pipeline_main
    
    # Simulate command line arguments for synthetic mode
    sys.argv = ['main.py', '--mode', 'synthetic', '--output', 'data/results/']
    
    try:
        pipeline_main()
    except SystemExit as e:
        if e.code != 0:
            raise
    
    end_time = time.time()
    duration = end_time - start_time
    duration_hours = duration / 3600
    
    # Generate report
    report = {
        "test_name": "6_Hour_Stress_Test",
        "start_time": datetime.fromtimestamp(start_time).isoformat(),
        "end_time": datetime.fromtimestamp(end_time).isoformat(),
        "duration_seconds": duration,
        "duration_hours": duration_hours,
        "status": "PASS" if duration_hours < 6.0 else "FAIL",
        "message": f"Pipeline completed in {duration_hours:.2f} hours."
    }
    
    output_path = Path("data/results/stress_test_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Stress test completed. Duration: {duration_hours:.2f} hours. Status: {report['status']}")
    print(f"Report saved to {output_path}")
    
    return report

def main():
    """Main entry point for stress test."""
    run_6_hour_stress_test()

if __name__ == "__main__":
    main()
