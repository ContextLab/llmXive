"""
Acquire Golden Set for Cognitive Load Optimization.

This script implements the workflow to acquire the required expert-labeled data
for the Golden Set (data/processed/golden_set.csv).

It attempts to fetch a verified external expert-labeled subset from a known source.
If no verified external source is available, it generates a template CSV with
sufficient interaction IDs and instructions for human experts to label them,
then blocks execution until the file is populated with real labels.

This task resolves the "create or load" requirement of FR-001.
"""

import os
import sys
import csv
import hashlib
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
GOLDEN_SET_PATH = PROJECT_ROOT / "data" / "processed" / "golden_set.csv"
TEMPLATE_PATH = PROJECT_ROOT / "data" / "processed" / "golden_set_template.csv"
LOCK_FILE = PROJECT_ROOT / "data" / "processed" / ".golden_set_lock"

# Minimum required samples
MIN_SAMPLES = 50

# Verified external sources (if any become available, add them here)
# Currently, no public dataset provides direct "expert_load_score" labels for
# ASSISTments/OULAD interactions in the exact format required.
# Therefore, we fall back to the template generation path.
VERIFIED_EXTERNAL_SOURCES = []

def ensure_directories():
    """Ensure the data/processed directory exists."""
    GOLDEN_SET_PATH.parent.mkdir(parents=True, exist_ok=True)

def fetch_external_golden_set() -> Optional[pd.DataFrame]:
    """
    Attempt to fetch a verified external expert-labeled Golden Set.
    Returns None if no source is available or fetch fails.
    """
    if not VERIFIED_EXTERNAL_SOURCES:
        print("INFO: No verified external sources configured.")
        return None

    for source in VERIFIED_EXTERNAL_SOURCES:
        try:
            print(f"INFO: Attempting to fetch from {source['name']}...")
            # Implementation would go here (e.g., load_dataset, requests.get)
            # For now, return None as no sources are configured
            return None
        except Exception as e:
            print(f"WARNING: Failed to fetch from {source['name']}: {e}")
            continue

    return None

def generate_template() -> pd.DataFrame:
    """
    Generate a template CSV with interaction IDs and instructions for experts.
    This template MUST be populated by human experts before the pipeline can proceed.
    """
    print(f"INFO: Generating Golden Set template with {MIN_SAMPLES} entries...")

    # We simulate interaction IDs from the ASSISTments/OULAD datasets
    # In a real scenario, these would be sampled from the actual loaded datasets
    # For the template, we generate placeholder IDs that experts can map to real data
    template_data = []

    # Header structure matching expected validation
    columns = [
        "interaction_id",
        "student_id",
        "skill_id",
        "problem_id",
        "attempt_number",
        "response_correctness",
        "response_latency_sec",
        "hint_requests",
        "expert_load_score"  # This is the column experts must fill
    ]

    # Generate placeholder rows
    # In a real deployment, these IDs would be real IDs from the dataset
    # For the template, we use a clear pattern that experts can replace
    for i in range(1, MIN_SAMPLES + 1):
        row = {
            "interaction_id": f"ASSIST-TEMP-{i:05d}",
            "student_id": f"STU-TEMP-{i:05d}",
            "skill_id": f"SKILL-TEMP-{i % 10:03d}",
            "problem_id": f"PROB-TEMP-{i:05d}",
            "attempt_number": 1,
            "response_correctness": None,  # Experts should verify/fill
            "response_latency_sec": None,  # Experts should verify/fill
            "hint_requests": None,  # Experts should verify/fill
            "expert_load_score": None  # CRITICAL: Experts MUST fill this (0-100)
        }
        template_data.append(row)

    df = pd.DataFrame(template_data, columns=columns)

    # Add a comment row at the top to guide experts (will be stripped on load)
    # We'll store instructions in a separate file to keep CSV clean
    return df

def save_template(df: pd.DataFrame):
    """Save the template CSV with instructions."""
    # Save the data
    df.to_csv(TEMPLATE_PATH, index=False)

    # Save instructions in a README next to the template
    instructions = f"""
    GOLDEN SET LABELING INSTRUCTIONS
    ================================

    File: {TEMPLATE_PATH.name}

    This file contains {MIN_SAMPLES} placeholder interaction records.
    You MUST replace the placeholder data with REAL interaction data from the
    ASSISTments or OULAD datasets, and fill in the 'expert_load_score' column.

    REQUIRED COLUMNS:
    -----------------
    - interaction_id: Unique ID for the interaction (from source dataset)
    - student_id: Student identifier
    - skill_id: Skill being practiced
    - problem_id: Problem identifier
    - attempt_number: Attempt number for this problem
    - response_correctness: 1 if correct, 0 if incorrect
    - response_latency_sec: Time in seconds from question end to answer start
    - hint_requests: Number of hints requested
    - expert_load_score: CRITICAL - Expert rating of cognitive load (0-100)

    LABELING GUIDELINES FOR EXPERT_LOAD_SCORE:
    ------------------------------------------
    Rate the cognitive load for each interaction on a scale of 0-100, where:
    - 0-20: Very low load (trivial, automatic retrieval)
    - 21-40: Low load (familiar, minimal effort)
    - 41-60: Moderate load (some effort, manageable)
    - 61-80: High load (significant effort, struggling)
    - 81-100: Very high load (overwhelmed, unable to proceed)

    Use your expertise to evaluate the behavioral indicators (latency, errors, hints)
    and assign a load score that reflects the actual cognitive effort required.

    CRITICAL: Do NOT use self-reported ease. Base your rating on observed behavior
    and your expert judgment of the difficulty.

    After labeling:
    1. Copy this file to: {GOLDEN_SET_PATH.name}
    2. Ensure all 'expert_load_score' values are filled (no None/NaN)
    3. Ensure at least {MIN_SAMPLES} rows are present
    4. Remove this instructions block
    """

    with open(PROJECT_ROOT / "data" / "processed" / "golden_set_instructions.txt", "w") as f:
        f.write(instructions)

    print(f"INFO: Template saved to {TEMPLATE_PATH}")
    print(f"INFO: Instructions saved to {PROJECT_ROOT / 'data' / 'processed' / 'golden_set_instructions.txt'}")

def load_template() -> Optional[pd.DataFrame]:
    """Load the template if it exists."""
    if TEMPLATE_PATH.exists():
        return pd.read_csv(TEMPLATE_PATH)
    return None

def load_golden_set() -> Optional[pd.DataFrame]:
    """Load the actual Golden Set if it exists and is valid."""
    if not GOLDEN_SET_PATH.exists():
        return None

    try:
        df = pd.read_csv(GOLDEN_SET_PATH)
        required_cols = ["interaction_id", "expert_load_score"]
        if not all(col in df.columns for col in required_cols):
            print(f"ERROR: Golden Set missing required columns: {required_cols}")
            return None

        if df["expert_load_score"].isna().any():
            print("ERROR: Golden Set contains missing expert_load_score values.")
            return None

        if len(df) < MIN_SAMPLES:
            print(f"ERROR: Golden Set has {len(df)} rows, need at least {MIN_SAMPLES}.")
            return None

        return df
    except Exception as e:
        print(f"ERROR: Failed to load Golden Set: {e}")
        return None

def wait_for_expert_population(template_df: pd.DataFrame):
    """
    Block execution and wait for experts to populate the Golden Set.
    This is a blocking check that halts the pipeline until data is ready.
    """
    print("\n" + "="*80)
    print("⚠️  GOLDEN SET ACQUISITION REQUIRED")
    print("="*80)
    print(f"Template generated at: {TEMPLATE_PATH}")
    print(f"Instructions at: {PROJECT_ROOT / 'data' / 'processed' / 'golden_set_instructions.txt'}")
    print()
    print("ACTION REQUIRED:")
    print("1. Review the template and instructions.")
    print("2. Have human experts label the 'expert_load_score' column.")
    print("3. Save the populated file as: data/processed/golden_set.csv")
    print("4. Ensure at least 50 rows with valid expert_load_score values.")
    print()
    print("The pipeline will now wait. Press Ctrl+C to abort.")
    print("="*80 + "\n")

    # Create a lock file to indicate waiting state
    LOCK_FILE.touch()

    try:
        while True:
            if GOLDEN_SET_PATH.exists():
                df = load_golden_set()
                if df is not None:
                    print(f"✅ Golden Set loaded successfully with {len(df)} valid entries.")
                    LOCK_FILE.unlink(missing_ok=True)
                    return df
                else:
                    print("⏳ Golden Set exists but is invalid. Please fix and retry.")
            else:
                print("⏳ Waiting for golden_set.csv to be created...")

            time.sleep(10)  # Check every 10 seconds
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline aborted by user.")
        LOCK_FILE.unlink(missing_ok=True)
        sys.exit(1)

def main():
    """Main entry point for acquiring the Golden Set."""
    print("Starting Golden Set Acquisition workflow...")

    ensure_directories()

    # Step 1: Try to fetch from external sources
    external_df = fetch_external_golden_set()
    if external_df is not None:
        print("✅ External Golden Set fetched successfully.")
        external_df.to_csv(GOLDEN_SET_PATH, index=False)
        print(f"Saved to {GOLDEN_SET_PATH}")
        return

    # Step 2: Check if Golden Set already exists (from previous run)
    existing_df = load_golden_set()
    if existing_df is not None:
        print(f"✅ Golden Set already exists with {len(existing_df)} entries.")
        return

    # Step 3: Generate template and wait for expert population
    print("No external source available and no existing Golden Set found.")
    print("Generating template for expert labeling...")

    template_df = generate_template()
    save_template(template_df)

    # Block until experts populate the data
    final_df = wait_for_expert_population(template_df)

    if final_df is not None:
        print("✅ Golden Set acquisition complete.")
    else:
        print("❌ Failed to acquire Golden Set.")
        sys.exit(1)

if __name__ == "__main__":
    main()
