"""
Cyclomatic complexity computation using radon cc.

Implements T029: Compute cyclomatic complexity for submitted code.
Returns an integer >= 1 (minimum complexity for any function/module).
"""
import os
import sys
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Import radon for cyclomatic complexity calculation
try:
    from radon.complexity import cc_visit
    from radon.raw import analyze as analyze_raw
except ImportError:
    # Fallback for environments where radon is not installed yet
    # This should be caught by the requirements.txt dependency
    raise ImportError("radon library is required. Install with: pip install radon")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def compute_cyclomatic_complexity(code: str, language: str = "python") -> int:
    """
    Compute the cyclomatic complexity of the given code block.
    
    Args:
        code: The source code string to analyze.
        language: The programming language (currently only 'python' is supported).
    
    Returns:
        int: The cyclomatic complexity value (minimum 1).
    
    Raises:
        ValueError: If the language is not supported or code is empty.
        SyntaxError: If the code contains syntax errors that prevent analysis.
    """
    if not code or not code.strip():
        raise ValueError("Code cannot be empty")
    
    if language.lower() != "python":
        raise ValueError(f"Cyclomatic complexity calculation is only supported for Python, got: {language}")
    
    try:
        # radon.cc_visit expects valid Python source code
        # It returns a list of complexity results for each function/class/block
        results = cc_visit(code)
        
        if not results:
            # If no functions/classes are found, the module itself has complexity 1
            return 1
        
        # Get the maximum complexity found in the code
        # This represents the most complex path in the submitted code
        max_complexity = max(r.complexity for r in results)
        
        # Ensure minimum value is 1 (standard for cyclomatic complexity)
        return max(1, max_complexity)
        
    except SyntaxError as e:
        logger.error(f"Syntax error in code preventing complexity analysis: {e}")
        # Re-raise as SyntaxError to be handled by the pipeline
        raise
    except Exception as e:
        logger.error(f"Error computing cyclomatic complexity: {e}")
        raise


def get_complexity_breakdown(code: str, language: str = "python") -> List[Dict[str, Any]]:
    """
    Get a detailed breakdown of complexity per function/class.
    
    Args:
        code: The source code string to analyze.
        language: The programming language.
    
    Returns:
        List[Dict]: List of dictionaries containing complexity details for each block.
    """
    if not code or not code.strip():
        return []
    
    if language.lower() != "python":
        raise ValueError(f"Only Python is supported, got: {language}")
    
    try:
        results = cc_visit(code)
        breakdown = []
        
        for r in results:
            breakdown.append({
                "name": r.name,
                "complexity": r.complexity,
                "lineno": r.lineno,
                "end_lineno": r.end_lineno,
                "is_class": r.is_class,
                "is_function": r.is_function,
            })
        
        return breakdown
    except Exception as e:
        logger.error(f"Error getting complexity breakdown: {e}")
        return []


def analyze_code_quality(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Perform a comprehensive code quality analysis including complexity.
    
    Args:
        code: The source code string.
        language: The programming language.
    
    Returns:
        Dict: Analysis results including complexity, lines of code, etc.
    """
    if not code or not code.strip():
        return {
            "cyclomatic_complexity": 1,
            "lines_of_code": 0,
            "comment_lines": 0,
            "blank_lines": 0,
            "sloc": 0,
            "breakdown": []
        }
    
    try:
        # Get complexity
        complexity = compute_cyclomatic_complexity(code, language)
        
        # Get raw metrics (LOC, comments, etc.)
        raw_analysis = analyze_raw(code)
        
        # Get detailed breakdown
        breakdown = get_complexity_breakdown(code, language)
        
        return {
            "cyclomatic_complexity": complexity,
            "lines_of_code": raw_analysis.ncloc,
            "comment_lines": raw_analysis.comment_lines,
            "blank_lines": raw_analysis.blank_lines,
            "sloc": raw_analysis.sloc,
            "breakdown": breakdown,
            "language": language
        }
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        return {
            "cyclomatic_complexity": 1,
            "lines_of_code": 0,
            "comment_lines": 0,
            "blank_lines": 0,
            "sloc": 0,
            "breakdown": [],
            "language": language,
            "error": str(e)
        }


def main():
    """
    Main entry point for testing the complexity calculation.
    Reads code from stdin or a file, computes complexity, and prints results.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute cyclomatic complexity of Python code")
    parser.add_argument("--file", type=str, help="Path to the Python file to analyze")
    parser.add_argument("--code", type=str, help="Direct code string to analyze")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed breakdown")
    
    args = parser.parse_args()
    
    code = None
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                code = f.read()
        except FileNotFoundError:
            logger.error(f"File not found: {args.file}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            sys.exit(1)
    elif args.code:
        code = args.code
    else:
        # Read from stdin
        logger.info("Reading code from stdin...")
        code = sys.stdin.read()
    
    if not code:
        logger.error("No code provided")
        sys.exit(1)
    
    try:
        result = analyze_code_quality(code, "python")
        
        print(json.dumps({
            "cyclomatic_complexity": result["cyclomatic_complexity"],
            "lines_of_code": result["lines_of_code"],
            "sloc": result["sloc"],
            "comment_lines": result["comment_lines"],
            "blank_lines": result["blank_lines"]
        }, indent=2))
        
        if args.verbose:
            print("\nDetailed Breakdown:")
            for item in result["breakdown"]:
                print(f"  - {item['name']} (line {item['lineno']}): CC={item['complexity']}")
                
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()