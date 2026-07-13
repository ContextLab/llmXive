"""
Problem validation module for FR-014.

Validates problems based on:
1. Average solution time >= 5 minutes (300 seconds)
2. Medium difficulty classification
"""
import os
import sys
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_datasets_config
from experiment.problem_loader import load_humaneval_problems, load_codeforces_problems, load_all_problems

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MIN_AVG_SOLUTION_TIME_SECONDS = 300  # 5 minutes
MEDIUM_DIFFICULTY_THRESHOLD = 0.3  # Pass rate threshold for "medium" difficulty (30-70%)
MAX_DIFFICULTY_THRESHOLD = 0.7  # Upper bound for medium difficulty

def load_problem_metadata(source: str = "humaneval") -> List[Dict[str, Any]]:
    """
    Load problem metadata including solution times and difficulty metrics.
    
    Args:
        source: Data source ('humaneval' or 'codeforces')
        
    Returns:
        List of problem dictionaries with metadata
    """
    if source == "humaneval":
        problems = load_humaneval_problems()
    elif source == "codeforces":
        problems = load_codeforces_problems()
    else:
        raise ValueError(f"Unknown problem source: {source}")
    
    return problems

def estimate_solution_time(problem: Dict[str, Any]) -> float:
    """
    Estimate solution time for a problem based on its characteristics.
    
    For HumanEval: Uses pass rate as a proxy for difficulty/time.
    For Codeforces: Uses rating/difficulty score.
    
    Args:
        problem: Problem dictionary with metadata
        
    Returns:
        Estimated solution time in seconds
    """
    source = problem.get("source", "humaneval")
    
    if source == "humaneval":
        # HumanEval pass rate as proxy: lower pass rate = harder = more time
        # Typical HumanEval problems: 1-10 minutes based on pass rate
        pass_rate = problem.get("pass_rate", 0.5)
        
        # Inverse relationship: lower pass rate -> higher time
        # Base time 2 minutes, scaled by difficulty
        if pass_rate > 0.8:
            # Easy: 2-3 minutes
            estimated_time = 120 + (0.8 - pass_rate) * 300
        elif pass_rate > 0.5:
            # Medium: 3-6 minutes
            estimated_time = 180 + (0.5 - pass_rate) * 600
        else:
            # Hard: 6-15 minutes
            estimated_time = 360 + (0.5 - pass_rate) * 900
        
        return max(60, min(900, estimated_time))  # Clamp between 1 and 15 minutes
    
    elif source == "codeforces":
        # Codeforces uses rating (800-3000)
        rating = problem.get("rating", 1500)
        
        # Map rating to time: 800 -> 2min, 2000 -> 15min, 3000 -> 30min
        if rating < 1000:
            return 120
        elif rating < 1500:
            return 180 + (rating - 1000) * 0.12
        elif rating < 2000:
            return 360 + (rating - 1500) * 0.36
        else:
            return 360 + (rating - 2000) * 0.36
    
    return 300  # Default 5 minutes

def classify_difficulty(problem: Dict[str, Any]) -> str:
    """
    Classify problem difficulty based on pass rate or rating.
    
    Args:
        problem: Problem dictionary with metadata
        
    Returns:
        Difficulty classification: 'easy', 'medium', or 'hard'
    """
    source = problem.get("source", "humaneval")
    
    if source == "humaneval":
        pass_rate = problem.get("pass_rate", 0.5)
        
        if pass_rate > 0.7:
            return "easy"
        elif pass_rate >= 0.3:
            return "medium"
        else:
            return "hard"
    
    elif source == "codeforces":
        rating = problem.get("rating", 1500)
        
        if rating < 1200:
            return "easy"
        elif rating < 2000:
            return "medium"
        else:
            return "hard"
    
    return "medium"  # Default

def validate_problem(problem: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single problem against FR-014 criteria.
    
    Criteria:
    1. Average solution time >= 5 minutes (300 seconds)
    2. Medium difficulty classification
    
    Args:
        problem: Problem dictionary to validate
        
    Returns:
        Tuple of (is_valid, list_of_violations)
    """
    violations = []
    
    # Check solution time
    estimated_time = estimate_solution_time(problem)
    if estimated_time < MIN_AVG_SOLUTION_TIME_SECONDS:
        violations.append(
            f"Solution time ({estimated_time:.1f}s) < minimum ({MIN_AVG_SOLUTION_TIME_SECONDS}s)"
        )
    
    # Check difficulty
    difficulty = classify_difficulty(problem)
    if difficulty != "medium":
        violations.append(f"Difficulty ({difficulty}) != medium")
    
    is_valid = len(violations) == 0
    return is_valid, violations

def validate_problem_set(problems: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate a set of problems and generate a report.
    
    Args:
        problems: List of problem dictionaries
        
    Returns:
        Validation report with statistics and details
    """
    if not problems:
        return {
            "valid": False,
            "total": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "avg_solution_time": 0,
            "issues": ["No problems to validate"]
        }
    
    valid_problems = []
    invalid_problems = []
    total_time = 0
    issues = []
    
    for i, problem in enumerate(problems):
        problem_id = problem.get("task_id", problem.get("id", f"problem_{i}"))
        is_valid, violations = validate_problem(problem)
        
        estimated_time = estimate_solution_time(problem)
        total_time += estimated_time
        
        if is_valid:
            valid_problems.append({
                "id": problem_id,
                "source": problem.get("source"),
                "estimated_time": estimated_time,
                "difficulty": classify_difficulty(problem)
            })
        else:
            invalid_problems.append({
                "id": problem_id,
                "source": problem.get("source"),
                "estimated_time": estimated_time,
                "difficulty": classify_difficulty(problem),
                "violations": violations
            })
            for v in violations:
                issues.append(f"{problem_id}: {v}")
    
    avg_time = total_time / len(problems)
    
    report = {
        "valid": len(invalid_problems) == 0,
        "total": len(problems),
        "valid_count": len(valid_problems),
        "invalid_count": len(invalid_problems),
        "avg_solution_time": avg_time,
        "min_solution_time": min(estimate_solution_time(p) for p in problems),
        "max_solution_time": max(estimate_solution_time(p) for p in problems),
        "issues": issues,
        "valid_problems": valid_problems,
        "invalid_problems": invalid_problems
    }
    
    return report

def filter_medium_difficulty_problems(
    problems: List[Dict[str, Any]], 
    min_time: float = MIN_AVG_SOLUTION_TIME_SECONDS
) -> List[Dict[str, Any]]:
    """
    Filter problems to only include medium difficulty with sufficient solution time.
    
    Args:
        problems: List of all problems
        min_time: Minimum average solution time in seconds
        
    Returns:
        List of filtered problems meeting criteria
    """
    filtered = []
    
    for problem in problems:
        estimated_time = estimate_solution_time(problem)
        difficulty = classify_difficulty(problem)
        
        if difficulty == "medium" and estimated_time >= min_time:
            filtered.append(problem)
    
    return filtered

def verify_fr014_compliance(source: str = "all") -> Dict[str, Any]:
    """
    Verify FR-014 compliance for the specified problem source(s).
    
    Args:
        source: 'humaneval', 'codeforces', or 'all'
        
    Returns:
        Compliance report
    """
    if source == "all":
        problems = load_all_problems()
        sources = ["humaneval", "codeforces"]
    else:
        problems = load_problem_metadata(source)
        sources = [source]
    
    report = {
        "sources": sources,
        "compliance": {},
        "overall_valid": True
    }
    
    for src in sources:
        src_problems = [p for p in problems if p.get("source") == src]
        src_report = validate_problem_set(src_problems)
        report["compliance"][src] = src_report
        
        if not src_report["valid"]:
            report["overall_valid"] = False
    
    # Overall statistics
    if problems:
        all_times = [estimate_solution_time(p) for p in problems]
        report["overall_avg_time"] = sum(all_times) / len(all_times)
        report["total_problems"] = len(problems)
        report["valid_problems"] = sum(1 for p in problems if validate_problem(p)[0])
    
    return report

def main():
    """Main entry point for problem validation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting FR-014 problem validation")
    
    # Validate all problems
    report = verify_fr014_compliance("all")
    
    # Print summary
    print("\n" + "="*60)
    print("FR-014 Problem Validation Report")
    print("="*60)
    
    for source, data in report["compliance"].items():
        print(f"\nSource: {source}")
        print(f"  Total problems: {data['total']}")
        print(f"  Valid: {data['valid_count']}")
        print(f"  Invalid: {data['invalid_count']}")
        print(f"  Avg solution time: {data['avg_solution_time']:.1f}s")
        
        if data['issues']:
            print(f"  Issues ({len(data['issues'])}):")
            for issue in data['issues'][:5]:  # Show first 5
                print(f"    - {issue}")
            if len(data['issues']) > 5:
                print(f"    ... and {len(data['issues']) - 5} more")
    
    print(f"\nOverall Compliance: {'PASS' if report['overall_valid'] else 'FAIL'}")
    
    if not report["overall_valid"]:
        logger.warning("FR-014 compliance check failed")
        sys.exit(1)
    else:
        logger.info("FR-014 compliance check passed")
        sys.exit(0)

if __name__ == "__main__":
    main()