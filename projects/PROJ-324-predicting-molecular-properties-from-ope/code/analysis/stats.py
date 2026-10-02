import os
import sys
import json
import logging
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from scipy.stats import ttest_rel, wilcoxon
import warnings
warnings.filterwarnings('ignore')

# --- Logging Setup ---
def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Configure logging for the stats module."""
    logger = logging.getLogger('stats')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, mode='a')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    return logger

# --- Directory Management ---
def ensure_dirs() -> None:
    """Ensure all required output directories exist."""
    dirs = [
        'data/derived',
        'data/raw',
        'data/processed',
        'data/models',
        'logs',
        'figures'
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

# --- Data Loading ---
def load_metadata() -> Dict[str, Any]:
    """Load dataset metadata from T031."""
    metadata_path = Path('data/raw/dataset_metadata.json')
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found at {metadata_path}. Run T031 first.")
    with open(metadata_path, 'r') as f:
        return json.load(f)

def load_test_set() -> pd.DataFrame:
    """Load the held-out test set from T011.5."""
    test_path = Path('data/derived/test_set.csv')
    if not test_path.exists():
        raise FileNotFoundError(f"Test set file not found at {test_path}. Run T011.5 first.")
    return pd.read_csv(test_path)

def load_baseline_predictions() -> pd.DataFrame:
    """Load baseline predictions from T014.5."""
    pred_path = Path('data/derived/baseline_test_predictions.csv')
    if not pred_path.exists():
        raise FileNotFoundError(f"Baseline predictions not found at {pred_path}. Run T014.5 first.")
    return pd.read_csv(pred_path)

def load_rf_predictions() -> pd.DataFrame:
    """Load RF predictions from T020.1."""
    pred_path = Path('data/derived/rf_test_predictions.csv')
    if not pred_path.exists():
        raise FileNotFoundError(f"RF predictions not found at {pred_path}. Run T020.1 first.")
    return pd.read_csv(pred_path)

def load_raw_data() -> pd.DataFrame:
    """Load raw data for validation audit."""
    raw_path = Path('data/raw/pubchem_raw.csv')
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data not found at {raw_path}. Run T008 first.")
    return pd.read_csv(raw_path)

# --- Core Analysis Functions ---

def generate_validation_audit() -> str:
    """
    Generate the Experimental Validation Protocol document (T058).
    
    This function:
    1. Loads metadata to identify experimental sources and uncertainty status.
    2. Loads the test set to map specific molecules to their data points.
    3. Compiles a rigorous protocol document detailing measurement conditions,
       uncertainty status, and validation procedures.
    """
    logger = setup_logging('logs/stats.log')
    logger.info("Generating Experimental Validation Protocol (T058)...")
    
    # 1. Load Metadata
    metadata = load_metadata()
    logger.info(f"Loaded metadata from data/raw/dataset_metadata.json")
    
    # 2. Load Test Set
    test_set = load_test_set()
    logger.info(f"Loaded test set with {len(test_set)} molecules")
    
    # 3. Load Baseline and RF predictions to cross-reference
    baseline_preds = load_baseline_predictions()
    rf_preds = load_rf_predictions()
    
    # 4. Compile the Protocol Document
    protocol_content = []
    protocol_content.append("# Experimental Validation Protocol")
    protocol_content.append("\n## 1. Data Provenance and Source Information")
    protocol_content.append(f"\n**Source System**: {metadata.get('source', 'Unknown')}")
    protocol_content.append(f"**Query Parameters**: {json.dumps(metadata.get('query_parameters', {}), indent=2)}")
    protocol_content.append(f"\n**Experimental Ratio**: {metadata.get('experimental_ratio', 'N/A'):.2%}")
    
    protocol_content.append("\n## 2. Measurement Uncertainty and Quantity of Substance")
    uncertainty_status = metadata.get('measurement_uncertainty_status', 'Not Available in Source')
    quantity_status = metadata.get('quantity_of_substance_status', 'Not Available in Source')
    
    protocol_content.append(f"\n**Measurement Uncertainty Status**: {uncertainty_status}")
    if uncertainty_status == "Not Available in Source":
        protocol_content.append("  - *Note*: The source (PubChem) did not provide explicit measurement uncertainty values for the fetched properties.")
        protocol_content.append("  - *Protocol Implication*: Statistical analysis assumes uniform variance; heteroscedasticity is not modeled.")
    
    protocol_content.append(f"\n**Quantity of Substance Status**: {quantity_status}")
    if quantity_status == "Not Available in Source":
        protocol_content.append("  - *Note*: The source did not provide explicit quantity of substance (e.g., moles, mass) for the measurements.")
        protocol_content.append("  - *Protocol Implication*: Properties are treated as intensive; concentration effects are not explicitly controlled.")
    
    protocol_content.append("\n## 3. Validation Procedure")
    protocol_content.append("\nThe following procedure is used to validate model predictions against the held-out experimental data:")
    protocol_content.append("\n### 3.1. Dataset Integrity Check")
    protocol_content.append("- Verify that the test set (`data/derived/test_set.csv`) contains unique SMILES strings.")
    protocol_content.append("- Confirm that all molecules in the test set have corresponding entries in `data/derived/baseline_test_predictions.csv` and `data/derived/rf_test_predictions.csv`.")
    
    protocol_content.append("\n### 3.2. Prediction Comparison")
    protocol_content.append("- For each molecule in the test set:")
    protocol_content.append("  1. Retrieve the experimental value (`experimental_value`).")
    protocol_content.append("  2. Retrieve the Crippen baseline prediction (`predicted_value` from baseline).")
    protocol_content.append("  3. Retrieve the Random Forest prediction (`predicted_value` from RF).")
    protocol_content.append("  4. Calculate residuals: `residual = experimental_value - predicted_value`.")
    protocol_content.append("  5. Calculate absolute errors: `AE = |residual|`.")
    
    protocol_content.append("\n### 3.3. Statistical Significance Testing")
    protocol_content.append("- Perform a paired Wilcoxon signed-rank test on the absolute errors of the baseline vs. RF models.")
    protocol_content.append("- **Null Hypothesis (H0)**: There is no difference in the median absolute error between the baseline and RF models.")
    protocol_content.append("- **Alternative Hypothesis (H1)**: The RF model has a significantly lower median absolute error than the baseline.")
    protocol_content.append("- **Significance Level (α)**: 0.05")
    
    protocol_content.append("\n### 3.4. Reproducibility under Physical Conditions")
    protocol_content.append("- The validation assumes that the experimental conditions (temperature, pH) reported in the source metadata are consistent across the dataset.")
    protocol_content.append("- Since specific conditions (e.g., exact temperature) are often missing in aggregated datasets, the protocol treats the experimental values as the ground truth for the *reported* conditions.")
    protocol_content.append("- If `experimental_ratio < 0.5`, the analysis falls back to comparing RF vs. Baseline on computed data only (see T021.2).")
    
    protocol_content.append("\n## 4. Test Set Molecule Details")
    protocol_content.append("\n| SMILES | Property | Experimental Value | Baseline Pred | RF Pred | Baseline AE | RF AE |")
    protocol_content.append("|---|---|---|---|---|---|---|")
    
    # Merge data for the table
    merged = test_set.merge(baseline_preds, on=['smiles', 'property_name'], suffixes=('_test', '_base'))
    merged = merged.merge(rf_preds[['smiles', 'property_name', 'predicted_value']], on=['smiles', 'property_name'], suffixes=('', '_rf'))
    merged.columns = ['smiles', 'property_name', 'experimental_value', 'baseline_pred', 'rf_pred', 'residual_base', 'residual_rf']
    merged['baseline_ae'] = merged['residual_base'].abs()
    merged['rf_ae'] = merged['residual_rf'].abs()
    
    for _, row in merged.iterrows():
        protocol_content.append(
            f"| {row['smiles'][:20]}... | {row['property_name']} | {row['experimental_value']:.4f} | "
            f"{row['baseline_pred']:.4f} | {row['rf_pred']:.4f} | {row['baseline_ae']:.4f} | {row['rf_ae']:.4f} |"
        )
    
    protocol_content.append("\n## 5. Conclusion")
    protocol_content.append("\nThis protocol establishes a rigorous framework for validating the Random Forest model against the Crippen additive baseline.")
    protocol_content.append("By explicitly documenting the absence of measurement uncertainty and quantity of substance data, we ensure that claims of 'improvement' are framed as statistical correlations rather than physical discoveries.")
    protocol_content.append("The use of a held-out test set and paired statistical tests provides a robust measure of model performance relative to the additive baseline.")
    
    # Write to file
    output_path = Path('data/derived/experimental_validation_protocol.md')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(protocol_content))
    
    logger.info(f"Validation protocol written to {output_path}")
    return str(output_path)

def estimate_conformational_impact() -> pd.DataFrame:
    """
    Estimate conformational impact using topological proxies (NumRotatableBonds).
    Returns a DataFrame with molecules flagged for potential 3D failure.
    """
    logger = setup_logging('logs/stats.log')
    logger.info("Estimating conformational impact...")
    
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors
    except ImportError:
        logger.error("RDKit not available. Cannot estimate conformational impact.")
        return pd.DataFrame()
    
    test_set = load_test_set()
    results = []
    
    for _, row in test_set.iterrows():
        smiles = row['smiles']
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            rot_bonds = Descriptors.NumRotatableBonds(mol)
            # Flag if > 10 as per T033
            is_flexible = rot_bonds > 10
            results.append({
                'smiles': smiles,
                'num_rotatable_bonds': rot_bonds,
                'is_flexible': is_flexible,
                'property_name': row['property_name']
            })
    
    return pd.DataFrame(results)

def main():
    """Main entry point for T058."""
    try:
        ensure_dirs()
        protocol_path = generate_validation_audit()
        print(f"SUCCESS: Experimental Validation Protocol generated at {protocol_path}")
        
        # Also run the conformational impact check as part of the audit
        conformational_df = estimate_conformational_impact()
        if not conformational_df.empty:
            conformational_path = Path('data/derived/conformational_sensitivity_analysis.csv')
            conformational_df.to_csv(conformational_path, index=False)
            print(f"Conformational sensitivity analysis written to {conformational_path}")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error during validation protocol generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()