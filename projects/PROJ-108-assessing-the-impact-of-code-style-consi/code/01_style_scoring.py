"""
Style Consistency Scoring Module.

This module calculates normalized style-consistency scores for Python files
using pylint (for indentation and naming conventions) and radon (for line length).
It outputs a composite score and individual metric scores normalized to [0.0, 1.0].
"""

import subprocess
import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from radon.complexity import cc_visit
from radon.visitors import ComplexityVisitor
from radon.raw import analyze as radon_raw_analyze


def get_file_size(file_path: str) -> int:
    """Get the size of a file in bytes."""
    return os.path.getsize(file_path)


def get_cyclomatic_complexity(file_path: str) -> int:
    """Calculate the cyclomatic complexity of a file using radon."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        visitor = ComplexityVisitor.from_code(source)
        # Return the total complexity sum of all functions/classes
        return sum(block.complexity for block in visitor.blocks)
    except Exception:
        return 0


def get_pylint_score(file_path: str) -> Optional[float]:
    """
    Run pylint on a file and extract a normalized score.
    
    Pylint returns a score out of 10.0. We normalize this to 0.0-1.0.
    We specifically look for issues related to indentation and naming.
    """
    try:
        # Run pylint with JSON output
        result = subprocess.run(
            [sys.executable, '-m', 'pylint', '--output-format=json', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode not in [0, 16]: # 0=OK, 16=Usage error, 20+=Fatal
            # If pylint crashes, return None to indicate failure
            return None

        messages = json.loads(result.stdout)
        
        # Filter for indentation and naming issues
        # Indentation: E1101 (no-member), E1120 (no-value-for-param) are not style
        # Style codes: C0301 (line-too-long), C0303 (trailing-whitespace), C0304 (missing-final-newline),
        #            C0321 (multiple-statements), C0325 (superfluous-parens)
        #            W0311 (bad-indentation), E111 (bad-continuation)
        # Naming: C0103 (invalid-name), C0114 (missing-module-docstring), etc.
        
        style_issues = 0
        total_issues = len(messages)
        
        # Define style-related codes (simplified for this task)
        style_codes = {
            'W0311', # bad-indentation
            'E111',  # bad-continuation (deprecated in newer pylint but common)
            'C0301', # line-too-long
            'C0303', # trailing-whitespace
            'C0304', # missing-final-newline
            'C0325', # superfluous-parens
            'C0326', # bad-whitespace
            'C0103', # invalid-name (naming)
            'C0114', # missing-module-docstring
            'C0115', # missing-class-docstring
            'C0116', # missing-function-docstring
        }
        
        for msg in messages:
            if msg.get('symbol') in style_codes or msg.get('message-id', '').startswith('C') or msg.get('message-id', '').startswith('W'):
                # We count all W and C codes as style issues for this simplified metric
                if msg.get('type') in ['convention', 'refactor', 'warning']:
                    style_issues += 1
        
        # If no issues found, score is 1.0
        if total_issues == 0:
            return 1.0
        
        # Normalize: 1.0 - (issues / total_possible_issues). 
        # Since we don't know total possible, we use a heuristic based on lines of code
        # or simply cap the penalty. Let's use a simple ratio:
        # Score = 1.0 - (style_issues / max(1, total_lines))
        # But to keep it strictly within [0,1] and robust, let's use a simpler approach:
        # If pylint runs successfully, it gives a global score.
        # Let's try to parse the global score from the "report" section if available, 
        # or calculate based on the ratio of style issues to total lines.
        
        # Fallback: Use the global score from pylint if we can parse it, else estimate.
        # The JSON output doesn't always have the global score directly in the list of messages.
        # We will calculate a heuristic score based on the number of style violations.
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        total_lines = len(lines)
        
        # Heuristic: 10% of lines having a style issue is a 0.5 score
        # Max penalty is 0.0 if style_issues > total_lines * 2 (impossible but safe)
        penalty = min(1.0, style_issues / max(1, total_lines * 0.1))
        return max(0.0, 1.0 - penalty)
        
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None


def get_radon_line_length_score(file_path: str) -> float:
    """
    Calculate a normalized score for line length consistency using radon.
    
    Returns 1.0 if no lines exceed 100 chars, decreasing as violations increase.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            return 1.0
        
        long_lines = 0
        max_len = 100 # Standard limit
        
        for line in lines:
            # Strip newline for length check
            if len(line.rstrip('\n\r')) > max_len:
                long_lines += 1
        
        if long_lines == 0:
            return 1.0
        
        # Score decreases based on the proportion of long lines
        # If 10% of lines are too long, score is 0.9
        penalty = min(1.0, long_lines / len(lines))
        return max(0.0, 1.0 - penalty)
        
    except Exception:
        return 0.0


def compute_style_score(file_path: str) -> Dict[str, Any]:
    """
    Compute style consistency scores for a given Python file.
    
    Args:
        file_path: Path to the Python file.
        
    Returns:
        A dictionary containing:
        - pylint_indent: Normalized score for indentation and naming (0.0-1.0)
        - radon_line_len: Normalized score for line length (0.0-1.0)
        - composite_score: Average of the two scores (0.0-1.0)
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    if not file_path.endswith('.py'):
        raise ValueError(f"File must be a Python file: {file_path}")
    
    # Calculate individual metrics
    pylint_score = get_pylint_score(file_path)
    radon_score = get_radon_line_length_score(file_path)
    
    # Handle cases where pylint fails (e.g., syntax error)
    if pylint_score is None:
        # If pylint fails, we assume a very low score or 0.0 for style consistency
        # This indicates the file is not well-formed or cannot be analyzed
        pylint_score = 0.0
    
    # Ensure scores are within [0.0, 1.0] (they should be by design, but safe-guard)
    pylint_score = max(0.0, min(1.0, pylint_score))
    radon_score = max(0.0, min(1.0, radon_score))
    
    # Compute composite score (simple average)
    composite = (pylint_score + radon_score) / 2.0
    
    return {
        "pylint_indent": pylint_score,
        "radon_line_len": radon_score,
        "composite_score": composite
    }


def main():
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute style scores for Python files.")
    parser.add_argument("file_path", help="Path to the Python file to analyze")
    parser.add_argument("--output", "-o", help="Output file path (JSON)", default=None)
    
    args = parser.parse_args()
    
    try:
        result = compute_style_score(args.file_path)
        output_str = json.dumps(result, indent=2)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output_str)
            print(f"Results written to {args.output}")
        else:
            print(output_str)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
