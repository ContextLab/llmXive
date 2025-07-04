#!/usr/bin/env python3
"""Debug the review parser specifically"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.response_parser import ResponseParser


def test_review_parsing():
    """Test review parsing with actual response"""
    
    parser = ResponseParser()
    
    test_response = """Score: 8.5

Strengths:
- Clear methodology
- Novel approach
- Good feasibility

Concerns:
- Needs more evaluation metrics
- Timeline seems aggressive

Recommendation: Accept
Summary: Strong proposal with minor revisions needed."""

    print("Testing review response parsing...")
    print("="*60)
    print("Input:")
    print(test_response)
    print("="*60)
    
    result = parser.parse_review_response(test_response)
    print("\nParsed result:")
    print(result)
    
    # Test individual components
    print("\n\nTesting individual components:")
    
    # Test score parsing
    score = parser.parse_review_score(test_response)
    print(f"Score: {score}")
    
    # Test strengths regex
    import re
    strengths_match = re.search(r'Strengths?:?\s*\n((?:[-*•]\s*.+\n?)+)', test_response, re.MULTILINE | re.IGNORECASE)
    if strengths_match:
        print(f"\nStrengths matched: '{strengths_match.group(1)}'")
    else:
        print("\nStrengths NOT matched")
        
    # Test with different patterns
    print("\n\nTrying different patterns:")
    
    # Pattern 1: Look for lines starting with -
    pattern1 = r'Strengths?:.*?\n((?:.*\n)*?)(?:\n(?:[A-Z]|$))'
    match1 = re.search(pattern1, test_response, re.DOTALL | re.IGNORECASE)
    if match1:
        print(f"Pattern 1 matched: '{match1.group(1).strip()}'")
        
    # Pattern 2: Everything between Strengths and Concerns
    pattern2 = r'Strengths?:.*?\n(.*?)(?=\n\w+:|$)'
    match2 = re.search(pattern2, test_response, re.DOTALL | re.IGNORECASE)
    if match2:
        print(f"Pattern 2 matched: '{match2.group(1).strip()}'")


if __name__ == "__main__":
    test_review_parsing()