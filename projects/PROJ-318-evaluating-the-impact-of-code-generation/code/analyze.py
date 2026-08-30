"""
analyze.py - User Story 3: Parameter Coverage Analysis and Statistical Comparison

This module implements:
- Parameter Coverage Score calculation using docstring_parser
- Semantic similarity calculation (auxiliary)
- Wilcoxon signed-rank test
- Final report generation
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from docstring_parser import parse as parse_docstring
from docstring_parser.common import DocstringParam

# Import from project utilities
from utils.coverage import CoverageException, parse_docstring_parameters
from utils.stats import StatsException, run_wilcoxon_test
from utils.exceptions import StatsException as LocalStatsException
from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/analysis.log')
    ]
)
logger = logging.getLogger(__name__)


def calculate_parameter_coverage_score(ast_params: List[str], docstring_text: Optional[str]) -> float:
    """
    Calculate Parameter Coverage Score.

    Score = (matched params / total AST params)

    Args:
        ast_params: List of parameter names extracted from AST
        docstring_text: The generated or human docstring text (or None)

    Returns:
        Float between 0.0 and 1.0 representing coverage score.
        Returns 0.0 if no AST params exist (to avoid division by zero).
    """
    if not ast_params:
        return 0.0

    if not docstring_text or not docstring_text.strip():
        return 0.0

    try:
        # Parse the docstring text to extract parameters
        parsed_docstring = parse_docstring(docstring_text)
        docstring_params = parse_docstring_parameters(parsed_docstring)

        # Convert to sets for comparison
        ast_params_set = set(param.strip().lower() for param in ast_params if param.strip())
        docstring_params_set = set(param.strip().lower() for param in docstring_params if param.strip())

        if not ast_params_set:
            return 0.0

        # Calculate matched parameters
        matched = ast_params_set.intersection(docstring_params_set)
        total_ast = len(ast_params_set)

        score = len(matched) / total_ast
        return round(score, 4)

    except Exception as e:
        logger.warning(f"Error parsing docstring for coverage calculation: {e}")
        return 0.0


def process_results_for_coverage(input_path: str) -> List[Dict[str, Any]]:
    """
    Read results.json, calculate coverage scores, and return enriched records.

    Args:
        input_path: Path to data/processed/results.json

    Returns:
        List of enriched records with 'coverage_score' added.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading results from {input_path}")
    with open(input_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    if not isinstance(results, list):
        raise ValueError(f"Expected list in {input_path}, got {type(results)}")

    enriched_records = []
    total_records = len(results)
    logger.info(f"Processing {total_records} records for coverage calculation")

    for idx, record in enumerate(results):
        if idx % 100 == 0:
            logger.info(f"Processed {idx}/{total_records} records")

        ast_params = record.get('ast_params', [])
        # Check for both human and generated docstrings
        # Priority: generated_docstring if available, else human_docstring
        docstring_text = record.get('generated_docstring') or record.get('human_docstring')

        coverage_score = calculate_parameter_coverage_score(ast_params, docstring_text)

        # Update record
        enriched_record = record.copy()
        enriched_record['coverage_score'] = coverage_score

        # Handle empty/whitespace docstrings (as per T027 logic, though T027 should have run already)
        if not docstring_text or not docstring_text.strip():
            enriched_record['coverage_score'] = 0.0
            enriched_record['needs_review'] = True

        enriched_records.append(enriched_record)

    logger.info(f"Coverage calculation complete. Processed {len(enriched_records)} records.")
    return enriched_records


def calculate_semantic_similarity_batch(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate semantic similarity as an auxiliary metric.

    Note: This is a placeholder implementation. The actual implementation
    would use sentence-transformers (all-MiniLM-L6-v2) as specified in T034.
    For now, we return a dummy value or 0.0 if the model is not loaded.

    Args:
        records: List of enriched records

    Returns:
        List of records with 'semantic_similarity' added.
    """
    # T034 will implement the real semantic similarity calculation
    # For now, we just add a placeholder to maintain structure
    logger.warning("Semantic similarity calculation not yet implemented (T034). Using placeholder.")

    for record in records:
        record['semantic_similarity'] = 0.0  # Placeholder

    return records


def run_wilcoxon_analysis(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run Wilcoxon signed-rank test on coverage scores.

    Compares Human vs LLM coverage scores if both are available.
    Since we are calculating coverage for the generated docstrings,
    we compare against a baseline (e.g., perfect coverage = 1.0) or
    against human docstrings if available in the dataset.

    Args:
        records: List of enriched records with coverage scores

    Returns:
        Dictionary with test results (statistic, p_value, etc.)
    """
    logger.info("Running Wilcoxon signed-rank test")

    # Extract coverage scores
    # We compare generated coverage against human coverage if available
    # Otherwise, we compare against a theoretical maximum (1.0)
    generated_scores = []
    human_scores = []

    for record in records:
        gen_score = record.get('coverage_score', 0.0)
        # If human docstring exists and we have its coverage, use it
        # For this analysis, we'll assume we want to compare generated vs human
        # But since we only calculated coverage for the final output,
        # we need to check if human_docstring exists and calculate its score too
        human_docstring = record.get('human_docstring')
        ast_params = record.get('ast_params', [])

        if human_docstring and human_docstring.strip():
            human_score = calculate_parameter_coverage_score(ast_params, human_docstring)
            human_scores.append(human_score)
            generated_scores.append(gen_score)
        else:
            # If no human docstring, we can't do paired comparison
            # We'll skip these for the Wilcoxon test
            pass

    if len(generated_scores) < 2:
        logger.warning("Not enough data points for Wilcoxon test (need at least 2 pairs)")
        return {
            'statistic': None,
            'p_value': None,
            'n_pairs': len(generated_scores),
            'warning': 'Insufficient data for statistical test'
        }

    if len(generated_scores) < 30:
        logger.warning(f"Small sample size ({len(generated_scores)} pairs) for Wilcoxon test. Proceeding with caution.")

    try:
        statistic, p_value = run_wilcoxon_test(generated_scores, human_scores)
        return {
            'statistic': float(statistic),
            'p_value': float(p_value),
            'n_pairs': len(generated_scores),
            'significant': p_value < 0.05
        }
    except Exception as e:
        logger.error(f"Wilcoxon test failed: {e}")
        return {
            'statistic': None,
            'p_value': None,
            'n_pairs': len(generated_scores),
            'error': str(e)
        }


def generate_final_report(enriched_records: List[Dict[str, Any]], wilcoxon_results: Dict[str, Any], output_path: str):
    """
    Generate the final analysis report.

    Args:
        enriched_records: List of records with coverage scores
        wilcoxon_results: Results from Wilcoxon test
        output_path: Path to save the final report (data/processed/final_report.json)
    """
    logger.info(f"Generating final report to {output_path}")

    # Calculate summary statistics
    total_records = len(enriched_records)
    coverage_scores = [r['coverage_score'] for r in enriched_records]

    if coverage_scores:
        mean_coverage = sum(coverage_scores) / len(coverage_scores)
        min_coverage = min(coverage_scores)
        max_coverage = max(coverage_scores)
    else:
        mean_coverage = 0.0
        min_coverage = 0.0
        max_coverage = 0.0

    # Count records needing review
    needs_review_count = sum(1 for r in enriched_records if r.get('needs_review', False))

    report = {
        'summary': {
            'total_methods': total_records,
            'mean_coverage_score': round(mean_coverage, 4),
            'min_coverage_score': round(min_coverage, 4),
            'max_coverage_score': round(max_coverage, 4),
            'methods_needing_review': needs_review_count
        },
        'wilcoxon_test': wilcoxon_results,
        'records': enriched_records
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"Final report saved to {output_path}")


def main():
    """Main entry point for the analysis pipeline."""
    config = get_config()
    input_path = config.get('results_path', 'data/processed/results.json')
    output_path = config.get('report_path', 'data/processed/final_report.json')

    logger.info(f"Starting analysis pipeline. Input: {input_path}")

    try:
        # Step 1: Calculate parameter coverage scores
        enriched_records = process_results_for_coverage(input_path)

        # Step 2: Calculate semantic similarity (placeholder for T034)
        # This will be implemented in T034
        # enriched_records = calculate_semantic_similarity_batch(enriched_records)

        # Step 3: Run Wilcoxon test
        wilcoxon_results = run_wilcoxon_analysis(enriched_records)

        # Step 4: Generate final report
        generate_final_report(enriched_records, wilcoxon_results, output_path)

        logger.info("Analysis pipeline completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
