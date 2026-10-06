"""
Task T014a: Normalize Ingredients
Normalizes ingredient names and maps them to canonical IDs based on the ratified methodology.

Dependencies:
- T013a: Stream & Validate Recipe1M (provides raw ingredient list)
- T012d_ratification_gate: Provides amendment status
- T007b: Provides updated schema expectations

Output:
- data/processed/normalized_ingredients.csv
"""
import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from Levenshtein import distance as levenshtein_distance

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = DATA_DIR / "logs"

def load_amendment_log():
    """Load the amendment log to determine methodology."""
    path = DATA_DIR / "amendment_log.json"
    if not path.exists():
        raise FileNotFoundError(f"Amendment log not found at {path}. Run T012b first.")
    with open(path, 'r') as f:
        return json.load(f)

def load_raw_ingredients():
    """Load ingredients from the processed Recipe1M dataset (T013a output)."""
    # T013a outputs data/raw/recipe1m_processed.parquet
    input_path = DATA_DIR / "raw" / "recipe1m_processed.parquet"
    if not input_path.exists():
        # Fallback to raw if processed doesn't exist but raw does (depending on T013a specifics)
        input_path = DATA_DIR / "raw" / "recipe1m_raw.parquet"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Recipe1M dataset not found at {input_path}. Run T013a first.")
    
    logger.info(f"Loading ingredients from {input_path}")
    df = pd.read_parquet(input_path)
    
    # Identify the ingredient column. Usually 'ingredients' or 'ingredient_list'.
    # Assuming the stream_recipe1m task flattened this into a list or string.
    # If it's a list of strings, we need to explode. If it's a string, we parse.
    # Based on typical Recipe1M structures, 'ingredients' is often a list of dicts or strings.
    # Let's assume a column 'ingredient' exists or we derive it.
    # If the column is 'ingredients' (list), we explode.
    
    ingredient_col = None
    candidates = ['ingredient', 'ingredients', 'ingredient_name']
    for col in candidates:
        if col in df.columns:
            ingredient_col = col
            break
    
    if not ingredient_col:
        # Try to find any column with 'ing' in name
        matches = [c for c in df.columns if 'ing' in c.lower()]
        if matches:
            ingredient_col = matches[0]
        else:
            raise ValueError("Could not identify ingredient column in Recipe1M dataset.")
    
    logger.info(f"Found ingredient column: {ingredient_col}")
    
    if isinstance(df[ingredient_col].iloc[0], list):
        # Explode list of ingredients
        df_exploded = df.explode(ingredient_col).reset_index(drop=True)
        df_clean = df_exploded[[ingredient_col]].dropna().drop_duplicates()
        df_clean.columns = ['raw_ingredient']
    else:
        # Assume string, maybe comma separated or just single ingredient per row
        # If it's a single string per row, we might need to parse if multiple per row.
        # For Recipe1M, often it's one ingredient per row after explosion in T013a.
        df_clean = df[[ingredient_col]].dropna().drop_duplicates()
        df_clean.columns = ['raw_ingredient']
    
    # Clean whitespace
    df_clean['raw_ingredient'] = df_clean['raw_ingredient'].astype(str).str.strip().str.lower()
    df_clean = df_clean[df_clean['raw_ingredient'] != '']
    
    # Calculate marginal frequency for tie-breaking
    freq = df_clean['raw_ingredient'].value_counts().reset_index()
    freq.columns = ['raw_ingredient', 'frequency']
    
    return freq

def get_canonical_reference_list(methodology):
    """
    Load the canonical reference list based on methodology.
    - Correlational Analysis: Use Recipe1M's own high-frequency unique list as reference.
    - Causal Independence: Use FlavorDB (not implemented here as per T014a focus on Correlational path usually, but structure included).
    """
    if methodology == "Correlational Analysis":
        # For Correlational, we normalize within the Recipe1M corpus itself.
        # We load the raw ingredients, count frequencies, and treat the most frequent
        # spelling as the canonical form.
        return None # We derive on the fly
    
    elif methodology == "Causal Independence":
        # This would require loading FlavorDB canonical list.
        # Since T014a is often blocked by T016a in Causal path, and T012b usually fails Causal,
        # we assume Correlational for this implementation unless FlavorDB exists.
        flavor_db_path = DATA_DIR / "raw" / "flavordb_raw.csv"
        if flavor_db_path.exists():
            df = pd.read_csv(flavor_db_path)
            # Assume column 'ingredient' or 'name'
            col = 'ingredient' if 'ingredient' in df.columns else 'name'
            if col in df.columns:
                return df[col].str.lower().unique().tolist()
        else:
            logger.warning("FlavorDB not found. Falling back to Recipe1M internal normalization.")
            return None
    else:
        raise ValueError(f"Unknown methodology: {methodology}")

def normalize_ingredient(raw_name, canonical_map):
    """
    Normalize a raw ingredient name to its canonical ID.
    Uses Levenshtein distance <= 2.
    Ties broken by highest marginal frequency (handled in main logic).
    """
    raw_lower = raw_name.lower().strip()
    
    if raw_lower in canonical_map:
        return canonical_map[raw_lower]
    
    best_match = None
    best_dist = 3 # Threshold is 2
    
    for canonical, details in canonical_map.items():
        d = levenshtein_distance(raw_lower, canonical)
        if d <= 2 and d < best_dist:
            best_dist = d
            best_match = canonical
        elif d <= 2 and d == best_dist:
            # Tie-breaking: check frequency
            if details['frequency'] > canonical_map[best_match]['frequency']:
                best_match = canonical
    
    if best_match:
        return best_match
    return raw_lower # Return original if no match found within threshold

def main():
    logger.info("Starting T014a: Normalize Ingredients")
    
    # 1. Check Ratification
    amendment = load_amendment_log()
    if amendment.get('status') != 'RATIFIED':
        raise RuntimeError(f"Amendment log status is {amendment.get('status')}. Must be RATIFIED.")
    
    methodology = amendment.get('methodology')
    logger.info(f"Methodology: {methodology}")
    
    # 2. Load Raw Ingredients
    raw_freq_df = load_raw_ingredients()
    logger.info(f"Loaded {len(raw_freq_df)} unique raw ingredient strings.")
    
    # 3. Determine Canonical List
    # Strategy: For "Correlational Analysis", we normalize the raw list to itself.
    # We group by normalized form (Levenshtein match) and pick the most frequent as canonical.
    # This effectively creates the canonical list from the data.
    
    # Build a map of raw -> {frequency, original}
    raw_to_freq = dict(zip(raw_freq_df['raw_ingredient'], raw_freq_df['frequency']))
    
    # We need to cluster similar names.
    # Since N^2 comparison is expensive, we iterate and try to map to existing canonicals.
    # We sort by frequency descending so high frequency items become canonicals first.
    sorted_raw = sorted(raw_to_freq.keys(), key=lambda x: raw_to_freq[x], reverse=True)
    
    canonical_map = {} # canonical_name -> {frequency, id}
    canonical_id_counter = 0
    
    # We will build a mapping: raw_name -> canonical_name
    raw_to_canonical = {}
    
    logger.info("Normalizing ingredients...")
    
    # To avoid O(N^2), we can use a simple heuristic:
    # If a high-freq item is close to a lower-freq item, map lower to higher.
    # We iterate from most frequent to least.
    
    for raw in sorted_raw:
        if raw in raw_to_canonical:
            continue # Already mapped as a lower-freq version of someone else
        
        # This 'raw' is the most frequent seen so far not yet mapped.
        # It becomes a new canonical.
        canonical_name = raw
        canonical_id = f"ING_{canonical_id_counter:05d}"
        canonical_id_counter += 1
        
        freq = raw_to_freq[raw]
        canonical_map[canonical_name] = {'id': canonical_id, 'frequency': freq}
        raw_to_canonical[raw] = canonical_name
        
        # Now try to map other unmapped raw ingredients to this new canonical
        # (Only if they are close enough)
        # Optimization: Only check against the last few added or all?
        # For correctness, we check all unmapped.
        # But to keep it fast, we can do a second pass or just accept O(N) per step if N is small (unique ingredients ~5k-10k).
        
        # Let's do a pass to find matches for this new canonical among remaining unmapped
        # We'll do this lazily in a final pass to save time, or just do it now if dataset is small.
        # Given constraints, let's assume unique ingredients < 20k. O(N^2) might be slow but acceptable for 300s?
        # Better: Just map the current 'raw' to itself and let a separate clustering step handle the rest?
        # No, the task says "map to canonical IDs".
        
    # Refined Approach:
    # 1. Sort all unique raw ingredients by frequency (desc).
    # 2. Iterate. If an ingredient is not yet assigned a canonical, it becomes a canonical.
    # 3. Check all *remaining* unassigned ingredients. If distance <= 2, assign them to this canonical.
    
    unassigned = set(sorted_raw)
    final_canonicals = []
    
    # We need a map from raw -> canonical_name
    raw_to_canonical_name = {}
    
    for candidate in sorted_raw:
        if candidate not in unassigned:
            continue
        
        # Candidate becomes canonical
        canonical_name = candidate
        freq = raw_to_freq[candidate]
        final_canonicals.append({
            'raw_ingredient': candidate,
            'canonical_name': canonical_name,
            'frequency': freq
        })
        
        # Mark self
        raw_to_canonical_name[candidate] = canonical_name
        unassigned.remove(candidate)
        
        # Try to match others
        # Optimization: Only check if distance is small? No, must check all.
        # To speed up, we can skip if unassigned is huge?
        # Let's just do it. If it's too slow, we might need a better algorithm, but for <50k unique it's okay.
        to_remove = []
        for other in list(unassigned):
            if levenshtein_distance(candidate, other) <= 2:
                raw_to_canonical_name[other] = canonical_name
                to_remove.append(other)
        
        for rem in to_remove:
            unassigned.remove(rem)
    
    logger.info(f"Normalized {len(final_canonicals)} unique canonical ingredients.")
    
    # 4. Construct Output DataFrame
    # Schema: {"ingredient_id": str, "canonical_name": str, "frequency": int}
    output_data = []
    for item in final_canonicals:
        # Generate ID based on frequency rank or just a counter
        # Let's use the counter we had earlier logic, but here we just need unique IDs.
        # The task doesn't specify ID format, just "canonical ID".
        # We'll use the index in final_canonicals as ID for now, or hash.
        # Let's use a simple counter ID.
        # Actually, we need to assign IDs to the final list.
        pass
    
    # Re-assign IDs to the final list
    df_output = pd.DataFrame(final_canonicals)
    df_output['ingredient_id'] = [f"ING_{i:05d}" for i in range(len(df_output))]
    df_output = df_output[['ingredient_id', 'canonical_name', 'frequency']]
    
    # 5. Save Output
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / "normalized_ingredients.csv"
    df_output.to_csv(output_path, index=False)
    
    logger.info(f"Saved normalized ingredients to {output_path}")
    
    # 6. Log completion
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_entry = {
        "task": "T014a",
        "status": "SUCCESS",
        "methodology": methodology,
        "unique_raw": len(raw_freq_df),
        "unique_canonical": len(df_output),
        "timestamp": pd.Timestamp.now().isoformat()
    }
    with open(LOGS_DIR / "normalize_ingredients_log.json", 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
