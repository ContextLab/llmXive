import random
import json
import csv
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
INTERMEDIATE_DIR = Path("data/intermediate")
EXPLANATIONS_FILE = INTERMEDIATE_DIR / "explanations.json"
SURVEY_CONDITIONS_FILE = INTERMEDIATE_DIR / "survey_conditions.json"
MOCK_RESPONSES_FILE = INTERMEDIATE_DIR / "mock_responses.csv"
RESPONSES_FILE = INTERMEDIATE_DIR / "responses.csv"

# Ensure output directories exist
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

def load_explanations() -> List[Dict[str, Any]]:
    """Load explanations from the intermediate JSON file."""
    if not EXPLANATIONS_FILE.exists():
        logger.error(f"Explanations file not found: {EXPLANATIONS_FILE}")
        return []
    
    try:
        with open(EXPLANATIONS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Loaded {len(data)} explanations")
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse explanations JSON: {e}")
        return []

def stratified_randomize(snippet_ids: List[str], n_participants: int, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Stratified assignment of participants to conditions (A, B, C).
    Conditions: A=Code Only, B=Code+LLM, C=Code+Docstring.
    """
    random.seed(seed)
    conditions = ['A', 'B', 'C']
    participants = []
    
    # Assign each participant a condition in a round-robin fashion for balance
    for i in range(n_participants):
        participant_id = f"P{i+1:03d}"
        condition = conditions[i % 3]
        
        # Randomly select a snippet for this participant
        snippet_id = random.choice(snippet_ids)
        
        participants.append({
            'participant_id': participant_id,
            'condition': condition,
            'snippet_id': snippet_id
        })
    
    return participants

def render_condition_a(code: str) -> Dict[str, Any]:
    """Condition A: Code only."""
    return {
        'type': 'A',
        'display': {'code': code},
        'prompt': 'Please analyze the following code snippet and answer the comprehension question.'
    }

def render_condition_b(code: str, explanation: str) -> Dict[str, Any]:
    """Condition B: Code + LLM Explanation."""
    return {
        'type': 'B',
        'display': {'code': code, 'explanation': explanation},
        'prompt': 'Please analyze the following code snippet and its explanation, then answer the comprehension question.'
    }

def render_condition_c(code: str, docstring: Optional[str] = None) -> Dict[str, Any]:
    """Condition C: Code + Official Docstring (or placeholder if missing)."""
    display_doc = docstring if docstring else "No official docstring available."
    return {
        'type': 'C',
        'display': {'code': code, 'docstring': display_doc},
        'prompt': 'Please analyze the following code snippet and its docstring, then answer the comprehension question.'
    }

def save_survey_conditions(participants: List[Dict[str, Any]], explanations: List[Dict[str, Any]]) -> None:
    """
    Save the rendered survey conditions for all participants.
    Explanations are used to map snippet_id to explanation text.
    """
    # Create a lookup map for explanations
    explanation_map = {e['snippet_id']: e for e in explanations}
    
    rendered_survey = []
    for p in participants:
        snippet_id = p['snippet_id']
        condition = p['condition']
        
        # Find the snippet data (we assume we have access to the full snippet data)
        # For now, we'll fetch the explanation entry which contains code
        exp_entry = explanation_map.get(snippet_id)
        if not exp_entry:
            logger.warning(f"Snippet {snippet_id} not found in explanations, skipping.")
            continue
        
        code = exp_entry['code']
        
        if condition == 'A':
            rendered = render_condition_a(code)
        elif condition == 'B':
            explanation = exp_entry.get('explanation', '')
            rendered = render_condition_b(code, explanation)
        elif condition == 'C':
            # Docstring is not currently stored in explanations.json, so we use placeholder
            rendered = render_condition_c(code, docstring=None)
        else:
            logger.error(f"Unknown condition {condition}")
            continue
        
        rendered['participant_id'] = p['participant_id']
        rendered['condition'] = condition
        rendered['snippet_id'] = snippet_id
        rendered_survey.append(rendered)
    
    with open(SURVEY_CONDITIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(rendered_survey, f, indent=2)
    logger.info(f"Saved {len(rendered_survey)} survey conditions to {SURVEY_CONDITIONS_FILE}")

def run_mock_survey(n_participants: int = 10, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Simulate N participants answering the survey.
    Generates random latency > 30s (uniform distribution).
    """
    random.seed(seed)
    
    explanations = load_explanations()
    if not explanations:
        logger.error("No explanations available to run mock survey.")
        return []
    
    snippet_ids = [e['snippet_id'] for e in explanations]
    participants = stratified_randomize(snippet_ids, n_participants, seed)
    
    mock_responses = []
    for p in participants:
        # Simulate answer (True/False) with 70% accuracy
        answer = random.random() < 0.7
        
        # Simulate latency > 30s (uniform between 30 and 120 seconds)
        latency_s = random.uniform(30, 120)
        latency_ms = int(latency_s * 1000)
        
        # Timestamp
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        
        mock_responses.append({
            'participant_id': p['participant_id'],
            'condition': p['condition'],
            'snippet_id': p['snippet_id'],
            'answer': answer,
            'latency_ms': latency_ms,
            'timestamp': timestamp
        })
    
    return mock_responses

def save_mock_responses(responses: List[Dict[str, Any]]) -> None:
    """Save mock responses to CSV."""
    if not responses:
        logger.warning("No responses to save.")
        return
    
    fieldnames = ['participant_id', 'condition', 'snippet_id', 'answer', 'latency_ms', 'timestamp']
    
    with open(MOCK_RESPONSES_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(responses)
    
    logger.info(f"Saved {len(responses)} mock responses to {MOCK_RESPONSES_FILE}")

def calculate_missing_count(responses: List[Dict[str, Any]], total_questions_per_participant: int = 3) -> List[Dict[str, Any]]:
    """
    Calculate missing_count (number of unanswered questions) per participant.
    In this simulation, we assume a 'missing' answer is represented by a specific marker.
    For the mock data, we assume all questions are answered, so missing_count is 0.
    However, for real data ingestion, we would check for nulls or specific markers.
    
    This function updates the response records with the 'missing_count' field.
    """
    # Group responses by participant
    participant_responses = {}
    for r in responses:
        pid = r['participant_id']
        if pid not in participant_responses:
            participant_responses[pid] = []
        participant_responses[pid].append(r)
    
    updated_responses = []
    for r in responses:
        pid = r['participant_id']
        # In a real scenario, we might check if 'answer' is None or a specific placeholder
        # For now, we assume all are answered, so missing_count = 0
        # If the data had a 'missing' marker, we would count those here.
        # Example logic for real data:
        # count = sum(1 for resp in participant_responses[pid] if resp.get('answer') is None)
        count = 0 
        
        r['missing_count'] = count
        updated_responses.append(r)
    
    return updated_responses

def save_responses_with_missing(responses: List[Dict[str, Any]], output_file: Path = RESPONSES_FILE) -> None:
    """Save responses including the calculated missing_count."""
    if not responses:
        logger.warning("No responses to save.")
        return
    
    # Ensure missing_count is present
    updated_responses = calculate_missing_count(responses)
    
    fieldnames = ['participant_id', 'condition', 'snippet_id', 'answer', 'latency_ms', 'timestamp', 'missing_count']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_responses)
    
    logger.info(f"Saved {len(updated_responses)} responses with missing_count to {output_file}")

def main():
    """Main entry point for survey logic and mock survey generation."""
    logger.info("Starting survey logic and mock survey generation.")
    
    # Run mock survey
    mock_responses = run_mock_survey(n_participants=10, seed=42)
    
    if mock_responses:
        # Save mock responses to intermediate file
        save_mock_responses(mock_responses)
        
        # Calculate missing_count and save to responses.csv
        save_responses_with_missing(mock_responses, RESPONSES_FILE)
        
        logger.info("Mock survey completed and responses saved with missing_count.")
    else:
        logger.error("Mock survey failed to generate responses.")

if __name__ == "__main__":
    main()
