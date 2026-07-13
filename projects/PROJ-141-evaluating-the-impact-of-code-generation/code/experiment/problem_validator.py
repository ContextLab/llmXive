import os
import sys
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple

from experiment.problem_loader import load_all_problems, load_humaneval_problems, load_codeforces_problems
from config.settings import get_datasets_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FR-014 Constants
MIN_AVG_SOLUTION_TIME_SECONDS = 300  # 5 minutes
TARGET_DIFFICULTY = "medium"
MIN_MEDIUM_PROBLEM_PERCENTAGE = 0.60  # At least 60% should be medium difficulty

def load_problem_metadata(problem: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load or extract metadata for a problem.
    If metadata is not present in the problem dict, attempt to derive it.
    """
    if 'metadata' in problem:
        return problem['metadata']
    
    # Derive from problem structure if missing
    return {
        'problem_id': problem.get('problem_id', 'unknown'),
        'source': problem.get('source', 'unknown'),
        'difficulty': problem.get('difficulty', 'unknown'),
        'estimated_time_minutes': problem.get('estimated_time_minutes', 10)
    }

def estimate_solution_time(problem: Dict[str, Any]) -> float:
    """
    Estimate solution time for a problem in seconds.
    Uses a heuristic based on problem description length and complexity markers.
    Falls back to metadata if available.
    """
    metadata = load_problem_metadata(problem)
    
    # If we have a direct estimate, use it
    if 'estimated_time_minutes' in metadata:
        return float(metadata['estimated_time_minutes']) * 60.0

    # Heuristic estimation based on problem characteristics
    description = problem.get('description', '')
    prompt = problem.get('prompt', '')
    test_cases = problem.get('test_cases', [])
    
    text_length = len(description) + len(prompt)
    
    # Base time: 2 minutes
    base_time = 120.0
    
    # Add time for text length (1 second per 100 chars)
    length_time = text_length / 100.0
    
    # Add time for complexity (10 seconds per test case)
    complexity_time = len(test_cases) * 10.0
    
    # Add time for description complexity (keywords)
    complexity_keywords = ['complex', 'advanced', 'optimize', 'dynamic', 'graph', 'tree']
    keyword_penalty = sum(1 for kw in complexity_keywords if kw in description.lower()) * 30.0
    
    total_seconds = base_time + length_time + complexity_time + keyword_penalty
    
    # Clamp to reasonable bounds (2 min to 60 min)
    return max(120.0, min(3600.0, total_seconds))

def classify_difficulty(problem: Dict[str, Any]) -> str:
    """
    Classify problem difficulty as 'easy', 'medium', or 'hard'.
    Uses a heuristic based on estimated time and problem characteristics.
    """
    metadata = load_problem_metadata(problem)
    
    # If difficulty is explicitly stated, trust it
    if 'difficulty' in metadata and metadata['difficulty'] in ['easy', 'medium', 'hard']:
        return metadata['difficulty']
    
    # Heuristic classification based on estimated time
    estimated_seconds = estimate_solution_time(problem)
    estimated_minutes = estimated_seconds / 60.0
    
    if estimated_minutes < 5.0:
        return 'easy'
    elif estimated_minutes < 15.0:
        return 'medium'
    else:
        return 'hard'

def validate_problem(problem: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single problem against FR-014 criteria.
    Returns (is_valid, list_of_issues).
    """
    issues = []
    
    # Check required fields
    if 'problem_id' not in problem:
        issues.append("Missing 'problem_id'")
    if 'description' not in problem and 'prompt' not in problem:
        issues.append("Missing 'description' or 'prompt'")
    
    # Estimate solution time
    est_time = estimate_solution_time(problem)
    if est_time < 120.0:  # Less than 2 minutes is suspicious
        issues.append(f"Estimated time {est_time:.1f}s is very short (< 2 min)")
    
    # Classify difficulty
    difficulty = classify_difficulty(problem)
    if difficulty == 'unknown':
        issues.append("Could not classify difficulty")
    
    is_valid = len(issues) == 0
    return is_valid, issues

def validate_problem_set(problems: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate a set of problems for FR-014 compliance.
    Returns validation report.
    """
    if not problems:
        return {
            'valid': False,
            'error': 'No problems to validate',
            'avg_solution_time': 0,
            'medium_difficulty_ratio': 0,
            'issues': ['Empty problem set']
        }
    
    total_estimated_time = 0.0
    medium_count = 0
    valid_count = 0
    all_issues = []
    
    for i, problem in enumerate(problems):
        is_valid, issues = validate_problem(problem)
        if is_valid:
            valid_count += 1
        
        all_issues.extend([f"Problem {i}: {issue}" for issue in issues])
        
        total_estimated_time += estimate_solution_time(problem)
        difficulty = classify_difficulty(problem)
        if difficulty == 'medium':
            medium_count += 1
    
    avg_time_seconds = total_estimated_time / len(problems)
    medium_ratio = medium_count / len(problems)
    
    fr014_compliant = (
        avg_time_seconds >= MIN_AVG_SOLUTION_TIME_SECONDS and
        medium_ratio >= MIN_MEDIUM_PROBLEM_PERCENTAGE
    )
    
    return {
        'valid': fr014_compliant,
        'total_problems': len(problems),
        'valid_problems': valid_count,
        'avg_solution_time_seconds': avg_time_seconds,
        'avg_solution_time_minutes': avg_time_seconds / 60.0,
        'medium_difficulty_count': medium_count,
        'medium_difficulty_ratio': medium_ratio,
        'issues': all_issues[:10]  # Limit to first 10 issues for readability
    }

def filter_medium_difficulty_problems(problems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter problems to keep only those classified as 'medium' difficulty.
    """
    return [p for p in problems if classify_difficulty(p) == 'medium']

def verify_fr014_compliance(problems: List[Dict[str, Any]]) -> bool:
    """
    Verify that a problem set meets FR-014 requirements:
    - Average solution time >= 5 minutes
    - Majority of problems are 'medium' difficulty
    
    Returns True if compliant, False otherwise.
    """
    report = validate_problem_set(problems)
    
    if not report['valid']:
        logger.warning(f"FR-014 Compliance failed: {report.get('issues', [])}")
        logger.info(f"Avg time: {report['avg_solution_time_minutes']:.1f} min, "
                   f"Medium ratio: {report['medium_difficulty_ratio']:.2f}")
        return False
    
    logger.info(f"FR-014 Compliance passed: Avg time {report['avg_solution_time_minutes']:.1f} min, "
               f"Medium ratio {report['medium_difficulty_ratio']:.2f}")
    return True

def main():
    """
    Main entry point for problem validation.
    Loads problems from HumanEval and Codeforces, validates them,
    and reports compliance with FR-014.
    """
    logger.info("Starting problem validation for FR-014 compliance...")
    
    try:
        # Load all problems
        problems = load_all_problems()
        
        if not problems:
            logger.error("No problems loaded. Cannot validate.")
            sys.exit(1)
        
        logger.info(f"Loaded {len(problems)} problems.")
        
        # Validate problem set
        report = validate_problem_set(problems)
        
        # Print report
        print("\n=== FR-014 Validation Report ===")
        print(f"Total Problems: {report['total_problems']}")
        print(f"Valid Problems: {report['valid_problems']}")
        print(f"Avg Solution Time: {report['avg_solution_time_minutes']:.2f} minutes "
              f"({'PASS' if report['avg_solution_time_seconds'] >= MIN_AVG_SOLUTION_TIME_SECONDS else 'FAIL'})")
        print(f"Medium Difficulty Ratio: {report['medium_difficulty_ratio']:.2%} "
              f"({'PASS' if report['medium_difficulty_ratio'] >= MIN_MEDIUM_PROBLEM_PERCENTAGE else 'FAIL'})")
        print(f"FR-014 Compliant: {'YES' if report['valid'] else 'NO'}")
        
        if report['issues']:
            print("\nIssues found:")
            for issue in report['issues']:
                print(f"  - {issue}")
        
        # Exit with appropriate code
        sys.exit(0 if report['valid'] else 1)
        
    except Exception as e:
        logger.exception(f"Validation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()