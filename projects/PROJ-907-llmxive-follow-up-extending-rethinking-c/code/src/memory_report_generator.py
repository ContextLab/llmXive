import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

def load_memory_profile(profile_path: str) -> Dict[str, Any]:
    """Loads the memory profile from a JSON file."""
    with open(profile_path, 'r') as f:
        return json.load(f)

def generate_markdown_report(profile: Dict[str, Any]) -> str:
    """Generates a markdown report from the memory profile."""
    report = f"""
    # Memory Usage Report

    - **Peak Memory**: {profile.get('peak_memory_gb', 0.0):.2f} GB
    - **Within Limit**: {profile.get('within_limit', False)}
    - **Status**: {profile.get('status', 'UNKNOWN')}
    """
    return report

def main():
    """Entry point for the memory report generator."""
    profile_path = os.getenv('MEMORY_PROFILE_PATH', 'data/results/memory_profile.json')
    output_path = os.getenv('MEMORY_REPORT_PATH', 'docs/memory_report.md')
    
    if not Path(profile_path).exists():
        raise FileNotFoundError(f"Memory profile not found at {profile_path}")
    
    profile = load_memory_profile(profile_path)
    report = generate_markdown_report(profile)
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report)
    print(f"Memory report saved to {output_path}")

if __name__ == "__main__":
    main()
