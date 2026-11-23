"""
Module for extracting discussion data for the Gut Microbiome and Cognitive Decline study.
Reads correlation results and memory logs to prepare data for the Discussion section.
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CORRELATION_RESULTS_PATH = DATA_PROCESSED_DIR / "correlation_results.csv"
MEMORY_LOG_PATH = DATA_PROCESSED_DIR / "memory_log.txt"
DISCUSSION_DATA_OUTPUT_PATH = DATA_PROCESSED_DIR / "discussion_data_extracted.json"


def load_correlation_results():
    """
    Load correlation results from CSV.

    Returns:
        pd.DataFrame: DataFrame containing correlation results.

    Raises:
        FileNotFoundError: If the correlation results file does not exist.
        ValueError: If the file is empty or has incorrect schema.
    """
    if not CORRELATION_RESULTS_PATH.exists():
        raise FileNotFoundError(f"Correlation results file not found: {CORRELATION_RESULTS_PATH}")

    try:
        df = pd.read_csv(CORRELATION_RESULTS_PATH)
        if df.empty:
            raise ValueError("Correlation results file is empty.")

        required_columns = ['genus', 'cognitive_score', 'rho', 'p-value', 'adj-p-value', 'interpretation']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in correlation results: {missing_cols}")

        logger.info(f"Loaded {len(df)} correlation results from {CORRELATION_RESULTS_PATH}")
        return df
    except Exception as e:
        logger.error(f"Error loading correlation results: {e}")
        raise


def load_memory_log():
    """
    Load memory usage log from text file.

    Returns:
        dict: Dictionary containing memory log statistics.

    Raises:
        FileNotFoundError: If the memory log file does not exist.
        ValueError: If the file is empty or cannot be parsed.
    """
    if not MEMORY_LOG_PATH.exists():
        raise FileNotFoundError(f"Memory log file not found: {MEMORY_LOG_PATH}")

    try:
        with open(MEMORY_LOG_PATH, 'r') as f:
            lines = f.readlines()

        if not lines:
            raise ValueError("Memory log file is empty.")

        # Parse memory log entries
        # Expected format: "timestamp - memory_usage_mb - peak_memory_mb - status"
        memory_data = {
            'entries': [],
            'max_memory_mb': 0.0,
            'avg_memory_mb': 0.0,
            'total_entries': 0
        }

        memory_values = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split(' - ')
            if len(parts) >= 3:
                try:
                    timestamp = parts[0]
                    memory_mb = float(parts[1])
                    peak_mb = float(parts[2])
                    status = parts[3] if len(parts) > 3 else "unknown"

                    entry = {
                        'timestamp': timestamp,
                        'memory_mb': memory_mb,
                        'peak_memory_mb': peak_mb,
                        'status': status
                    }
                    memory_data['entries'].append(entry)
                    memory_values.append(memory_mb)
                    if peak_mb > memory_data['max_memory_mb']:
                        memory_data['max_memory_mb'] = peak_mb
                except ValueError:
                    logger.warning(f"Could not parse memory log line: {line}")
                    continue

        memory_data['total_entries'] = len(memory_data['entries'])
        if memory_values:
            memory_data['avg_memory_mb'] = sum(memory_values) / len(memory_values)

        logger.info(f"Loaded {memory_data['total_entries']} memory log entries from {MEMORY_LOG_PATH}")
        return memory_data
    except Exception as e:
        logger.error(f"Error loading memory log: {e}")
        raise


def extract_discussion_data():
    """
    Extract and compile data needed for the Discussion section.

    This function:
    1. Loads correlation results (significant genus-score associations)
    2. Loads memory usage logs (resource utilization and limitations)
    3. Compiles summary statistics for discussion points
    4. Saves the extracted data to a JSON file

    Returns:
        dict: Compiled discussion data including correlation summaries and resource metrics.

    Raises:
        FileNotFoundError: If required input files are missing.
        ValueError: If data cannot be processed.
    """
    logger.info("Starting discussion data extraction...")

    # Load correlation results
    logger.info("Loading correlation results...")
    correlation_df = load_correlation_results()

    # Load memory log
    logger.info("Loading memory log...")
    memory_log = load_memory_log()

    # Compile correlation discussion data
    significant_pairs = correlation_df[correlation_df['adj-p-value'] < 0.05]
    total_pairs = len(correlation_df)
    significant_count = len(significant_pairs)

    # Calculate correlation strength distribution
    strong_positive = significant_pairs[significant_pairs['rho'] > 0.5]
    moderate_positive = significant_pairs[(significant_pairs['rho'] > 0.3) & (significant_pairs['rho'] <= 0.5)]
    strong_negative = significant_pairs[significant_pairs['rho'] < -0.5]
    moderate_negative = significant_pairs[(significant_pairs['rho'] >= -0.5) & (significant_pairs['rho'] < -0.3)]

    correlation_summary = {
        'total_tested_pairs': total_pairs,
        'significant_pairs': significant_count,
        'strong_positive_correlations': len(strong_positive),
        'moderate_positive_correlations': len(moderate_positive),
        'strong_negative_correlations': len(strong_negative),
        'moderate_negative_correlations': len(moderate_negative),
        'top_10_positive': significant_pairs.nlargest(10, 'rho')[['genus', 'rho', 'adj-p-value']].to_dict('records'),
        'top_10_negative': significant_pairs.nsmallest(10, 'rho')[['genus', 'rho', 'adj-p-value']].to_dict('records')
    }

    # Compile memory/resource discussion data
    resource_summary = {
        'max_memory_mb': memory_log['max_memory_mb'],
        'avg_memory_mb': memory_log['avg_memory_mb'],
        'total_log_entries': memory_log['total_entries'],
        'memory_limit_status': 'within_limit' if memory_log['max_memory_mb'] < 7000 else 'exceeded_limit',
        'resource_constraints_discussion': (
            f"Peak memory usage was {memory_log['max_memory_mb']:.2f} MB. "
            f"Average memory usage was {memory_log['avg_memory_mb']:.2f} MB. "
            f"{'Memory constraints were respected.' if memory_log['max_memory_mb'] < 7000 else 'Memory limits were exceeded during execution.'}"
        )
    }

    # Compile final discussion data
    discussion_data = {
        'correlation_summary': correlation_summary,
        'resource_summary': resource_summary,
        'discussion_points': [
            {
                'point': 'Significant associations found',
                'evidence': f"{significant_count} out of {total_pairs} genus-cognitive score pairs showed significant associations (FDR-corrected p < 0.05)",
                'implication': 'Suggests specific microbial taxa may be linked to cognitive decline'
            },
            {
                'point': 'Correlation strength distribution',
                'evidence': f"{len(strong_positive)} strong positive, {len(moderate_positive)} moderate positive, {len(strong_negative)} strong negative, {len(moderate_negative)} moderate negative correlations",
                'implication': 'Mixed directionality suggests complex gut-brain axis interactions'
            },
            {
                'point': 'Resource constraints',
                'evidence': resource_summary['resource_constraints_discussion'],
                'implication': 'Computational limitations may affect model complexity and sample size'
            },
            {
                'point': 'Associational nature',
                'evidence': 'All findings are associational (correlation-based), not causal',
                'implication': 'Results require validation through longitudinal and interventional studies'
            }
        ],
        'limitations': [
            'Cross-sectional design limits causal inference',
            'Memory constraints limited sample size and model complexity',
            'FDR correction may have reduced power to detect weaker associations',
            'Potential confounding variables not fully accounted for'
        ],
        'extraction_timestamp': pd.Timestamp.now().isoformat()
    }

    # Save extracted data
    logger.info(f"Saving discussion data to {DISCUSSION_DATA_OUTPUT_PATH}...")
    try:
        with open(DISCUSSION_DATA_OUTPUT_PATH, 'w') as f:
            json.dump(discussion_data, f, indent=2, default=str)
        logger.info(f"Successfully saved discussion data to {DISCUSSION_DATA_OUTPUT_PATH}")
    except Exception as e:
        logger.error(f"Error saving discussion data: {e}")
        raise

    return discussion_data


def main():
    """
    Main entry point for discussion data extraction.
    """
    try:
        discussion_data = extract_discussion_data()
        print(f"Discussion data extracted successfully.")
        print(f"  - Significant associations: {discussion_data['correlation_summary']['significant_pairs']}")
        print(f"  - Peak memory usage: {discussion_data['resource_summary']['max_memory_mb']:.2f} MB")
        print(f"  - Output file: {DISCUSSION_DATA_OUTPUT_PATH}")
        return 0
    except Exception as e:
        logger.error(f"Discussion data extraction failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())