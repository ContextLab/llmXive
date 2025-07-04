#!/usr/bin/env python3
"""Generate model attribution report"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model_attribution import ModelAttributionTracker


def main():
    """Generate and display attribution report"""
    print("Loading model attribution data...")
    tracker = ModelAttributionTracker("model_attributions.json")
    
    # Generate report
    report = tracker.generate_attribution_report()
    print("\n" + report)
    
    # Show recent contributions
    print("\n## Recent Contributions (Last 10)\n")
    recent = tracker.get_recent_contributions(limit=10)
    
    for contrib in recent:
        model_name = contrib["model_id"].split("/")[-1]
        timestamp = contrib["timestamp"][:19]  # Trim microseconds
        print(f"- {timestamp} | {model_name} | {contrib['task_type']} | {contrib['reference']}")
        
    # Show detailed stats
    print("\n## Detailed Model Statistics\n")
    for model_id, stats in tracker.get_all_model_stats().items():
        model_name = model_id.split("/")[-1]
        print(f"### {model_name}")
        print(f"- Total Contributions: {stats['total_contributions']}")
        print(f"- First Contribution: {stats['first_contribution'][:10]}")
        print(f"- Last Contribution: {stats.get('last_contribution', 'N/A')[:10]}")
        print(f"- Contribution Types:")
        for ctype, count in stats.get("contributions_by_type", {}).items():
            print(f"  - {ctype}: {count}")
        print()


if __name__ == "__main__":
    main()