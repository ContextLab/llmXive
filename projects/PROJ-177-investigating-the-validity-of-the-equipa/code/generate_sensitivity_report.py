import json
import sys
from pathlib import Path
from sensitivity import run_sensitivity_analysis, SensitivityError

def main():
    """Generate sensitivity report."""
    try:
        from sensitivity import load_statistical_results
        results = load_statistical_results()
        
        thresholds = [0.01, 0.05, 0.10]
        boundaries = [0.01, 0.05, 0.10]
        
        analysis = run_sensitivity_analysis(results, thresholds, boundaries)
        
        output_path = Path('artifacts/sensitivity_analysis_report.json')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"Sensitivity report written to {output_path}")
        return 0
    
    except Exception as e:
        print(f"Sensitivity report generation failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
