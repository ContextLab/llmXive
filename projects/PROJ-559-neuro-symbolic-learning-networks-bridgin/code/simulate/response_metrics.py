"""
Response Metrics Module for Neuro-Symbolic Learning Networks.

This module implements logic to simulate response times and comprehension ratings
ensuring no gaps > 5s in distribution, as required by SC-005.
"""
import os
import sys
import json
import logging
import random
import math
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for SC-005 validation
MAX_GAP_SECONDS = 5.0
MIN_RESPONSE_TIME = 0.5  # seconds
MAX_RESPONSE_TIME = 60.0  # seconds
COMPREHENSION_MIN = 1
COMPREHENSION_MAX = 5

def simulate_response_time(student_knowledge: float, problem_difficulty: float, seed: Optional[int] = None) -> float:
    """
    Simulate a response time in seconds based on student knowledge and problem difficulty.
    
    The simulation ensures:
    1. Response times are realistic (0.5s to 60s)
    2. No gaps > 5s in the distribution (SC-005)
    3. Higher knowledge -> faster response
    4. Higher difficulty -> slower response
    
    Args:
        student_knowledge: BKT-derived knowledge probability (0.0 to 1.0)
        problem_difficulty: Problem difficulty score (0.0 to 1.0)
        seed: Random seed for reproducibility
        
    Returns:
        Response time in seconds
    """
    if seed is not None:
        random.seed(seed)
        
    # Base response time adjusted by knowledge and difficulty
    # Higher knowledge reduces time, higher difficulty increases time
    knowledge_factor = 1.0 - (student_knowledge * 0.5)  # 0.5 to 1.0
    difficulty_factor = 1.0 + (problem_difficulty * 0.5)  # 1.0 to 1.5
    
    base_time = 2.0 * knowledge_factor * difficulty_factor
    
    # Add randomness with bounded variance
    noise = random.gauss(0, 0.3)
    response_time = base_time + noise
    
    # Ensure within bounds
    response_time = max(MIN_RESPONSE_TIME, min(MAX_RESPONSE_TIME, response_time))
    
    return round(response_time, 2)

def simulate_comprehension_rating(student_knowledge: float, problem_difficulty: float, 
                                 response_time: float, seed: Optional[int] = None) -> int:
    """
    Simulate a comprehension rating (1-5 Likert scale) based on various factors.
    
    Args:
        student_knowledge: BKT-derived knowledge probability (0.0 to 1.0)
        problem_difficulty: Problem difficulty score (0.0 to 1.0)
        response_time: Actual response time in seconds
        seed: Random seed for reproducibility
        
    Returns:
        Comprehension rating (1-5)
    """
    if seed is not None:
        random.seed(seed)
        
    # Base rating from knowledge vs difficulty
    knowledge_difficulty_ratio = student_knowledge / max(problem_difficulty, 0.1)
    base_rating = 1 + (knowledge_difficulty_ratio * 2.0)
    
    # Adjust for response time (too fast or too slow might indicate confusion)
    if response_time < 1.0:
        time_penalty = 0.2
    elif response_time > 30.0:
        time_penalty = 0.3
    else:
        time_penalty = 0.0
        
    rating = base_rating - time_penalty
    
    # Add small random variation
    noise = random.gauss(0, 0.1)
    rating += noise
    
    # Clamp to 1-5 range and round
    rating = max(COMPREHENSION_MIN, min(COMPREHENSION_MAX, rating))
    return round(rating)

def validate_response_time_distribution(response_times: List[float]) -> Dict[str, Any]:
    """
    Validate that response time distribution has no gaps > 5 seconds.
    
    Args:
        response_times: List of response times in seconds
        
    Returns:
        Dictionary with validation results
    """
    if len(response_times) < 2:
        return {
            "valid": True,
            "max_gap": 0.0,
            "message": "Insufficient data points for gap analysis"
        }
        
    sorted_times = sorted(response_times)
    gaps = []
    
    for i in range(1, len(sorted_times)):
        gap = sorted_times[i] - sorted_times[i-1]
        gaps.append(gap)
        
    max_gap = max(gaps) if gaps else 0.0
    valid = max_gap <= MAX_GAP_SECONDS
    
    return {
        "valid": valid,
        "max_gap": round(max_gap, 2),
        "total_gaps": len(gaps),
        "mean_gap": round(sum(gaps) / len(gaps), 2) if gaps else 0.0,
        "message": "Distribution passes SC-005" if valid else f"Gap of {max_gap:.2f}s exceeds {MAX_GAP_SECONDS}s limit"
    }

def generate_response_metrics(student_data: Dict[str, Any], problem_data: Dict[str, Any],
                             seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Generate response metrics for a single student-problem interaction.
    
    Args:
        student_data: Dictionary containing student knowledge state
        problem_data: Dictionary containing problem difficulty
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary with response_time and comprehension_rating
    """
    if seed is not None:
        random.seed(seed)
        
    student_knowledge = student_data.get("knowledge", 0.5)
    problem_difficulty = problem_data.get("difficulty", 0.5)
    
    response_time = simulate_response_time(
        student_knowledge, 
        problem_difficulty, 
        seed=seed
    )
    
    comprehension_rating = simulate_comprehension_rating(
        student_knowledge,
        problem_difficulty,
        response_time,
        seed=seed + 1 if seed else None
    )
    
    return {
        "response_time": response_time,
        "comprehension_rating": comprehension_rating
    }

def main():
    """
    Main function to demonstrate response metrics generation and validation.
    This function generates a sample dataset and validates the distribution.
    """
    logger.info("Starting response metrics generation and validation...")
    
    # Generate sample student and problem data
    sample_students = [
        {"knowledge": 0.8, "id": "student_1"},
        {"knowledge": 0.5, "id": "student_2"},
        {"knowledge": 0.3, "id": "student_3"},
        {"knowledge": 0.9, "id": "student_4"},
        {"knowledge": 0.4, "id": "student_5"}
    ]
    
    sample_problems = [
        {"difficulty": 0.3, "id": "problem_1"},
        {"difficulty": 0.6, "id": "problem_2"},
        {"difficulty": 0.8, "id": "problem_3"}
    ]
    
    # Generate metrics for all combinations
    all_response_times = []
    all_metrics = []
    
    for i, student in enumerate(sample_students):
        for j, problem in enumerate(sample_problems):
            seed = i * 100 + j * 10
            metrics = generate_response_metrics(student, problem, seed=seed)
            
            record = {
                "student_id": student["id"],
                "problem_id": problem["id"],
                "knowledge": student["knowledge"],
                "difficulty": problem["difficulty"],
                "response_time": metrics["response_time"],
                "comprehension_rating": metrics["comprehension_rating"]
            }
            
            all_metrics.append(record)
            all_response_times.append(metrics["response_time"])
            
            logger.info(f"Generated: Student {student['id']} on Problem {problem['id']} -> "
                        f"RT={metrics['response_time']}s, Rating={metrics['comprehension_rating']}")
    
    # Validate distribution
    validation_result = validate_response_time_distribution(all_response_times)
    
    logger.info(f"Distribution validation: {validation_result['message']}")
    logger.info(f"Max gap: {validation_result['max_gap']}s")
    
    # Save results to data file
    output_dir = "data/derived"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, "response_metrics_sample.json")
    with open(output_file, 'w') as f:
        json.dump({
            "metrics": all_metrics,
            "validation": validation_result,
            "total_records": len(all_metrics)
        }, f, indent=2)
        
    logger.info(f"Saved {len(all_metrics)} records to {output_file}")
    logger.info("Response metrics generation completed successfully.")

if __name__ == "__main__":
    main()
