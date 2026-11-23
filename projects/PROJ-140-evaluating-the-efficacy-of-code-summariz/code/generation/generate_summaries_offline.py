"""
Offline Summary Generation for CI Testing (Simulation Mode)

This script generates simulated LLM summaries and rule-based summaries
for all tasks in the stratified sample. It is designed to run in CI
without GPU access, producing valid CSV artifacts for downstream
simulation tasks (T015-base, T015-llm, T015-rule).

Outputs:
    data/summaries/llm_summaries_sim.csv: Simulated LLM summaries
    data/summaries/rule_summaries.csv: Rule-based summaries (fallback source)
"""

import os
import sys
import csv
import json
import random
import hashlib
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_utils import get_logger

# Configuration
RANDOM_SEED = 42
OUTPUT_DIR = PROJECT_ROOT / "data" / "summaries"
INPUT_GROUND_TRUTH = PROJECT_ROOT / "data" / "raw" / "defects4j" / "ground_truth.csv"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)

def load_ground_truth():
    """
    Load the stratified sample of buggy methods from ground_truth.csv.
    Validates that the file exists and contains required columns.
    """
    if not INPUT_GROUND_TRUTH.exists():
        raise FileNotFoundError(
            f"Ground truth file not found: {INPUT_GROUND_TRUTH}. "
            "Please run T013 (download_defects4j.py) first."
        )

    rows = []
    with open(INPUT_GROUND_TRUTH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required_cols = {'task_id', 'method_id', 'ground_truth_line', 'project_name'}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                f"Ground truth file missing required columns. "
                f"Found: {reader.fieldnames}, Required: {required_cols}"
            )

        for row in reader:
            rows.append(row)

    if not rows:
        raise ValueError("Ground truth file is empty after reading.")

    logger.info(f"Loaded {len(rows)} tasks from ground truth.")
    return rows

def generate_llm_summary_text(task_id, method_id, project_name):
    """
    Generates a simulated LLM summary text.
    In CI mode, this is a deterministic mock based on the task ID.
    """
    # Deterministic mock generation based on task_id
    random.seed(hash(task_id) % (2**32))
    verbs = ["Analyzes", "Computes", "Validates", "Processes", "Retrieves", "Updates"]
    nouns = ["input parameters", "data structures", "error states", "configuration values", "user requests"]
    outcomes = ["and returns a result.", "handling potential exceptions.", "with error logging.", "for downstream processing."]

    verb = random.choice(verbs)
    noun = random.choice(nouns)
    outcome = random.choice(outcomes)

    summary = f"{verb} {noun} {outcome}"
    return summary

def generate_rule_summary_text(task_id, method_id, project_name):
    """
    Generates a rule-based summary text.
    This serves as the fallback source for T015-llm and T015-rule.
    """
    # Deterministic rule-based generation
    # Simulates extracting a comment or signature
    return f"[Rule-Based] Summary for {method_id} in {project_name}: Method signature extraction."

def save_summaries_to_csv(summaries, output_path, summary_type):
    """
    Saves a list of summary dictionaries to a CSV file.
    Validates schema before writing.
    """
    if not summaries:
        raise ValueError(f"No summaries to save for {summary_type}.")

    required_fields = {'task_id', 'summary_text', 'method_id'}
    if not required_fields.issubset(set(summaries[0].keys())):
        raise ValueError(f"Summary schema mismatch. Expected {required_fields}.")

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=required_fields)
        writer.writeheader()
        writer.writerows(summaries)

    logger.info(f"Saved {len(summaries)} {summary_type} summaries to {output_path}")

def main():
    """
    Main entry point for offline summary generation.
    """
    logger.info("Starting offline summary generation (Simulation Mode)...")

    try:
        # 1. Load ground truth
        ground_truth = load_ground_truth()

        # 2. Generate Simulated LLM Summaries
        llm_summaries = []
        for task in ground_truth:
            summary_text = generate_llm_summary_text(
                task['task_id'],
                task['method_id'],
                task['project_name']
            )
            llm_summaries.append({
                'task_id': task['task_id'],
                'summary_text': summary_text,
                'method_id': task['method_id']
            })

        output_llm = OUTPUT_DIR / "llm_summaries_sim.csv"
        save_summaries_to_csv(llm_summaries, output_llm, "LLM Simulated")

        # 3. Generate Rule-Based Summaries (Fallback)
        rule_summaries = []
        for task in ground_truth:
            summary_text = generate_rule_summary_text(
                task['task_id'],
                task['method_id'],
                task['project_name']
            )
            rule_summaries.append({
                'task_id': task['task_id'],
                'summary_text': summary_text,
                'method_id': task['method_id']
            })

        output_rule = OUTPUT_DIR / "rule_summaries.csv"
        save_summaries_to_csv(rule_summaries, output_rule, "Rule-Based")

        logger.info("Offline summary generation completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error during summary generation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
