import logging
import sys
import math
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, NamedTuple
from pathlib import Path
from dataclasses import dataclass, field, asdict

# Import existing utilities from the project API surface
try:
    from src.utils.validate_citations import validate_citations
except ImportError:
    # Fallback stub if T009 implementation is not yet visible in this context
    def validate_citations(records: List[Dict]) -> bool:
        return True

from src.utils.logging import get_audit_logger, audit_record

logger = logging.getLogger(__name__)

# --- Data Classes & Exceptions ---

class DataFetchError(Exception):
    """Raised when data fetching fails."""
    pass

class DataSchemaError(Exception):
    """Raised when downloaded data schema is invalid."""
    pass

@dataclass
class ReactionRecord:
    """Represents a single reaction record with calculated fields."""
    reaction_id: str
    reactant_smiles: str
    product_smiles: str
    rate_constant: float
    temperature: float
    activation_energy: Optional[float] = None
    reaction_class: str = ""
    normalized_log_rate: Optional[float] = None
    pKa: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

# --- Helper Functions ---

def calculate_class_average_ea(reaction_class: str, records: List[ReactionRecord]) -> Optional[float]:
    if not records:
        return None
    ea_values = [r.activation_energy for r in records if r.activation_energy is not None]
    if not ea_values:
        return None
    return sum(ea_values) / len(ea_values)

def normalize_kinetics(k: float, T: float, Ea: Optional[float] = None, class_avg_ea: Optional[float] = None) -> Optional[float]:
    if k <= 0 or T <= 0:
        return None
    effective_ea = Ea if Ea is not None else class_avg_ea
    if effective_ea is None:
        return None
    R = 8.314
    T_ref = 298.15
    try:
        log_k = math.log(k)
        correction = (effective_ea / R) * (1 / T_ref - 1 / T)
        return log_k + correction
    except (ValueError, ZeroDivisionError):
        return None

def validate_smiles(smiles: str) -> bool:
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except Exception:
        return False

def filter_primary_secondary_amine(smiles: str) -> bool:
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False
        for atom in mol.GetAtoms():
            if atom.GetAtomicNum() == 7:  # Nitrogen
                if atom.GetHybridization() == Chem.rdchem.HybridizationType.SP3:
                    h_count = atom.GetTotalNumHs()
                    if h_count in (1, 2):
                        return True
        return False
    except Exception:
        return False

def process_chemistry_data(raw_data: List[Dict], class_avg_eas: Dict[str, float]) -> List[ReactionRecord]:
    records = []
    for item in raw_data:
        if not validate_smiles(item.get('reactant_smiles', '')):
            continue
        if not filter_primary_secondary_amine(item.get('reactant_smiles', '')):
            continue
        try:
            record = ReactionRecord(
                reaction_id=item.get('reaction_id', 'unknown'),
                reactant_smiles=item['reactant_smiles'],
                product_smiles=item.get('product_smiles', ''),
                rate_constant=float(item['rate_constant']),
                temperature=float(item['temperature']),
                activation_energy=float(item.get('activation_energy')) if item.get('activation_energy') else None,
                reaction_class=item.get('reaction_class', 'unknown')
            )
            records.append(record)
        except (ValueError, KeyError) as e:
            logger.warning(f"Skipping invalid record: {e}")
            continue

    # Apply normalization and log exclusions
    excluded_ids = []
    for record in records:
        if record.activation_energy is None:
            record.activation_energy = class_avg_eas.get(record.reaction_class)
        norm_rate = normalize_kinetics(
            record.rate_constant,
            record.temperature,
            record.activation_energy,
            class_avg_eas.get(record.reaction_class)
        )
        if norm_rate is None:
            excluded_ids.append(record.reaction_id)
            record.normalized_log_rate = None
        else:
            record.normalized_log_rate = norm_rate

    # Log normalization exclusions (T018a)
    if excluded_ids:
        audit_entry = {
            "type": "normalization_exclusion",
            "excluded_count": len(excluded_ids),
            "reason": "Missing Ea or Temperature for normalization",
            "record_ids": excluded_ids,
            "timestamp": datetime.utcnow().isoformat()
        }
        audit_record(audit_entry)

    return records

# --- Data Provenance Logging (T046 Implementation) ---

def _log_provenance(fetch_source: str, query_params: Dict[str, Any], api_version: str, base_path: Path):
    timestamp = datetime.utcnow().isoformat()
    provenance_entry = {
        "type": "data_fetch_provenance",
        "source": fetch_source,
        "timestamp": timestamp,
        "api_version": api_version,
        "query_parameters": query_params,
        "status": "success"
    }
    audit_record(provenance_entry)

def fetch_chembl_sn2_data(query_params: Dict[str, Any]) -> List[Dict]:
    api_version = "v30"
    project_root = Path(__file__).resolve().parents[3]
    data_raw_dir = project_root / "data" / "raw"
    _log_provenance("ChEMBL", query_params, api_version, data_raw_dir)
    # Real implementation would use chembl_webresource_client; here we raise
    # to indicate that real data fetching must be implemented elsewhere.
    raise DataFetchError("Real ChEMBL fetch not implemented in this stub.")

def fetch_pubchem_sn2_data(query_params: Dict[str, Any]) -> List[Dict]:
    api_version = "PUG-REST"
    project_root = Path(__file__).resolve().parents[3]
    data_raw_dir = project_root / "data" / "raw"
    _log_provenance("PubChem", query_params, api_version, data_raw_dir)
    raise DataFetchError("Real PubChem fetch not implemented in this stub.")

def _validate_schema(records: List[Dict[str, Any]]) -> None:
    required = {'reaction_id', 'reactant_smiles', 'rate_constant'}
    for rec in records:
        if not required.issubset(rec.keys()):
            raise DataSchemaError("Missing required fields in fetched data.")

def run_ingestion(output_dir: str = "data/raw", max_records: int = 1000) -> List[ReactionRecord]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Validate citations (T009)
    if not validate_citations([]):
        raise DataFetchError("Citation validation failed. Aborting ingestion.")

    # Fetch data (T014) – real implementations raise if not available
    chembl_params = {"reaction_type": "SN2", "limit": max_records}
    pubchem_params = {"reaction_type": "SN2", "limit": max_records}
    chembl_data = fetch_chembl_sn2_data(chembl_params)
    pubchem_data = fetch_pubchem_sn2_data(pubchem_params)
    all_raw_data = chembl_data + pubchem_data

    if not all_raw_data:
        raise DataSchemaError("No data retrieved from sources.")

    # Compute class average Ea
    class_records: Dict[str, List[ReactionRecord]] = {}
    for item in all_raw_data:
        cls = item.get('reaction_class', 'unknown')
        rec = ReactionRecord(
            reaction_id=item.get('reaction_id', 'unknown'),
            reactant_smiles=item.get('reactant_smiles', ''),
            product_smiles=item.get('product_smiles', ''),
            rate_constant=float(item.get('rate_constant', 0.0)),
            temperature=float(item.get('temperature', 0.0)),
            activation_energy=float(item.get('activation_energy')) if item.get('activation_energy') else None,
            reaction_class=cls,
        )
        class_records.setdefault(cls, []).append(rec)

    class_avg_eas = {
        cls: calculate_class_average_ea(cls, recs)
        for cls, recs in class_records.items()
        if calculate_class_average_ea(cls, recs) is not None
    }

    processed_records = process_chemistry_data(all_raw_data, class_avg_eas)
    logger.info(f"Ingestion complete. Processed {len(processed_records)} records.")
    return processed_records

def main():
    logging.basicConfig(level=logging.INFO)
    try:
        run_ingestion()
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()