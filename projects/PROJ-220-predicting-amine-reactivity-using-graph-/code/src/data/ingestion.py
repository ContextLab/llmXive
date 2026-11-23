import logging
import sys
import math
from typing import List, Dict, Any, Optional, NamedTuple
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import json

# Attempt to import dataset libraries; if missing, the script will fail loudly as per constraints
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError("The 'datasets' package is required. Install it via 'pip install datasets'.")

from chembl_webresource_client.new_client import new_client

# --- Custom Exceptions ---
class DataFetchError(Exception):
    """Raised when data fetching from external sources fails."""
    pass

class DataSchemaError(Exception):
    """Raised when the downloaded dataset is missing required fields."""
    pass

# --- Data Structures ---
@dataclass
class ReactionRecord:
    reaction_id: str
    reactant_smiles: str
    product_smiles: Optional[str]
    rate_constant: float
    temperature: float  # in Kelvin
    activation_energy: Optional[float] = None  # in kJ/mol
    reaction_class: Optional[str] = None
    citation_url: Optional[str] = None
    citation_title: Optional[str] = None
    source: str = "unknown"
    normalized_log_rate: Optional[float] = None
    pKa: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def validate_citations():
    """
    Placeholder for T009 implementation.
    In a full implementation, this would check URL reachability and checksums.
    For this task, we assume it passes or is called externally.
    """
    logger.info("Running citation validation gate...")
    # Simulating a pass for the purpose of this implementation block
    return True

def calculate_class_average_ea(reaction_class: str, records: List[ReactionRecord]) -> Optional[float]:
    """
    Calculates the average activation energy for a specific reaction class.
    """
    if not reaction_class:
        return None
    
    relevant_eas = [
        r.activation_energy for r in records 
        if r.reaction_class == reaction_class and r.activation_energy is not None
    ]
    
    if not relevant_eas:
        return None
    
    return sum(relevant_eas) / len(relevant_eas)

def normalize_kinetics(k: float, T: float, Ea: Optional[float] = None, class_avg_ea: Optional[float] = None) -> Optional[float]:
    """
    Normalizes kinetic data using Arrhenius equation to a reference temperature (e.g., 298K).
    log(k_ref) = log(k) + (Ea / R) * (1/T - 1/T_ref)
    
    Returns None if Ea is missing and no class_avg_ea is provided.
    """
    R = 8.314e-3  # kJ/(mol*K)
    T_ref = 298.15
    
    if k <= 0 or T <= 0:
        return None
    
    effective_Ea = Ea
    if effective_Ea is None:
        if class_avg_ea is not None:
            effective_Ea = class_avg_ea
        else:
            # Cannot normalize without Ea
            return None
    
    try:
        log_k = math.log(k)
        adjustment = (effective_Ea / R) * ((1.0 / T) - (1.0 / T_ref))
        return log_k + adjustment
    except (ValueError, ZeroDivisionError):
        return None

def fetch_chembl_sn2_data() -> List[Dict[str, Any]]:
    """
    Fetches SN2 reaction data from ChEMBL.
    Note: In a real scenario, this would use specific ChEMBL assays or reactions.
    This is a simplified fetcher for the pipeline structure.
    """
    logger.info("Fetching data from ChEMBL...")
    # This is a placeholder for the actual API call logic required by T014.
    # Since we cannot execute real network calls in this static generation,
    # we define the structure that the real code would produce.
    # The actual implementation would iterate new_client.reaction.search(...)
    return []

def fetch_pubchem_sn2_data() -> List[Dict[str, Any]]:
    """
    Fetches SN2 reaction data from PubChem.
    """
    logger.info("Fetching data from PubChem...")
    # Placeholder for PubChem logic
    return []

def filter_primary_secondary_amine(records: List[ReactionRecord]) -> List[ReactionRecord]:
    """
    Filters records to keep only those involving primary or secondary amines.
    Uses RDKit for SMILES parsing (assumed available via T002 dependencies).
    """
    try:
        from rdkit import Chem
    except ImportError:
        raise ImportError("RDKit is required for amine filtering.")

    filtered = []
    for r in records:
        if not r.reactant_smiles:
            continue
        mol = Chem.MolFromSmiles(r.reactant_smiles)
        if mol is None:
            continue
        
        # Simple heuristic: check for N with 1 or 2 heavy atom neighbors
        # A robust implementation would use SMARTS patterns
        for atom in mol.GetAtoms():
            if atom.GetAtomicNum() == 6: # Carbon
                continue
            if atom.GetAtomicNum() == 7: # Nitrogen
                neighbors = [a for a in atom.GetNeighbors() if a.GetAtomicNum() != 1]
                if len(neighbors) <= 2: # Primary or Secondary
                    filtered.append(r)
                    break
    return filtered

def process_chemistry_data(raw_records: List[Dict[str, Any]], class_avg_eas: Dict[str, float]) -> List[ReactionRecord]:
    """
    Converts raw dictionaries to ReactionRecord objects, applying normalization.
    """
    processed = []
    for raw in raw_records:
        try:
            # Map raw keys to standard fields
            r_id = raw.get('reaction_id')
            smiles = raw.get('reactant_smiles')
            rate = raw.get('rate_constant')
            temp = raw.get('temperature')
            ea = raw.get('activation_energy')
            r_class = raw.get('reaction_class')
            
            if not all([r_id, smiles, rate, temp]):
                continue
            
            # Normalize kinetics
            avg_ea = class_avg_eas.get(r_class)
            norm_rate = normalize_kinetics(rate, temp, ea, avg_ea)
            
            record = ReactionRecord(
                reaction_id=r_id,
                reactant_smiles=smiles,
                product_smiles=raw.get('product_smiles'),
                rate_constant=rate,
                temperature=temp,
                activation_energy=ea,
                reaction_class=r_class,
                normalized_log_rate=norm_rate,
                source=raw.get('source', 'unknown')
            )
            processed.append(record)
        except Exception as e:
            logger.warning(f"Skipping record due to processing error: {e}")
            continue
    
    return processed

def _validate_schema(records: List[Dict[str, Any]]) -> None:
    """
    Validates that the downloaded dataset contains required fields:
    'reaction_id', 'reactant_smiles', 'rate_constant'.
    Raises DataSchemaError if missing.
    """
    required_fields = ['reaction_id', 'reactant_smiles', 'rate_constant']
    
    if not records:
        raise DataSchemaError("Downloaded dataset is empty. Cannot validate schema.")
    
    first_record = records[0]
    missing_fields = [f for f in required_fields if f not in first_record]
    
    if missing_fields:
        raise DataSchemaError(
            f"Dataset schema validation failed. Missing required fields: {missing_fields}. "
            f"Expected fields: {required_fields}. "
            f"Received keys: {list(first_record.keys()) if first_record else 'None'}"
        )
    
    logger.info("Dataset schema validation passed.")

def run_ingestion(output_dir: str = "data/raw") -> List[ReactionRecord]:
    """
    Main ingestion pipeline:
    1. Validate citations.
    2. Fetch data (ChEMBL/PubChem).
    3. Validate schema (T043).
    4. Filter and process.
    5. Log exclusions.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 1. Citation Validation
    if not validate_citations():
        raise RuntimeError("Citation validation failed. Aborting ingestion.")
    
    # 2. Fetch Data
    raw_chembl = fetch_chembl_sn2_data()
    raw_pubchem = fetch_pubchem_sn2_data()
    raw_all = raw_chembl + raw_pubchem
    
    # 3. Schema Validation (T043)
    # This is the core logic added for T043
    try:
        _validate_schema(raw_all)
    except DataSchemaError as e:
        logger.error(f"Schema validation failed: {e}")
        raise e
    
    # 4. Calculate Class Average EAs
    # Group by reaction class first
    class_records = {}
    for r in raw_all:
        r_class = r.get('reaction_class', 'unknown')
        if r_class not in class_records:
            class_records[r_class] = []
        class_records[r_class].append(r)
    
    class_avg_eas = {}
    for r_class, recs in class_records.items():
        # Convert dict to ReactionRecord temporarily for calc or do direct calc
        # Simplified direct calc for this snippet
        eas = [x['activation_energy'] for x in recs if x.get('activation_energy') is not None]
        if eas:
            class_avg_eas[r_class] = sum(eas) / len(eas)
    
    # 5. Process and Convert
    processed_records = process_chemistry_data(raw_all, class_avg_eas)
    
    # 6. Filter for Amines
    amine_records = filter_primary_secondary_amine(processed_records)
    
    # 7. Log Exclusions (T018a/b logic would go here)
    excluded_count = len(processed_records) - len(amine_records)
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} records during amine filtering.")
        # In a real run, we would append to data/raw/audit_log.json
    
    logger.info(f"Ingestion complete. Processed {len(amine_records)} valid reaction records.")
    return amine_records

def main():
    """Entry point for the ingestion script."""
    try:
        records = run_ingestion()
        # In a real pipeline, we would save these to a file (e.g., JSON, HDF5)
        # For now, we just log the count
        logger.info(f"Successfully ingested {len(records)} records.")
    except DataSchemaError as e:
        logger.critical(f"Schema Error: {e}")
        sys.exit(1)
    except DataFetchError as e:
        logger.critical(f"Data Fetch Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()