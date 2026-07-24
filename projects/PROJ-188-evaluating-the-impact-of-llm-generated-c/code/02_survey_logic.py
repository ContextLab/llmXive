import random
import json
import csv
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data")
INTERMEDIATE_DIR = DATA_DIR / "intermediate"
EXPLANATIONS_FILE = INTERMEDIATE_DIR / "explanations.json"
SURVEY_CONDITIONS_FILE = INTERMEDIATE_DIR / "survey_conditions.json"
MOCK_RESPONSES_FILE = INTERMEDIATE_DIR / "mock_responses.csv"
RESPONSES_FILE = INTERMEDIATE_DIR / "responses.csv"
TOTAL_QUESTIONS = 3  # Per participant as per spec

def ensure_dirs():
    """Ensure all required directories exist."""
    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {INTERMEDIATE_DIR}")

def load_explanations() -> List[Dict[str, Any]]:
    """Load explanations from the JSON file."""
    if not EXPLANATIONS_FILE.exists():
        raise FileNotFoundError(f"Explanations file not found: {EXPLANATIONS_FILE}")
    
    with open(EXPLANATIONS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} explanations from {EXPLANATIONS_FILE}")
    return data

def stratified_randomize(snippets: List[Dict[str, Any]], seed: int = 42) -> List[Dict[str, Any]]:
    """
    Perform stratified randomization of snippets to conditions.
    Stratify by complexity label (low, medium, high).
    """
    random.seed(seed)
    
    # Group by complexity
    groups = {"low": [], "medium": [], "high": []}
    for snippet in snippets:
        label = snippet.get("complexity", "low")
        if label in groups:
            groups[label].append(snippet)
        else:
            groups["low"].append(snippet)  # Default to low if unknown
    
    # Shuffle each group
    for label in groups:
        random.shuffle(groups[label])
    
    # Interleave (round-robin) to ensure balanced distribution
    result = []
    max_len = max(len(g) for g in groups.values()) if groups else 0
    
    for i in range(max_len):
        for label in ["low", "medium", "high"]:
            if i < len(groups[label]):
                result.append(groups[label][i])
    
    # Shuffle final result to break any remaining order patterns
    random.shuffle(result)
    return result

def render_condition_a(code: str) -> Dict[str, Any]:
    """Render Condition A: Code Only."""
    return {
        "condition": "A",
        "type": "code_only",
        "content": code,
        "explanation": None,
        "docstring": None
    }

def render_condition_b(code: str, explanation: str) -> Dict[str, Any]:
    """Render Condition B: Code + LLM Explanation."""
    return {
        "condition": "B",
        "type": "code_plus_llm",
        "content": code,
        "explanation": explanation,
        "docstring": None
    }

def render_condition_c(code: str, docstring: Optional[str] = None) -> Dict[str, Any]:
    """Render Condition C: Code + Official Docstring (or placeholder)."""
    if not docstring or not docstring.strip():
        docstring = "No Doc"
    
    return {
        "condition": "C",
        "type": "code_plus_docstring",
        "content": code,
        "explanation": None,
        "docstring": docstring
    }

def save_survey_conditions(conditions: List[Dict[str, Any]], filepath: Path):
    """Save rendered survey conditions to JSON."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(conditions, f, indent=2)
    logger.info(f"Saved {len(conditions)} survey conditions to {filepath}")

def run_mock_survey(n_participants: int = 10, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Simulate N participants answering survey questions.
    Randomly assign conditions and generate mock responses.
    """
    random.seed(seed)
    
    # Load snippets and explanations
    try:
        explanations = load_explanations()
    except FileNotFoundError:
        logger.warning("Explanations file not found. Using empty list.")
        explanations = []
    
    if not explanations:
        logger.error("No snippets available for mock survey.")
        return []
    
    # Randomize snippets
    randomized_snippets = stratified_randomize(explanations, seed)
    
    # Ensure we have enough snippets
    if len(randomized_snippets) < n_participants:
        # Repeat snippets if necessary
        randomized_snippets = (randomized_snippets * (n_participants // len(randomized_snippets) + 1))[:n_participants]
    
    responses = []
    
    for i in range(n_participants):
        snippet = randomized_snippets[i]
        snippet_id = snippet.get("snippet_id", f"snippet_{i}")
        code = snippet.get("code", "")
        explanation = snippet.get("explanation", "")
        docstring = snippet.get("docstring", None)
        
        # Assign condition (A, B, or C) - round-robin for balance
        condition_char = ["A", "B", "C"][i % 3]
        
        if condition_char == "A":
            rendered = render_condition_a(code)
        elif condition_char == "B":
            rendered = render_condition_b(code, explanation)
        else:
            rendered = render_condition_c(code, docstring)
        
        # Generate mock answers
        # Randomly decide which questions are answered (to simulate missing data)
        # Probability of missing ~10% per question
        answered_questions = []
        missing_count = 0
        
        for q_idx in range(TOTAL_QUESTIONS):
            if random.random() > 0.1:  # 90% chance to answer
                # Random answer (True/False)
                answer = random.choice([True, False])
                answered_questions.append(answer)
            else:
                missing_count += 1
                answered_questions.append(None)  # Missing
        
        # Calculate latency (Uniform(30000, 300000) ms)
        latency_ms = random.randint(30000, 300000)
        
        # Generate timestamp
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        
        # Create response record
        # If all answers are missing, still record the participant with missing_count = TOTAL_QUESTIONS
        # If some are missing, record them as None or a placeholder
        # The task requires appending missing_count to response records.
        # We'll store the answers as a list or JSON string, and include missing_count explicitly.
        
        # For simplicity in CSV, we'll store the primary answer (first non-missing) or a placeholder
        # and include missing_count as a separate column.
        
        # Determine the 'answer' field for CSV (e.g., the first answered question, or False if all missing)
        primary_answer = answered_questions[0] if answered_questions and answered_questions[0] is not None else False
        
        response_record = {
            "participant_id": f"p{i+1:03d}",
            "condition": condition_char,
            "snippet_id": snippet_id,
            "answer": str(primary_answer),  # Convert bool to string for CSV
            "latency_ms": latency_ms,
            "timestamp": timestamp,
            "missing_count": missing_count,
            "answers_detail": json.dumps(answered_questions)  # Store full details for validation
        }
        
        responses.append(response_record)
    
    logger.info(f"Generated {len(responses)} mock responses.")
    return responses

def save_mock_responses(responses: List[Dict[str, Any]], filepath: Path):
    """Save mock responses to CSV."""
    if not responses:
        logger.warning("No responses to save.")
        return
    
    fieldnames = ["participant_id", "condition", "snippet_id", "answer", "latency_ms", "timestamp", "missing_count", "answers_detail"]
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(responses)
    
    logger.info(f"Saved {len(responses)} mock responses to {filepath}")

def calculate_missing_count_per_participant(responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate missing_count for each participant and append it to the response records.
    This function ensures the 'missing_count' field is present and accurate.
    """
    updated_responses = []
    for resp in responses:
        # If missing_count is already present and valid, keep it
        if "missing_count" in resp and isinstance(resp["missing_count"], int):
            resp["missing_count"] = resp["missing_count"]
        else:
            # Recalculate based on answers_detail if available
            if "answers_detail" in resp:
                try:
                    answers = json.loads(resp["answers_detail"])
                    missing = sum(1 for a in answers if a is None)
                    resp["missing_count"] = missing
                except (json.JSONDecodeError, TypeError):
                    resp["missing_count"] = 0
            else:
                # Default to 0 if no detail available
                resp["missing_count"] = 0
        
        updated_responses.append(resp)
    
    return updated_responses

def main():
    """Main entry point for survey logic and mock survey generation."""
    ensure_dirs()
    
    # Run mock survey
    mock_responses = run_mock_survey(n_participants=10, seed=42)
    
    # Calculate missing counts (ensures the field is present and accurate)
    mock_responses = calculate_missing_count_per_participant(mock_responses)
    
    # Save mock responses
    save_mock_responses(mock_responses, MOCK_RESPONSES_FILE)
    
    # Also save to the main responses file (as per T021b dependency)
    save_mock_responses(mock_responses, RESPONSES_FILE)
    
    logger.info("Survey logic and missing count calculation completed successfully.")
    return mock_responses

if __name__ == "__main__":
    main()
