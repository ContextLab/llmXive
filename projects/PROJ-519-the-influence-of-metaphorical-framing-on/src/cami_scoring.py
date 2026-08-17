import json
import os
import csv
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional

# CAMI Scale Configuration
# The Community Attitudes towards the Mentally Ill (CAMI) scale typically has 40 items.
# For this implementation, we map the raw response keys to subscales.
# Standard CAMI subscales: Authoritarianism, Benevolence, Social Restrictiveness, Community Mental Health Ideology.
# We assume the survey_interface collected these as:
# 'authoritarianism_1'..'authoritarianism_10', 'benevolence_1'..'benevolence_10', etc.
# Or a flat list of 40 items.
# To be robust, we define a mapping of item_id to (subscale, reverse_scored).
# Using a standard 10-item per subscale structure for demonstration.
CAMI_ITEMS = {
    # Authoritarianism (Items 1-10) - Assume some are reverse scored
    # Format: (subscale_name, is_reverse)
    'authoritarianism_1': ('authoritarianism', True),
    'authoritarianism_2': ('authoritarianism', False),
    'authoritarianism_3': ('authoritarianism', True),
    'authoritarianism_4': ('authoritarianism', False),
    'authoritarianism_5': ('authoritarianism', True),
    'authoritarianism_6': ('authoritarianism', False),
    'authoritarianism_7': ('authoritarianism', True),
    'authoritarianism_8': ('authoritarianism', False),
    'authoritarianism_9': ('authoritarianism', True),
    'authoritarianism_10': ('authoritarianism', False),
    
    # Benevolence (Items 11-20)
    'benevolence_1': ('benevolence', False),
    'benevolence_2': ('benevolence', True),
    'benevolence_3': ('benevolence', False),
    'benevolence_4': ('benevolence', True),
    'benevolence_5': ('benevolence', False),
    'benevolence_6': ('benevolence', True),
    'benevolence_7': ('benevolence', False),
    'benevolence_8': ('benevolence', True),
    'benevolence_9': ('benevolence', False),
    'benevolence_10': ('benevolence', True),
    
    # Social Restrictiveness (Items 21-30)
    'social_restrictiveness_1': ('social_restrictiveness', True),
    'social_restrictiveness_2': ('social_restrictiveness', False),
    'social_restrictiveness_3': ('social_restrictiveness', True),
    'social_restrictiveness_4': ('social_restrictiveness', False),
    'social_restrictiveness_5': ('social_restrictiveness', True),
    'social_restrictiveness_6': ('social_restrictiveness', False),
    'social_restrictiveness_7': ('social_restrictiveness', True),
    'social_restrictiveness_8': ('social_restrictiveness', False),
    'social_restrictiveness_9': ('social_restrictiveness', True),
    'social_restrictiveness_10': ('social_restrictiveness', False),
    
    # Community Mental Health Ideology (Items 31-40)
    'cmhi_1': ('cmhi', False),
    'cmhi_2': ('cmhi', True),
    'cmhi_3': ('cmhi', False),
    'cmhi_4': ('cmhi', True),
    'cmhi_5': ('cmhi', False),
    'cmhi_6': ('cmhi', True),
    'cmhi_7': ('cmhi', False),
    'cmhi_8': ('cmhi', True),
    'cmhi_9': ('cmhi', False),
    'cmhi_10': ('cmhi', True),
}

# Help Seeking Likert Scale (Single item or average of 3 items)
# Assuming keys: 'help_seek_1', 'help_seek_2', 'help_seek_3'
HELP_SEEK_ITEMS = ['help_seek_1', 'help_seek_2', 'help_seek_3']

def load_survey_responses(input_path: str) -> List[Dict[str, Any]]:
    """
    Loads raw survey responses from a JSON file.
    
    Args:
        input_path: Path to the JSON file containing survey responses.
        
    Returns:
        List of response dictionaries.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Survey response file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle structure where data might be {"responses": [...]} or just [...]
    if isinstance(data, dict) and 'responses' in data:
        return data['responses']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Invalid JSON structure: expected list or dict with 'responses' key")

def reverse_score(value: int, scale_min: int = 1, scale_max: int = 5) -> int:
    """
    Reverse scores a Likert item (e.g., 1->5, 5->1).
    
    Args:
        value: The original score.
        scale_min: Minimum value of the scale (default 1).
        scale_max: Maximum value of the scale (default 5).
        
    Returns:
        The reversed score.
    """
    return scale_max + scale_min - value

def calculate_subscale_score(items: Dict[str, int], subscale_items: List[str], 
                             reverse_map: Dict[str, bool]) -> Optional[float]:
    """
    Calculates the average score for a specific subscale.
    
    Args:
        items: Dictionary of all item responses for a participant.
        subscale_items: List of item keys belonging to this subscale.
        reverse_map: Dictionary mapping item keys to boolean reverse_score flag.
        
    Returns:
        Average score (float) or None if no valid items found.
    """
    scores = []
    for item_key in subscale_items:
        if item_key in items:
            val = items[item_key]
            if isinstance(val, (int, float)):
                if reverse_map.get(item_key, False):
                    val = reverse_score(int(val))
                scores.append(val)
    
    if not scores:
        return None
    return sum(scores) / len(scores)

def process_responses(responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Processes a list of raw survey responses to calculate CAMI subscale scores
    and Help-Seeking intent.
    
    Args:
        responses: List of raw response dictionaries.
        
    Returns:
        List of processed dictionaries with calculated scores.
    """
    processed = []
    
    # Build reverse map for quick lookup
    reverse_lookup = {k: v[1] for k, v in CAMI_ITEMS.items()}
    
    # Extract subscale item keys
    subscales = {
        'authoritarianism': [k for k, v in CAMI_ITEMS.items() if v[0] == 'authoritarianism'],
        'benevolence': [k for k, v in CAMI_ITEMS.items() if v[0] == 'benevolence'],
        'social_restrictiveness': [k for k, v in CAMI_ITEMS.items() if v[0] == 'social_restrictiveness'],
        'cmhi': [k for k, v in CAMI_ITEMS.items() if v[0] == 'cmhi'],
    }

    for resp in responses:
        participant_id = resp.get('participant_id')
        if not participant_id:
            continue
        
        # Extract CAMI items
        cami_scores = {}
        for subscale_name, item_keys in subscales.items():
            score = calculate_subscale_score(resp, item_keys, reverse_lookup)
            if score is not None:
                cami_scores[f'{subscale_name}_score'] = round(score, 2)
            else:
                cami_scores[f'{subscale_name}_score'] = None # Missing data

        # Calculate Help Seeking Score
        help_seek_scores = []
        for item in HELP_SEEK_ITEMS:
            if item in resp:
                val = resp[item]
                if isinstance(val, (int, float)):
                    help_seek_scores.append(val)
        
        help_seek_avg = sum(help_seek_scores) / len(help_seek_scores) if help_seek_scores else None

        # Construct output record
        record = {
            'participant_id': participant_id,
            'timestamp': datetime.now().isoformat(),
            'condition_guess': resp.get('condition_guess', 'Unknown'),
            'age': resp.get('age'),
            'gender': resp.get('gender'),
            **cami_scores,
            'help_seek_intent_score': round(help_seek_avg, 2) if help_seek_avg is not None else None
        }
        processed.append(record)
    
    return processed

def save_scores(processed_data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves processed scores to a CSV file.
    
    Args:
        processed_data: List of processed response dictionaries.
        output_path: Path to the output CSV file.
    """
    if not processed_data:
        print("Warning: No data to write.")
        return

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    fieldnames = list(processed_data[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_data)

def main():
    parser = argparse.ArgumentParser(description='Process CAMI survey responses and calculate scores.')
    parser.add_argument('--input', '-i', type=str, default='data/raw/survey_responses.json',
                        help='Path to input survey responses JSON file.')
    parser.add_argument('--output', '-o', type=str, default='data/processed/cami_scores.csv',
                        help='Path to output CSV file.')
    
    args = parser.parse_args()
    
    try:
        print(f"Loading survey responses from {args.input}...")
        raw_data = load_survey_responses(args.input)
        print(f"Loaded {len(raw_data)} responses.")
        
        print("Processing responses and calculating scores...")
        processed_data = process_responses(raw_data)
        print(f"Processed {len(processed_data)} responses.")
        
        print(f"Saving results to {args.output}...")
        save_scores(processed_data, args.output)
        print("Done.")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

if __name__ == '__main__':
    main()
