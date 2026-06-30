"""
Task T024: Handle missing data - flag as 'unknown' and proceed without halting (FR-006).

This module implements robust handling for missing or incomplete data fields
in the training data estimates and hallucination rates. Instead of halting
the pipeline when data is missing, it flags entries as 'unknown' and allows
the analysis to proceed with available data.
"""

import json
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import from existing API surface
from config import load_config
from setup_logging import get_logger, init_logging

logger = get_logger(__name__)

def flag_missing_as_unknown(data: Dict[str, Any], missing_fields: List[str]) -> Dict[str, Any]:
    """
    Flag missing fields as 'unknown' in the provided data dictionary.
    
    Args:
        data: The input data dictionary
        missing_fields: List of field names that should be treated as missing
    
    Returns:
        Modified data dictionary with missing fields flagged as 'unknown'
    """
    for field in missing_fields:
        if field not in data or data[field] is None:
            data[field] = 'unknown'
            logger.info(f"Flagged missing field '{field}' as 'unknown'")
        elif data[field] == '' or data[field] == '':
            data[field] = 'unknown'
            logger.info(f"Flagged empty field '{field}' as 'unknown'")
    
    return data

def validate_training_estimate(entry: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate a training data estimate entry and flag missing fields.
    
    Args:
        entry: A single model's training data estimate dictionary
    
    Returns:
        Tuple of (validated_entry, list_of_flagged_fields)
    """
    flagged_fields = []
    required_fields = ['speech_hours', 'music_hours', 'env_hours']
    
    for field in required_fields:
        if field not in entry or entry[field] is None:
            entry[field] = 'unknown'
            flagged_fields.append(field)
            logger.debug(f"Model '{entry.get('model_name', 'unknown')}': {field} missing, flagged as 'unknown'")
        elif isinstance(entry[field], str) and entry[field].strip() == '':
            entry[field] = 'unknown'
            flagged_fields.append(field)
            logger.debug(f"Model '{entry.get('model_name', 'unknown')}': {field} empty, flagged as 'unknown'")
    
    # Ensure uncertainty_notes exists
    if 'uncertainty_notes' not in entry or not entry['uncertainty_notes']:
        entry['uncertainty_notes'] = "Data partially missing; estimates derived from proxies where possible"
        if flagged_fields:
            entry['uncertainty_notes'] += f". Missing fields: {', '.join(flagged_fields)}"
    
    return entry, flagged_fields

def process_training_data_estimates(input_path: Path, output_path: Path) -> Dict[str, int]:
    """
    Process training data estimates file, flagging missing values as 'unknown'.
    
    Args:
        input_path: Path to input YAML file
        output_path: Path to output YAML file
    
    Returns:
        Dictionary with counts of processed entries and flagged fields
    """
    logger.info(f"Processing training data estimates from {input_path}")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return {'processed': 0, 'flagged': 0, 'error': 'File not found'}
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if not isinstance(data, list):
        data = [data]
    
    processed_count = 0
    flagged_count = 0
    
    for entry in data:
        if 'model_name' not in entry:
            logger.warning("Skipping entry without model_name")
            continue
        
        validated_entry, flagged_fields = validate_training_estimate(entry)
        flagged_count += len(flagged_fields)
        processed_count += 1
        
        # Update entry in list
        idx = data.index(entry)
        data[idx] = validated_entry
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    
    logger.info(f"Processed {processed_count} entries, flagged {flagged_count} fields as 'unknown'")
    return {
        'processed': processed_count,
        'flagged': flagged_count,
        'output_path': str(output_path)
    }

def handle_missing_hallucination_rates(input_path: Path, output_path: Path) -> Dict[str, int]:
    """
    Handle missing values in hallucination rates CSV, flagging as 'unknown'.
    
    Args:
        input_path: Path to input CSV file
        output_path: Path to output CSV file
    
    Returns:
        Dictionary with counts of processed entries and flagged fields
    """
    logger.info(f"Processing hallucination rates from {input_path}")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return {'processed': 0, 'error': 'File not found'}
    
    import csv
    
    processed_count = 0
    flagged_count = 0
    rows = []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        for row in reader:
            # Flag missing rate values
            if row.get('rate') is None or row.get('rate') == '':
                row['rate'] = 'unknown'
                flagged_count += 1
                logger.warning(f"Domain '{row.get('domain', 'unknown')}': rate missing, flagged as 'unknown'")
            
            # Flag missing CI values
            for ci_field in ['ci_lower', 'ci_upper']:
                if row.get(ci_field) is None or row.get(ci_field) == '':
                    row[ci_field] = 'unknown'
                    flagged_count += 1
                    logger.warning(f"Domain '{row.get('domain', 'unknown')}': {ci_field} missing, flagged as 'unknown'")
            
            rows.append(row)
            processed_count += 1
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Processed {processed_count} entries, flagged {flagged_count} fields as 'unknown'")
    return {
        'processed': processed_count,
        'flagged': flagged_count,
        'output_path': str(output_path)
    }

def main():
    """Main entry point for T024: Handle missing data."""
    init_logging()
    
    config = load_config()
    base_path = Path(config.get('base_path', '.'))
    
    # Define input/output paths
    training_input = base_path / 'data' / 'training_data_estimates.yaml'
    training_output = base_path / 'data' / 'training_data_estimates_cleaned.yaml'
    
    rates_input = base_path / 'results' / 'hallucination_rates.csv'
    rates_output = base_path / 'results' / 'hallucination_rates_cleaned.csv'
    
    results = {}
    
    # Process training data estimates
    if training_input.exists():
        results['training_data'] = process_training_data_estimates(training_input, training_output)
    else:
        logger.warning(f"Training data estimates not found at {training_input}, skipping")
        results['training_data'] = {'skipped': True, 'reason': 'File not found'}
    
    # Process hallucination rates
    if rates_input.exists():
        results['hallucination_rates'] = handle_missing_hallucination_rates(rates_input, rates_output)
    else:
        logger.warning(f"Hallucination rates not found at {rates_input}, skipping")
        results['hallucination_rates'] = {'skipped': True, 'reason': 'File not found'}
    
    # Write summary report
    summary_path = base_path / 'results' / 'missing_data_handling_report.json'
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Missing data handling complete. Report saved to {summary_path}")
    
    # Print summary to stdout
    print("Missing Data Handling Summary:")
    print(f"  Training Data Estimates: {results.get('training_data', {})}")
    print(f"  Hallucination Rates: {results.get('hallucination_rates', {})}")
    print(f"  Summary Report: {summary_path}")

if __name__ == '__main__':
    main()