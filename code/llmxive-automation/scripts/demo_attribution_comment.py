#!/usr/bin/env python3
"""Demo script showing how attribution comments work"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model_attribution import ModelAttributionTracker


def main():
    """Show example attribution comment"""
    tracker = ModelAttributionTracker("model_attributions.json")
    
    # Get the TinyLlama stats
    model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    # Generate example comment
    comment = tracker.format_attribution_comment(
        model_id=model_id,
        task_type="BRAINSTORM_IDEA",
        additional_info={
            "Temperature": 0.7,
            "Max Tokens": 512,
            "Task Duration": "2.3 seconds",
            "Model Size": "1.1B parameters"
        }
    )
    
    print("Example Attribution Comment for GitHub Issue:")
    print("=" * 60)
    print(comment)
    print("=" * 60)
    
    print("\nThis comment would be automatically added to the GitHub issue")
    print("when a model makes a contribution.")


if __name__ == "__main__":
    main()