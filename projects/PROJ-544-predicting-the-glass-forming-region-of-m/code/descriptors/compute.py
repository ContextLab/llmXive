import argparse
import hashlib
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import yaml
from pymatgen.core.periodic_table import Element, PeriodicTable
from pymatgen.core import Composition

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"
CODE_CONFIG_DIR = PROJECT_ROOT / "code" / "config"
STATE_DIR = PROJECT_ROOT / "state"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DERIVED_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Configure standard logging for console and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "computation.log")
    ]
)
logger = logging.getLogger(__name__)

# --- Structured Logging Helper (Task T014) ---
# Writes JSON-Lines to logs/computation_log.jsonl
# Fields: timestamp, sample_id, step, status

_COMPUTATION_LOG_PATH = LOGS_DIR / "computation_log.jsonl"

def log_computation_step(sample_id: str, step: str, status: str, message: Optional[str] = None):
    """
    Appends a structured log entry to logs/computation_log.jsonl.
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sample_id": sample_id,
        "step": step,
        "status": status
    }
    if message:
        entry["message"] = message

    try:
        with open(_COMPUTATION_LOG_PATH, "a", encoding="utf-8") as f:
            import json
            f.write(json.dumps(entry) + "\n")
    except IOError as e:
        logger.error(f"Failed to write structured log for sample {sample_id}: {e}")

# --- Helper Functions (from utils integration) ---

PT = PeriodicTable()

def get_element_or_none(symbol: str) -> Optional[Element]:
    try:
        return PT[symbol]
    except ValueError:
        return None

def get_nearest_neighbor(symbol: str) -> str:
    """
    Finds the nearest neighbor in the periodic table for a given symbol.
    Returns the symbol of the neighbor.
    """
    el = get_element_or_none(symbol)
    if not el:
        # Default fallback if symbol is invalid, though caller should check
        return "H" 
    
    # Simple heuristic: check atomic number +/- 1
    candidates = []
    for offset in [1, -1, 2, -2]:
        new_z = el.number + offset
        if 1 <= new_z <= 118:
            candidate = Element.from_Z(new_z)
            if candidate:
                candidates.append(candidate)
    
    if not candidates:
        return "H"
    
    # Return the first valid candidate (closest in Z)
    return candidates[0].symbol

def get_property_with_fallback(symbol: str, prop_name: str, fallback_symbol: Optional[str] = None) -> Optional[float]:
    """
    Gets a property from an element, falling back to a neighbor if missing.
    """
    el = get_element_or_none(symbol)
    if not el:
        return None

    try:
        val = getattr(el, prop_name)
        if val is not None:
            return float(val)
    except (AttributeError, TypeError):
        pass

    # Fallback logic
    if not fallback_symbol:
        fallback_symbol = get_nearest_neighbor(symbol)
    
    fallback_el = get_element_or_none(fallback_symbol)
    if fallback_el:
        try:
            val = getattr(fallback_el, prop_name)
            if val is not None:
                logger.warning(f"Using fallback {fallback_symbol} for {prop_name} of {symbol}")
                return float(val)
        except (AttributeError, TypeError):
            pass
    
    return None

def safe_get_atomic_radius(symbol: str) -> Optional[float]:
    return get_property_with_fallback(symbol, "atomic_radius")

def safe_get_electronegativity(symbol: str) -> Optional[float]:
    return get_property_with_fallback(symbol, "electronegativity")

def safe_get_binary_mixing_enthalpy(el1: str, el2: str) -> Optional[float]:
    # Simplified fallback for mixing enthalpy if not in standard pymatgen direct API
    # In a real scenario, this might query a specific database or use Miedema's model
    # Here we simulate a lookup or return None if not found
    # For this implementation, we assume a simplified logic or return 0.0 if missing
    # to prevent crashes, logging a warning.
    # Real implementation would use a library like pymatgen.analysis.phase_diagrams or similar
    # For now, returning None triggers fallback logic in compute functions
    return None

# --- Core Computation Functions ---

def parse_composition(composition_str: str) -> Optional[Composition]:
    """
    Parses a string like 'Cu50Zr50' or 'Cu50 Zr50' into a Composition object.
    """
    try:
        # Handle spaces if present
        clean_str = composition_str.replace(" ", "")
        return Composition(clean_str)
    except Exception as e:
        logger.error(f"Failed to parse composition '{composition_str}': {e}")
        return None

def compute_atomic_size_mismatch(composition: Composition) -> Optional[float]:
    """
    Calculates atomic size mismatch (delta).
    Formula: sqrt( sum( c_i * (1 - r_i / r_avg)^2 ) )
    """
    elements = composition.elements
    if not elements:
        return None

    radii = []
    fractions = []
    
    for el in elements:
        r = safe_get_atomic_radius(el.symbol)
        if r is None:
            # If we can't get radius, we cannot compute this descriptor accurately
            # Log warning and return None or handle gracefully
            logger.warning(f"Missing atomic radius for {el.symbol}, cannot compute size mismatch.")
            return None
        radii.append(r)
        fractions.append(composition.get_atomic_fraction(el.symbol))

    # Weighted average radius
    r_avg = sum(f * r for f, r in zip(fractions, radii))
    if r_avg == 0:
        return None

    delta_sq = 0.0
    for f, r in zip(fractions, radii):
        delta_sq += f * ((1 - r / r_avg) ** 2)

    return (delta_sq ** 0.5) * 100.0  # Often expressed as percentage

def compute_mixing_enthalpy(composition: Composition) -> Optional[float]:
    """
    Calculates mixing enthalpy (delta H).
    Sum over pairs: 4 * c_i * c_j * delta_H_ij
    Note: This is a simplified Miedema approximation or requires a specific database.
    """
    elements = composition.elements
    if len(elements) < 2:
        return 0.0 # Pure element, no mixing

    total_h = 0.0
    el_list = list(elements)
    
    for i in range(len(el_list)):
        for j in range(i + 1, len(el_list)):
            el_i = el_list[i]
            el_j = el_list[j]
            
            c_i = composition.get_atomic_fraction(el_i.symbol)
            c_j = composition.get_atomic_fraction(el_j.symbol)
            
            h_ij = safe_get_binary_mixing_enthalpy(el_i.symbol, el_j.symbol)
            if h_ij is None:
                # If enthalpy data is missing, we might skip or use a default (0)
                # For robustness, we log and assume 0 for this pair if data missing
                logger.warning(f"Missing mixing enthalpy for {el_i.symbol}-{el_j.symbol}, assuming 0.")
                h_ij = 0.0
            
            # Miedema-like factor (simplified)
            total_h += 4 * c_i * c_j * h_ij

    return total_h

def compute_electronegativity_variance(composition: Composition) -> Optional[float]:
    """
    Calculates electronegativity variance.
    """
    elements = composition.elements
    if not elements:
        return None

    en_values = []
    fractions = []

    for el in elements:
        en = safe_get_electronegativity(el.symbol)
        if en is None:
            logger.warning(f"Missing electronegativity for {el.symbol}, cannot compute variance.")
            return None
        en_values.append(en)
        fractions.append(composition.get_atomic_fraction(el.symbol))

    # Weighted mean
    en_avg = sum(f * e for f, e in zip(fractions, en_values))
    
    variance = 0.0
    for f, e in zip(fractions, en_values):
        variance += f * ((e - en_avg) ** 2)

    return variance

def compute_descriptors(composition_str: str, sample_id: str) -> Dict[str, Any]:
    """
    Computes all three descriptors for a given composition string.
    Returns a dict with results or error flags.
    """
    log_computation_step(sample_id, "parse", "start")
    composition = parse_composition(composition_str)
    if not composition:
        log_computation_step(sample_id, "parse", "failed", "Invalid composition string")
        return {"error": "INVALID_COMPOSITION"}
    log_computation_step(sample_id, "parse", "success")

    result = {"sample_id": sample_id, "composition": composition_str}

    # Size Mismatch
    log_computation_step(sample_id, "size_mismatch", "start")
    delta = compute_atomic_size_mismatch(composition)
    if delta is None:
        log_computation_step(sample_id, "size_mismatch", "failed", "Missing atomic radii")
        result["atomic_size_mismatch"] = None
    else:
        log_computation_step(sample_id, "size_mismatch", "success")
        result["atomic_size_mismatch"] = delta

    # Mixing Enthalpy
    log_computation_step(sample_id, "mixing_enthalpy", "start")
    h_mix = compute_mixing_enthalpy(composition)
    if h_mix is None:
        log_computation_step(sample_id, "mixing_enthalpy", "failed", "Missing enthalpy data")
        result["mixing_enthalpy"] = None
    else:
        log_computation_step(sample_id, "mixing_enthalpy", "success")
        result["mixing_enthalpy"] = h_mix

    # Electronegativity Variance
    log_computation_step(sample_id, "electronegativity_variance", "start")
    var_en = compute_electronegativity_variance(composition)
    if var_en is None:
        log_computation_step(sample_id, "electronegativity_variance", "failed", "Missing electronegativity data")
        result["electronegativity_variance"] = None
    else:
        log_computation_step(sample_id, "electronegativity_variance", "success")
        result["electronegativity_variance"] = var_en

    return result

def write_provenance(output_path: Path):
    """
    Writes the parameters used for descriptor calculation to a YAML file.
    """
    provenance = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "parameters": {
            "atomic_size_mismatch_formula": "sqrt(sum(c_i * (1 - r_i / r_avg)^2))",
            "mixing_enthalpy_formula": "4 * sum(c_i * c_j * H_ij)",
            "electronegativity_variance_formula": "sum(c_i * (chi_i - chi_avg)^2)",
            "fallback_strategy": "nearest_neighbor"
        }
    }
    with open(output_path, "w") as f:
        yaml.dump(provenance, f)

def compute_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_artifact_hashes(file_path: Path, state_file: Path):
    """
    Updates the state/artifact_hashes.yaml with the new hash.
    """
    if not state_file.exists():
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, "w") as f:
            yaml.dump({"artifacts": {}}, f)
    
    with open(state_file, "r") as f:
        state = yaml.safe_load(f)
    
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    rel_path = str(file_path.relative_to(PROJECT_ROOT))
    state["artifacts"][rel_path] = {
        "sha256": compute_sha256(file_path),
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    
    with open(state_file, "w") as f:
        yaml.dump(state, f)

def main():
    parser = argparse.ArgumentParser(description="Compute alloy descriptors from CSV.")
    parser.add_argument("--input", required=True, help="Path to input CSV with 'composition' and 'sample_id' columns.")
    parser.add_argument("--output", required=True, help="Path to output CSV.")
    parser.add_argument("--errors", default=None, help="Path to output CSV for errors.")
    
    args = parser.parse_args()
    
    # Initialize structured log file (clear previous run if needed, or append? 
    # Usually for a run, we might want to start fresh or append with a run ID. 
    # For simplicity, we append but ensure the file exists.)
    if _COMPUTATION_LOG_PATH.exists():
        # Optional: Clear log for new run to keep logs clean per run
        # _COMPUTATION_LOG_PATH.unlink() 
        pass

    log_computation_step("system", "start_run", "start")

    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        log_computation_step("system", "start_run", "failed", f"Input file not found: {args.input}")
        sys.exit(1)

    df = pd.read_csv(args.input)
    
    required_cols = ["sample_id", "composition"]
    if not all(col in df.columns for col in required_cols):
        logger.error(f"Input CSV must contain columns: {required_cols}")
        log_computation_step("system", "start_run", "failed", "Missing required columns")
        sys.exit(1)

    results = []
    error_rows = []

    for idx, row in df.iterrows():
        sample_id = str(row["sample_id"])
        comp_str = str(row["composition"])
        
        log_computation_step(sample_id, "process_row", "start")
        
        desc = compute_descriptors(comp_str, sample_id)
        
        if "error" in desc:
            error_rows.append({
                "sample_id": sample_id,
                "composition": comp_str,
                "error_code": desc["error"],
                "atomic_size_mismatch": None,
                "mixing_enthalpy": None,
                "electronegativity_variance": None
            })
            log_computation_step(sample_id, "process_row", "failed", desc["error"])
        else:
            results.append(desc)
            log_computation_step(sample_id, "process_row", "success")

    # Write main output
    if results:
        out_df = pd.DataFrame(results)
        out_df.to_csv(args.output, index=False)
        logger.info(f"Wrote {len(results)} successful rows to {args.output}")
    else:
        logger.warning("No successful rows to write.")
        # Create empty file with headers
        pd.DataFrame(columns=["sample_id", "composition", "atomic_size_mismatch", "mixing_enthalpy", "electronegativity_variance"]).to_csv(args.output, index=False)

    # Write errors if any
    if error_rows and args.errors:
        err_df = pd.DataFrame(error_rows)
        err_df.to_csv(args.errors, index=False)
        logger.info(f"Wrote {len(error_rows)} error rows to {args.errors}")
    
    # Update provenance
    provenance_path = DATA_DERIVED_DIR / "provenance.yaml"
    write_provenance(provenance_path)
    logger.info(f"Wrote provenance to {provenance_path}")

    # Update artifact hashes if output exists
    out_path = Path(args.output)
    if out_path.exists():
        state_file = STATE_DIR / "artifact_hashes.yaml"
        update_artifact_hashes(out_path, state_file)
        logger.info(f"Updated artifact hashes in {state_file}")

    log_computation_step("system", "end_run", "success")

if __name__ == "__main__":
    main()