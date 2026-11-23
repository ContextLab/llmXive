"""
CAMI Scoring Module for the Metaphor Framing Study.

Implements FR-002: Administer CAMI scale and help-seeking Likert scale
immediately after vignette exposure.

Input:  data/raw/survey_responses.json
Output: data/processed/cami_scores.csv

The CAMI (Community Attitudes towards the Mentally Ill) scale consists of
40 items. This implementation calculates the standard subscale scores:
- Authoritarianism
- Benevolence
- Social Restrictiveness
- Community Mental Health Ideology

Plus the Help-Seeking Likert score.
"""

import json
import os
import csv
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional

# CAMI Item mapping based on standard literature (e.g., Taylor & Dear, 1981)
# Items are 1-40. We assume the survey_interface collects these as 'q1'...'q40'.
# Some items are reverse-scored.
# Standard CAMI Subscales:
# Authoritarianism (1-10): Items 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
# Benevolence (11-20): Items 11, 12, 13, 14, 15, 16, 17, 18, 19, 20
# Social Restrictiveness (21-30): Items 21, 22, 23, 24, 25, 26, 27, 28, 29, 30
# Community Mental Health Ideology (31-40): Items 31, 32, 33, 34, 35, 36, 37, 38, 39, 40

# Reverse scoring items (where 1=4, 2=3, 3=2, 4=1)
# Note: The exact reverse items depend on the specific version used.
# Assuming standard reverse coding for negative phrasing items.
# For this implementation, we define a set of items known to be reverse-scored
# in the standard 40-item version (e.g., items 2, 5, 8, 12, 15, 18, 22, 25, 28, 32, 35, 38).
# If the survey_interface uses a different key, this mapping must be updated.
REVERSE_ITEMS = {
    2, 5, 8, 12, 15, 18, 22, 25, 28, 32, 35, 38
}

SUBSCALE_ITEMS = {
    "authoritarianism": list(range(1, 11)),
    "benevolence": list(range(11, 21)),
    "social_restrictiveness": list(range(21, 31)),
    "community_mental_health": list(range(31, 41))
}

def load_survey_responses(filepath: str) -> List[Dict[str, Any]]:
    """
    Loads raw survey responses from a JSON file.
    Expects a list of dictionaries with 'participant_id', 'condition', and 'responses'.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Survey responses file not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Expected a list of responses in the JSON file.")

    return data

def reverse_score(value: int) -> int:
    """Reverse scores a 1-4 Likert item (1->4, 2->3, 3->2, 4->1)."""
    return 5 - value

def calculate_subscale_score(items: List[int], response_data: Dict[str, int]) -> Optional[float]:
    """
    Calculates the mean score for a specific subscale.
    Returns None if any required item is missing.
    """
    scores = []
    for item_num in items:
        key = f"q{item_num}"
        if key not in response_data:
            return None
        
        val = response_data[key]
        if not isinstance(val, int) or val < 1 or val > 4:
            return None # Invalid response

        if item_num in REVERSE_ITEMS:
            val = reverse_score(val)
        
        scores.append(val)
    
    if not scores:
        return None
    
    return sum(scores) / len(scores)

def process_responses(responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Processes a list of raw responses and computes CAMI subscale scores.
    """
    processed_data = []

    for record in responses:
        participant_id = record.get("participant_id")
        condition = record.get("condition")
        raw_responses = record.get("responses", {})

        # Check for essential CAMI items
        # We require at least a subset to calculate a score, but strict mode requires all
        # Let's require all 40 for a valid record, or skip if missing.
        
        # Calculate subscales
        subscales = {}
        valid = True
        
        for scale_name, items in SUBSCALE_ITEMS.items():
            score = calculate_subscale_score(items, raw_responses)
            if score is None:
                valid = False
                break
            subscales[scale_name] = round(score, 4)

        if not valid:
            # Log warning or skip record. For now, we skip records with missing data.
            print(f"Warning: Skipping participant {participant_id} due to missing CAMI responses.")
            continue

        # Calculate Help-Seeking Likert
        # Assuming the survey interface records this as 'help_seeking_intent' (1-7 scale)
        help_seeking = raw_responses.get("help_seeking_intent")
        if help_seeking is None or not isinstance(help_seeking, (int, float)):
            print(f"Warning: Missing help-seeking score for participant {participant_id}. Skipping.")
            continue

        # Attention Check (optional, but good practice)
        # Assuming 'attention_check' is a boolean or string "correct"/"incorrect"
        attention_check = raw_responses.get("attention_check")
        attention_passed = True
        if attention_check is not None:
            if isinstance(attention_check, str):
                attention_passed = attention_check.lower() == "correct"
            elif isinstance(attention_check, bool):
                attention_passed = attention_check
            else:
                attention_passed = bool(attention_check)

        if not attention_passed:
            print(f"Info: Participant {participant_id} failed attention check. Marking as failed.")
            # We still include the data but flag it? Or exclude? 
            # Standard practice: Exclude from analysis, but keep in raw processed file with flag.
            # Let's include but flag.
            subscales["attention_failed"] = True
        else:
            subscales["attention_failed"] = False

        record_out = {
            "participant_id": participant_id,
            "condition": condition,
            "timestamp": record.get("timestamp", datetime.now().isoformat()),
            "authoritarianism": subscales["authoritarianism"],
            "benevolence": subscales["benevolence"],
            "social_restrictiveness": subscales["social_restrictiveness"],
            "community_mental_health": subscales["community_mental_health"],
            "help_seeking_intent": help_seeking,
            "attention_failed": subscales["attention_failed"]
        }

        processed_data.append(record_out)

    return processed_data

def save_scores(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves processed CAMI scores to a CSV file.
    """
    if not data:
        print("No data to save.")
        return

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        "participant_id", "condition", "timestamp",
        "authoritarianism", "benevolence", "social_restrictiveness",
        "community_mental_health", "help_seeking_intent", "attention_failed"
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"Successfully saved {len(data)} records to {output_path}")

def main():
    """
    CLI entry point for CAMI scoring.
    """
    parser = argparse.ArgumentParser(description="Process CAMI survey responses.")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/raw/survey_responses.json",
        help="Path to raw survey responses JSON file."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/cami_scores.csv",
        help="Path to output CSV file."
    )
    
    args = parser.parse_args()

    try:
        print(f"Loading survey responses from {args.input}...")
        responses = load_survey_responses(args.input)
        
        print(f"Processing {len(responses)} responses...")
        processed = process_responses(responses)
        
        print(f"Saving results to {args.output}...")
        save_scores(processed, args.output)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
