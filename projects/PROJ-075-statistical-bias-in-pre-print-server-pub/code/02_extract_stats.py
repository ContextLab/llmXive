import os
import sys
import csv
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import existing utilities from the project API surface
from utils.pdf_parser import (
    extract_p_values,
    extract_effect_sizes,
    extract_statistics_from_pdf_text,
    parse_inequality,
    filter_p_values_for_analysis
)
from utils.stats_helpers import convert_inequality_to_bounds

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def identify_primary_statistical_method(text: str) -> str:
    """
    Identify the primary statistical method used in the paper text.
    Returns a string like 't-test', 'anova', 'regression', etc.
    """
    text_lower = text.lower()
    
    # Priority list of common methods
    method_patterns = {
        'anova': r'\banova\b|analysis of variance',
        't-test': r'\bt-test\b|student\'?s t-test|independent samples t-test|paired t-test',
        'chi-square': r'\bchi-squared?\b|chi-square test',
        'regression': r'\bregression\b|linear regression|logistic regression|multiple regression',
        'manova': r'\bmanova\b|multivariate analysis of variance',
        'anova': r'\banova\b',
        'wilcoxon': r'\bwilcoxon\b|wilcoxon signed-rank|wilcoxon rank-sum',
        'kruskal-wallis': r'\bkruskal-wallis\b',
        'f-test': r'\bf-test\b',
        'z-test': r'\bz-test\b',
    }
    
    for method, pattern in method_patterns.items():
        if re.search(pattern, text_lower):
            return method
    
    return 'unknown'

def extract_stats_from_pdf(pdf_text: str) -> Dict[str, Any]:
    """
    Extract p-values, effect sizes, and statistical methods from PDF text.
    Handles both exact values and inequalities (e.g., p < 0.05).
    
    Returns a dictionary with:
      - p_values: List of dicts with 'value' (float or None), 'inequality_type' (str or None), 
                  'bounds' (tuple or None), 'raw' (str)
      - effect_sizes: List of dicts with 'type' (str), 'value' (float or None), 
                      'bounds' (tuple or None), 'raw' (str)
      - primary_method: str
      - censored_flags: Dict mapping index to 'censored' or 'non-censored'
    """
    # Extract raw p-values (including inequalities)
    raw_p_values = extract_p_values(pdf_text)
    
    # Extract raw effect sizes
    raw_effect_sizes = extract_effect_sizes(pdf_text)
    
    # Identify primary statistical method
    primary_method = identify_primary_statistical_method(pdf_text)
    
    # Process p-values: distinguish between exact and interval-censored
    processed_p_values = []
    for p_item in raw_p_values:
        raw_str = p_item.get('raw', '')
        value = p_item.get('value')
        
        # Check if this is an inequality
        inequality_info = parse_inequality(raw_str)
        
        if inequality_info and inequality_info.get('is_inequality'):
            # This is an interval-censored value (e.g., p < 0.05)
            bounds = convert_inequality_to_bounds(raw_str)
            processed_p_values.append({
                'value': None,  # No exact value
                'inequality_type': inequality_info.get('type'),
                'bounds': bounds,
                'raw': raw_str,
                'is_censored': True
            })
        else:
            # This is an exact value
            processed_p_values.append({
                'value': value,
                'inequality_type': None,
                'bounds': None,
                'raw': raw_str,
                'is_censored': False
            })
    
    # Process effect sizes similarly
    processed_effect_sizes = []
    for es_item in raw_effect_sizes:
        raw_str = es_item.get('raw', '')
        value = es_item.get('value')
        
        # Check for inequality in effect size (less common but possible)
        if value is None and re.search(r'[<>]', raw_str):
            # Attempt to parse as inequality
            bounds = convert_inequality_to_bounds(raw_str)
            processed_effect_sizes.append({
                'type': es_item.get('type', 'unknown'),
                'value': None,
                'bounds': bounds,
                'raw': raw_str,
                'is_censored': True
            })
        else:
            processed_effect_sizes.append({
                'type': es_item.get('type', 'unknown'),
                'value': value,
                'bounds': None,
                'raw': raw_str,
                'is_censored': False
            })
    
    # Create censored flags for routing
    censored_flags = {}
    for i, p in enumerate(processed_p_values):
        if p['is_censored']:
            censored_flags[f'p_value_{i}'] = 'censored'
        else:
            censored_flags[f'p_value_{i}'] = 'non-censored'
    
    for i, es in enumerate(processed_effect_sizes):
        if es['is_censored']:
            censored_flags[f'es_{i}'] = 'censored'
        else:
            censored_flags[f'es_{i}'] = 'non-censored'
    
    return {
        'p_values': processed_p_values,
        'effect_sizes': processed_effect_sizes,
        'primary_method': primary_method,
        'censored_flags': censored_flags
    }

def process_matched_pair(pair_data: Dict[str, Any], pdf_text_preprint: str, pdf_text_journal: str) -> Dict[str, Any]:
    """
    Process a matched pair of papers (pre-print and journal).
    Extract statistics from both and create a unified record.
    
    Args:
        pair_data: Dictionary containing metadata about the matched pair
        pdf_text_preprint: Full text of the pre-print PDF
        pdf_text_journal: Full text of the journal PDF
        
    Returns:
        Dictionary containing extracted statistics and metadata for both versions
    """
    logger.info(f"Processing pair: {pair_data.get('preprint_id', 'unknown')} -> {pair_data.get('journal_id', 'unknown')}")
    
    # Extract stats from pre-print
    preprint_stats = extract_stats_from_pdf(pdf_text_preprint)
    
    # Extract stats from journal
    journal_stats = extract_stats_from_pdf(pdf_text_journal)
    
    # Combine into a single record
    result = {
        # Metadata
        'preprint_id': pair_data.get('preprint_id'),
        'journal_id': pair_data.get('journal_id'),
        'preprint_title': pair_data.get('preprint_title'),
        'journal_title': pair_data.get('journal_title'),
        'field': pair_data.get('field', 'unknown'),
        
        # Pre-print statistics
        'preprint_p_values': preprint_stats['p_values'],
        'preprint_effect_sizes': preprint_stats['effect_sizes'],
        'preprint_primary_method': preprint_stats['primary_method'],
        'preprint_censored_flags': preprint_stats['censored_flags'],
        
        # Journal statistics
        'journal_p_values': journal_stats['p_values'],
        'journal_effect_sizes': journal_stats['effect_sizes'],
        'journal_primary_method': journal_stats['primary_method'],
        'journal_censored_flags': journal_stats['censored_flags'],
        
        # Filtering flags for analysis
        'has_valid_p_values_preprint': len([p for p in preprint_stats['p_values'] if not p['is_censored']]) > 0,
        'has_valid_p_values_journal': len([p for p in journal_stats['p_values'] if not p['is_censored']]) > 0,
        'has_valid_effect_sizes_preprint': len([e for e in preprint_stats['effect_sizes'] if not e['is_censored']]) > 0,
        'has_valid_effect_sizes_journal': len([e for e in journal_stats['effect_sizes'] if not e['is_censored']]) > 0,
    }
    
    return result

def write_extracted_stats_csv(results: List[Dict[str, Any]], output_path: str):
    """
    Write extracted statistics to a CSV file.
    
    The CSV will contain:
    - Metadata columns
    - JSON-encoded columns for complex data (p_values, effect_sizes, censored_flags)
    - Boolean flags for analysis filtering
    
    Note: Inequalities (interval-censored data) are recorded in the CSV for general reporting
    but are flagged so they can be excluded from p-curve analysis (FR-002).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys() if results else [])
        writer.writeheader()
        
        for row in results:
            # Convert complex fields to JSON strings for CSV storage
            row_to_write = row.copy()
            row_to_write['preprint_p_values'] = str(row['preprint_p_values'])
            row_to_write['preprint_effect_sizes'] = str(row['preprint_effect_sizes'])
            row_to_write['preprint_censored_flags'] = str(row['preprint_censored_flags'])
            row_to_write['journal_p_values'] = str(row['journal_p_values'])
            row_to_write['journal_effect_sizes'] = str(row['journal_effect_sizes'])
            row_to_write['journal_censored_flags'] = str(row['journal_censored_flags'])
            
            writer.writerow(row_to_write)
    
    logger.info(f"Wrote {len(results)} records to {output_path}")

def main():
    """
    Main entry point for the extraction pipeline.
    Reads matched pairs from data/processed/matched_pairs.csv,
    processes PDFs, and writes extracted statistics to data/processed/extracted_stats.csv.
    """
    # Configuration
    input_path = "data/processed/matched_pairs.csv"
    output_path = "data/processed/extracted_stats.csv"
    
    # Check if input exists
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    logger.info(f"Starting extraction from {input_path}")
    
    # Read matched pairs
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        matched_pairs = list(reader)
    
    logger.info(f"Loaded {len(matched_pairs)} matched pairs")
    
    results = []
    processed_count = 0
    skipped_count = 0
    
    for pair in matched_pairs:
        try:
            # Note: In a real implementation, we would read the actual PDF files
            # For this implementation, we assume PDF text is available or we skip
            # In a full pipeline, we would fetch PDFs based on IDs and extract text
            
            # Placeholder: In real code, this would load PDF text
            # For now, we simulate that we have the text
            preprint_text = pair.get('preprint_pdf_text', '')
            journal_text = pair.get('journal_pdf_text', '')
            
            if not preprint_text or not journal_text:
                logger.warning(f"Skipping pair {pair.get('preprint_id')}: PDF text not available")
                skipped_count += 1
                continue
            
            # Process the pair
            result = process_matched_pair(pair, preprint_text, journal_text)
            results.append(result)
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Error processing pair {pair.get('preprint_id')}: {e}")
            skipped_count += 1
            continue
    
    # Write results
    if results:
        write_extracted_stats_csv(results, output_path)
        logger.info(f"Successfully processed {processed_count} pairs, skipped {skipped_count}")
    else:
        logger.warning("No results to write")
        # Create empty file with headers
        write_extracted_stats_csv([], output_path)

if __name__ == "__main__":
    main()