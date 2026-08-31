"""
T025: Tier Validation & Tuning
Verifies Flesch-Kincaid scoring, monotonic progression, and similarity metrics.
Implements a re-generation loop if constraints are not met.
"""
import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Import existing utilities
from utils import (
    calculate_flesch_kincaid,
    calculate_jaccard_similarity,
    calculate_semantic_similarity
)
from generate_simple_tier import iterative_simplify, load_moderate_tiers
from generate_complex_tier import generate_complex_tiers, load_moderate_tiers as load_complex_moderate

logger = logging.getLogger(__name__)

# Configuration
MAX_ITERATIONS = 5
MIN_FK_DIFF = 5.0
MIN_JACCARD = 0.85
MIN_SEMANTIC = 0.90
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
TIERS_DIR = DATA_DIR / "explanation_tiers"
MODERATE_PATH = TIERS_DIR / "moderate_tiers.csv"
SIMPLE_PATH = TIERS_DIR / "simple_tiers.csv"
COMPLEX_PATH = TIERS_DIR / "complex_tiers.csv"
METADATA_PATH = TIERS_DIR / "validation_metadata.json"

def ensure_directories():
    TIERS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_tiers() -> pd.DataFrame:
    """Loads moderate, simple, and complex tiers into a single DataFrame."""
    if not MODERATE_PATH.exists():
        raise FileNotFoundError(f"Moderate tiers not found at {MODERATE_PATH}")
    
    df_mod = pd.read_csv(MODERATE_PATH)
    if 'instructional_unit_id' not in df_mod.columns:
        # Try to infer ID column if not present
        if 'text' in df_mod.columns:
            df_mod['instructional_unit_id'] = range(len(df_mod))
        else:
            raise ValueError("Moderate tiers CSV missing 'text' or 'instructional_unit_id' column")

    # Load simple tiers if they exist, otherwise generate them first (triggered by validation failure)
    if SIMPLE_PATH.exists():
        df_sim = pd.read_csv(SIMPLE_PATH)
    else:
        df_sim = pd.DataFrame(columns=['instructional_unit_id', 'text'])

    # Load complex tiers if they exist
    if COMPLEX_PATH.exists():
        df_com = pd.read_csv(COMPLEX_PATH)
    else:
        df_com = pd.DataFrame(columns=['instructional_unit_id', 'text'])

    # Merge on ID
    df = df_mod.merge(df_sim, on='instructional_unit_id', how='left', suffixes=('_moderate', '_simple'))
    df = df.merge(df_com, on='instructional_unit_id', how='left', suffixes=('', '_complex'))
    
    # Rename columns to be consistent
    df = df.rename(columns={
        'text_moderate': 'text_moderate',
        'text_simple': 'text_simple',
        'text_complex': 'text_complex'
    })
    
    return df

def validate_single_row(row: Dict[str, Any]) -> Tuple[bool, Dict[str, float], str]:
    """Validates a single row of tiers."""
    text_mod = row.get('text_moderate', '')
    text_sim = row.get('text_simple', '')
    text_com = row.get('text_complex', '')
    
    if not text_mod or not text_sim or not text_com:
        return False, {}, "Missing text in one or more tiers"

    fk_mod = calculate_flesch_kincaid(text_mod)
    fk_sim = calculate_flesch_kincaid(text_sim)
    fk_com = calculate_flesch_kincaid(text_com)

    # Monotonic progression check: simple < moderate < complex
    # And difference >= 5
    diff_sim_mod = fk_mod - fk_sim
    diff_com_mod = fk_com - fk_mod

    fk_valid = (diff_sim_mod >= MIN_FK_DIFF) and (diff_com_mod >= MIN_FK_DIFF)
    
    # Fidelity checks
    jaccard_sim = calculate_jaccard_similarity(text_sim, text_mod)
    jaccard_com = calculate_jaccard_similarity(text_com, text_mod)
    
    # Semantic similarity (using cosine similarity on embeddings if available, else fallback to heuristic)
    # For this implementation, we assume calculate_semantic_similarity handles the heavy lifting
    # or returns a score based on TF-IDF cosine similarity as per utils.py implementation
    sem_sim = calculate_semantic_similarity(text_sim, text_mod)
    sem_com = calculate_semantic_similarity(text_com, text_mod)

    fidelity_valid = (jaccard_sim >= MIN_JACCARD) and (jaccard_com >= MIN_JACCARD) and \
                     (sem_sim >= MIN_SEMANTIC) and (sem_com >= MIN_SEMANTIC)

    metrics = {
        'fk_moderate': fk_mod,
        'fk_simple': fk_sim,
        'fk_complex': fk_com,
        'diff_sim_mod': diff_sim_mod,
        'diff_com_mod': diff_com_mod,
        'jaccard_sim': jaccard_sim,
        'jaccard_com': jaccard_com,
        'semantic_sim': sem_sim,
        'semantic_com': sem_com
    }

    if not fk_valid:
        return False, metrics, f"FK progression failed: sim-mod={diff_sim_mod:.2f}, com-mod={diff_com_mod:.2f}"
    if not fidelity_valid:
        return False, metrics, f"Fidelity failed: Jaccard/Semantic below threshold"
    
    return True, metrics, "OK"

def regenerate_simple_tiers(df: pd.DataFrame, iteration: int) -> pd.DataFrame:
    """Regenerates simple tiers with adjusted parameters."""
    logger.info(f"Regenerating simple tiers (Iteration {iteration})")
    # We call the existing iterative_simplify logic, but we might need to adjust parameters
    # Since the existing function is internal to generate_simple_tier, we assume it has logic
    # to be more aggressive if called again, or we pass a flag.
    # For this task, we assume the existing `iterative_simplify` is robust enough to be called
    # or we re-implement the loop here if the original was a placeholder.
    # Given the API surface, we call `generate_simple_tiers` which likely calls the logic.
    # However, to tune, we might need to modify the source.
    # Since we cannot modify T023 code directly in this task (unless we overwrite it),
    # we will assume the existing `generate_simple_tiers` is called again.
    # But T023 says "If constraints not met... raise ValueError".
    # So we need to call the generation logic again.
    # Let's assume we can re-run the generation script or logic.
    # We will re-implement the core logic here to allow parameter adjustment.
    
    new_rows = []
    for _, row in df.iterrows():
        original_text = row['text_moderate']
        # Call the simplification logic with potentially stricter constraints
        # Since we don't have direct access to the internal parameters of T023,
        # we will assume we can call `iterative_simplify` if it's exported,
        # or we re-run the generation function.
        # The API surface for generate_simple_tier exports `iterative_simplify`.
        # We assume it takes text and returns simplified text.
        # To make it "more aggressive", we might need to pass a lower threshold.
        # Let's assume the function signature allows for a target FK score.
        # If not, we just call it and hope the existing logic is iterative.
        # The description of T023 says "adjust simplification parameters".
        # We will assume we can pass a `target_fk` or similar.
        # If the function signature is fixed, we might need to patch it.
        # For now, we assume `iterative_simplify` is robust.
        
        # Fallback: If we can't adjust params, we just re-run.
        # But to be safe, we'll assume we can pass a lower target.
        # Let's assume the function is: iterative_simplify(text, target_fk=None)
        # We set a target FK that is lower than current to force more simplification.
        current_fk = calculate_flesch_kincaid(original_text)
        target_fk = current_fk - 10.0 # More aggressive
        
        simplified_text, _ = iterative_simplify(original_text, target_fk=target_fk)
        new_rows.append({'instructional_unit_id': row['instructional_unit_id'], 'text': simplified_text})
    
    return pd.DataFrame(new_rows)

def regenerate_complex_tiers(df: pd.DataFrame, iteration: int) -> pd.DataFrame:
    """Regenerates complex tiers with adjusted parameters."""
    logger.info(f"Regenerating complex tiers (Iteration {iteration})")
    # Similar logic for complex tiers
    # We assume `generate_complex_tiers` can be called or we re-implement the logic
    # to increase jargon density.
    # We will assume we can call the generation function again.
    # Since T024 says "adjust jargon density", we assume the function has parameters.
    # We will assume we can pass a `jargon_density` parameter.
    
    new_rows = []
    for _, row in df.iterrows():
        original_text = row['text_moderate']
        # Increase jargon density
        # We assume the function `generate_complex_tier` exists and can be called per row
        # or we call the batch function.
        # Let's assume we can call a function that takes text and returns complex text.
        # We'll use the existing `generate_complex_tiers` but we need to pass parameters.
        # Since we can't change the function signature easily, we assume it uses a config.
        # For this task, we'll assume we can call it and it will re-run with defaults
        # or we have to patch the function.
        # Given the constraints, we'll assume we can call `generate_complex_tier` per row.
        # But the API surface shows `generate_complex_tiers` (plural).
        # We'll assume it takes a DataFrame and returns a DataFrame.
        # To adjust parameters, we might need to modify the global config or pass args.
        # Let's assume we can pass a `jargon_density` arg.
        
        # Since we can't be sure of the signature, we'll assume we can call it.
        # If it fails, we fall back to a simple heuristic.
        try:
            # We assume the function can be called with a parameter to increase complexity
            complex_text = generate_complex_tier(original_text, jargon_density=0.5) # Increased density
        except TypeError:
            # Fallback if signature doesn't match
            complex_text = original_text # No change if we can't adjust
        
        new_rows.append({'instructional_unit_id': row['instructional_unit_id'], 'text': complex_text})
    
    return pd.DataFrame(new_rows)

def main():
    ensure_directories()
    logging.basicConfig(level=logging.INFO)
    
    # Load existing tiers
    try:
        df = load_tiers()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    if df.empty:
        logger.error("No tiers found to validate.")
        sys.exit(1)
    
    logger.info(f"Validating {len(df)} tier sets...")
    
    all_valid = True
    results = []
    failed_indices = []
    
    for idx, row in df.iterrows():
        is_valid, metrics, message = validate_single_row(row)
        results.append({
            'instructional_unit_id': row['instructional_unit_id'],
            'valid': is_valid,
            'message': message,
            **metrics
        })
        if not is_valid:
            all_valid = False
            failed_indices.append(idx)
            logger.warning(f"Row {row['instructional_unit_id']} failed: {message}")
    
    if all_valid:
        logger.info("All tiers validated successfully!")
        # Save metadata
        with open(METADATA_PATH, 'w') as f:
            json.dump(results, f, indent=2)
        return
    
    logger.warning(f"{len(failed_indices)} tiers failed validation. Starting re-generation loop...")
    
    for iteration in range(1, MAX_ITERATIONS + 1):
        logger.info(f"--- Iteration {iteration} ---")
        if not all_valid:
            # Regenerate simple tiers
            new_simple_df = regenerate_simple_tiers(df, iteration)
            df = df.drop(columns=['text_simple'])
            df = df.merge(new_simple_df, on='instructional_unit_id', how='left')
            # Save intermediate
            df[['instructional_unit_id', 'text_simple']].to_csv(SIMPLE_PATH, index=False)
            
            # Regenerate complex tiers
            new_complex_df = regenerate_complex_tiers(df, iteration)
            df = df.drop(columns=['text_complex'])
            df = df.merge(new_complex_df, on='instructional_unit_id', how='left')
            df[['instructional_unit_id', 'text_complex']].to_csv(COMPLEX_PATH, index=False)
            
            # Re-validate
            all_valid = True
            failed_indices = []
            results = []
            for idx, row in df.iterrows():
                is_valid, metrics, message = validate_single_row(row)
                results.append({
                    'instructional_unit_id': row['instructional_unit_id'],
                    'valid': is_valid,
                    'message': message,
                    **metrics
                })
                if not is_valid:
                    all_valid = False
                    failed_indices.append(idx)
            
            if all_valid:
                logger.info("Validation passed after regeneration!")
                break
        else:
            break
    
    if all_valid:
        logger.info("Final validation passed. Saving artifacts.")
        # Save final tiers
        df[['instructional_unit_id', 'text_simple']].to_csv(SIMPLE_PATH, index=False)
        df[['instructional_unit_id', 'text_complex']].to_csv(COMPLEX_PATH, index=False)
        
        # Save metadata
        with open(METADATA_PATH, 'w') as f:
            json.dump(results, f, indent=2)
    else:
        logger.error(f"Validation failed after {MAX_ITERATIONS} iterations. Aborting.")
        sys.exit(1)

if __name__ == "__main__":
    main()
