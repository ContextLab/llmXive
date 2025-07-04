#!/usr/bin/env python3
"""Debug score parsing"""

import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.response_parser import ResponseParser


def test_score_parsing():
    """Debug score parsing"""
    
    parser = ResponseParser()
    
    test_texts = [
        "Score: 8.5",
        "Score: 8.5\n\nOther text",
        "score: 8.5",
        "SCORE: 8.5",
        "Score:8.5",
        "Score : 8.5",
    ]
    
    print("Testing score parsing...")
    for text in test_texts:
        score = parser.parse_review_score(text)
        print(f"Text: '{text}' -> Score: {score}")
        
    # Test the actual pattern
    print("\n\nTesting actual patterns:")
    text = "Score: 8.5"
    
    # Pattern from parse_review_score
    pattern = r'Score:\s*([0-9.]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        print(f"Pattern '{pattern}' matched: {match.group(1)}")
        try:
            score_val = float(match.group(1))
            print(f"Parsed value: {score_val}")
            print(f"In range [0, 1.0]: {0 <= score_val <= 1.0}")
        except:
            print("Failed to convert to float")
    else:
        print(f"Pattern '{pattern}' did NOT match")


if __name__ == "__main__":
    test_score_parsing()