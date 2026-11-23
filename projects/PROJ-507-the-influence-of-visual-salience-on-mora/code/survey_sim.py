"""
Survey Simulation Module for Pilot Data Validation (T026)

This module implements the generation of synthetic pilot data strictly for
pipeline validation and logic testing. It does NOT produce empirical data
for scientific claims.

Output: data/synth/pilot_responses_synth.csv
"""
import os
import sys
import json
import random
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Ensure project root is in path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import seed_everything
from models import SalienceLevel, ParticipantStatus
from logging_config import setup_logging

# Setup logger
logger = setup_logging("survey_sim")

class SurveyRandomizationError(Exception):
    """Custom exception for survey simulation errors."""
    pass

def load_scenarios(scenarios_path: Path) -> List[Dict[str, Any]]:
    """
    Load validated scenarios from the processed data directory.
    
    Args:
        scenarios_path: Path to validated_scenarios.csv or similar.
        
    Returns:
        List of scenario dictionaries.
        
    Raises:
        SurveyRandomizationError: If file not found or empty.
    """
    if not scenarios_path.exists():
        # For simulation purposes, if no real scenarios exist, we must fail loudly
        # or use a minimal set if strictly for logic testing (but T026 expects real structure).
        # However, T026 is "pilot data simulation" for pipeline validation.
        # If T014/T015 ran, we should have valid_scenarios.csv.
        # If not, we raise an error as per "Fail Loudly" principle for real data dependencies.
        # But since this is a *simulation* script for *logic* testing, we might need a fallback
        # ONLY IF the task explicitly allows a minimal mock for the *structure* check.
        # Given the strict "Real Data Only" constraint for the project, we assume T014/T015
        # produced data. If not, we raise.
        # However, for T026 specifically (simulation for validation), we might need to generate
        # a minimal set of "mock" scenarios IF the real ones are missing to test the *simulation logic*.
        # Let's check if the file exists. If not, we raise an error to force the user to run US1 first.
        raise SurveyRandomizationError(
            f"Scenarios file not found at {scenarios_path}. "
            "Please ensure T014/T015 have been completed to generate valid scenarios."
        )
    
    import pandas as pd
    df = pd.read_csv(scenarios_path)
    if df.empty:
        raise SurveyRandomizationError(f"No scenarios found in {scenarios_path}")
    
    return df.to_dict('records')

def load_stimulus_variants(variants_path: Path) -> List[Dict[str, Any]]:
    """
    Load stimulus variants (salience manipulations) from the processed data.
    
    Args:
        variants_path: Path to stimulus_variants.csv.
        
    Returns:
        List of variant dictionaries.
    """
    if not variants_path.exists():
        raise SurveyRandomizationError(
            f"Stimulus variants file not found at {variants_path}. "
            "Please ensure T016/T017 have been completed."
        )
    
    import pandas as pd
    df = pd.read_csv(variants_path)
    if df.empty:
        raise SurveyRandomizationError(f"No stimulus variants found in {variants_path}")
    
    return df.to_dict('records')

def build_variant_map(variants: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Build a mapping from scenario_id to list of stimulus variants.
    
    Args:
        variants: List of variant dictionaries.
        
    Returns:
        Dictionary mapping scenario_id to list of variants.
    """
    variant_map = {}
    for v in variants:
        sid = v.get('scenario_id')
        if not sid:
            continue
        if sid not in variant_map:
            variant_map[sid] = []
        variant_map[sid].append(v)
    return variant_map

def generate_latin_square_order(scenario_ids: List[str], n_levels: int = 3) -> List[List[str]]:
    """
    Generate a Latin Square design for within-subject randomization.
    
    Args:
        scenario_ids: List of scenario IDs to assign.
        n_levels: Number of salience levels (default 3: low, medium, high).
        
    Returns:
        List of lists, where each inner list is a permutation of scenario_ids
        representing the order for a specific condition/sequence.
    """
    if len(scenario_ids) % n_levels != 0:
        # Pad or truncate to make it divisible for Latin Square
        # For simplicity in simulation, we truncate to the nearest multiple
        logger.warning(f"Scenario count {len(scenario_ids)} not divisible by {n_levels}. Truncating.")
        scenario_ids = scenario_ids[:len(scenario_ids) // n_levels * n_levels]
    
    n_scenarios = len(scenario_ids)
    n_sequences = n_scenarios // n_levels
    
    # Generate base sequence
    base = scenario_ids[:n_sequences]
    
    # Generate Latin Square permutations
    # Each row is a shift of the previous
    sequences = []
    for i in range(n_sequences):
        # Shift base by i
        shifted = base[i:] + base[:i]
        # Repeat for all levels if needed, but here we assume 1 scenario per level per participant
        # Actually, in a full Latin Square for N scenarios and N levels, we have N rows.
        # Here we have N_scenarios total, and we want to assign each scenario to each level once across participants.
        # Simplified approach for simulation:
        # We will create N_sequences participants, each seeing a subset of scenarios.
        # This is a simplified Latin Square for the pilot.
        sequences.append(shifted)
        
    return sequences

def create_participant_sequences(
    scenarios: List[Dict[str, Any]],
    variants_map: Dict[str, List[Dict[str, Any]]],
    n_participants: int,
    seed: int
) -> List[Dict[str, Any]]:
    """
    Create survey sequences for multiple participants with within-subject constraints.
    
    Args:
        scenarios: List of scenario dictionaries.
        variants_map: Map of scenario_id to variants.
        n_participants: Number of simulated participants.
        seed: Random seed for reproducibility.
        
    Returns:
        List of survey sequence dictionaries.
    """
    seed_everything(seed)
    sequences = []
    
    scenario_ids = [s['id'] for s in scenarios]
    if not scenario_ids:
        raise SurveyRandomizationError("No scenario IDs available for sequencing.")
    
    # Get unique salience levels from variants
    salience_levels = set()
    for variants in variants_map.values():
        for v in variants:
            salience_levels.add(v.get('salience_level'))
    
    if not salience_levels:
        raise SurveyRandomizationError("No salience levels found in variants.")
    
    salience_levels = sorted(list(salience_levels))
    n_levels = len(salience_levels)
    
    # Generate Latin Square orders
    # We need enough orders to cover participants
    # Simplified: Cycle through permutations
    base_scenarios = scenario_ids[:len(scenario_ids)//n_levels * n_levels] # Ensure divisible
    if not base_scenarios:
        base_scenarios = scenario_ids[:n_levels] # Fallback to first N
        
    latin_square = generate_latin_square_order(base_scenarios, n_levels)
    
    for p_idx in range(n_participants):
        participant_id = f"P{p_idx:04d}"
        
        # Determine which sequence this participant gets
        # Cycle through the Latin Square rows
        sequence_idx = p_idx % len(latin_square) if latin_square else 0
        
        if sequence_idx >= len(latin_square):
            # Fallback if not enough sequences
            sequence_idx = 0
            
        assigned_scenario_ids = latin_square[sequence_idx]
        
        # For each scenario, pick a random salience level (ensuring within-subject balance)
        # In a true Latin Square, each scenario appears exactly once per level across participants.
        # Here, we simulate the assignment.
        
        survey_items = []
        for idx, sid in enumerate(assigned_scenario_ids):
            if sid not in variants_map or not variants_map[sid]:
                continue
            
            # Pick a salience level. To ensure balance, we can rotate based on participant index.
            # Simple rotation: (p_idx + idx) % n_levels
            level_idx = (p_idx + idx) % n_levels
            salience = salience_levels[level_idx]
            
            # Find the specific variant for this scenario and salience
            variant = None
            for v in variants_map[sid]:
                if v.get('salience_level') == salience:
                    variant = v
                    break
            
            if variant:
                survey_items.append({
                    "participant_id": participant_id,
                    "scenario_id": sid,
                    "stimulus_id": variant.get('id'),
                    "salience_level": salience,
                    "order": idx
                })
        
        sequences.append({
            "participant_id": participant_id,
            "sequence": survey_items
        })
    
    return sequences

def generate_synthetic_responses(sequences: List[Dict[str, Any]], seed: int) -> List[Dict[str, Any]]:
    """
    Generate synthetic blame ratings for the sequences.
    NOTE: These are synthetic and for pipeline validation ONLY.
    
    Args:
        sequences: List of survey sequences.
        seed: Random seed.
        
    Returns:
        List of response records.
    """
    seed_everything(seed + 1000) # Different seed for responses
    responses = []
    
    for seq in sequences:
        pid = seq["participant_id"]
        for item in seq["sequence"]:
            # Simulate a rating (1-5 ordinal scale)
            # Add some noise based on salience to simulate an effect for validation
            salience = item["salience_level"]
            base_rating = 3.0
            
            # Simple heuristic: higher salience -> slightly higher rating (just for testing logic)
            if salience == "high":
                base_rating += 0.5
            elif salience == "low":
                base_rating -= 0.3
            
            noise = random.gauss(0, 0.8)
            raw_rating = base_rating + noise
            rating = max(1, min(5, int(round(raw_rating))))
            
            responses.append({
                "participant_id": pid,
                "stimulus_id": item["stimulus_id"],
                "scenario_id": item["scenario_id"],
                "salience_level": item["salience_level"],
                "rating": rating,
                "timestamp": datetime.now().isoformat()
            })
    
    return responses

def save_responses(responses: List[Dict[str, Any]], output_path: Path):
    """
    Save synthetic responses to CSV.
    
    Args:
        responses: List of response dictionaries.
        output_path: Path to output CSV.
    """
    import pandas as pd
    df = pd.DataFrame(responses)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(responses)} synthetic responses to {output_path}")

def main():
    """
    Main entry point for T026: Pilot Data Simulation.
    """
    parser = argparse.ArgumentParser(description="Generate synthetic pilot data for pipeline validation.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--n-participants", type=int, default=20, help="Number of simulated participants")
    parser.add_argument("--scenarios-path", type=str, default="data/processed/valid_scenarios.csv",
                        help="Path to validated scenarios CSV")
    parser.add_argument("--variants-path", type=str, default="data/processed/stimulus_variants.csv",
                        help="Path to stimulus variants CSV")
    parser.add_argument("--output-dir", type=str, default="data/synth",
                        help="Output directory for synthetic data")
    
    args = parser.parse_args()
    
    seed_everything(args.seed)
    
    scenarios_path = Path(args.scenarios_path)
    variants_path = Path(args.variants_path)
    output_dir = Path(args.output_dir)
    output_file = output_dir / "pilot_responses_synth.csv"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info(f"Loading scenarios from {scenarios_path}")
        scenarios = load_scenarios(scenarios_path)
        
        logger.info(f"Loading stimulus variants from {variants_path}")
        variants = load_stimulus_variants(variants_path)
        
        variants_map = build_variant_map(variants)
        
        logger.info(f"Creating sequences for {args.n_participants} participants")
        sequences = create_participant_sequences(
            scenarios, variants_map, args.n_participants, args.seed
        )
        
        # Save sequences for reference (optional, but good for debugging)
        sequences_path = output_dir / "survey_sequences_synth.json"
        with open(sequences_path, 'w') as f:
            json.dump(sequences, f, indent=2)
        logger.info(f"Saved survey sequences to {sequences_path}")
        
        logger.info("Generating synthetic responses")
        responses = generate_synthetic_responses(sequences, args.seed)
        
        save_responses(responses, output_file)
        
        logger.info("T026 Simulation completed successfully.")
        
    except SurveyRandomizationError as e:
        logger.error(f"Survey Simulation Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during simulation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
