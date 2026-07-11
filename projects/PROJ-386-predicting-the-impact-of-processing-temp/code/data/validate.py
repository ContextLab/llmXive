import os
import sys
import json
import logging
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

# Import config for paths
from config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Known chemical coupling pairs in aluminum alloys (common synergistic effects)
# Based on metallurgical knowledge: Mg-Si (Mg2Si formation), Cu-Mg (S-phase), Zn-Mg (η-phase), etc.
CHEMICAL_COUPLES = [
    ('Mg', 'Si'),
    ('Cu', 'Mg'),
    ('Zn', 'Mg'),
    ('Mn', 'Fe'),
    ('Cr', 'Mn'),
    ('Ti', 'B'),
    ('Fe', 'Si'),
]

def load_processed_data(input_path: str = None) -> pd.DataFrame:
    """
    Load the preprocessed dataset.
    If input_path is None, uses the default path from config.
    """
    config = get_config()
    if input_path is None:
        input_path = config.get('paths', {}).get('processed_data', 'data/processed/processed_data.csv')
    
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found at {input_path}. "
                                "Please run code/data/preprocess.py first.")
    
    logger.info(f"Loading processed data from {input_path}")
    return pd.read_csv(path)

def calculate_correlation_matrix(df: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    """
    Calculate the correlation matrix for a specific subset of features.
    """
    # Filter to only existing columns to avoid errors
    available_cols = [c for c in feature_cols if c in df.columns]
    if len(available_cols) < 2:
        logger.warning(f"Not enough features found in {available_cols} to calculate correlation.")
        return pd.DataFrame()
    
    corr_matrix = df[available_cols].corr()
    return corr_matrix

def detect_collinearity(corr_matrix: pd.DataFrame, threshold: float = 0.8) -> list:
    """
    Detect pairs of features with absolute correlation > threshold.
    Returns a list of dicts: [{'feature1': ..., 'feature2': ..., 'correlation': ...}, ...]
    """
    collinear_pairs = []
    features = corr_matrix.columns
    
    for i in range(len(features)):
        for j in range(i + 1, len(features)):
            f1 = features[i]
            f2 = features[j]
            corr_val = corr_matrix.loc[f1, f2]
            
            if abs(corr_val) > threshold:
                collinear_pairs.append({
                    'feature1': f1,
                    'feature2': f2,
                    'correlation': float(corr_val),
                    'abs_correlation': float(abs(corr_val))
                })
    
    return collinear_pairs

def identify_chemical_couplings(collinear_pairs: list) -> dict:
    """
    Classify collinear pairs as chemical couplings or non-chemical (process-driven) collinearity.
    
    Returns a dict with:
    - 'chemical': list of pairs identified as chemical couplings
    - 'non_chemical': list of pairs identified as non-chemical
    - 'descriptive_framing': human-readable summary
    """
    chemical_pairs = []
    non_chemical_pairs = []
    
    for pair in collinear_pairs:
        f1 = pair['feature1']
        f2 = pair['feature2']
        
        # Normalize feature names to extract base element (handle interactions like 'Temp_Mg')
        def extract_element(name):
            # Remove common prefixes/suffixes
            name = name.replace('Temp_', '').replace('Interaction_', '')
            # Check if it's a known element in our couples
            for couple in CHEMICAL_COUPLES:
                if f1.startswith(couple[0]) or f2.startswith(couple[0]):
                    return couple[0]
                if f1.startswith(couple[1]) or f2.startswith(couple[1]):
                    return couple[1]
            # Fallback: check if name contains element name
            for couple in CHEMICAL_COUPLES:
                if couple[0] in name and couple[1] in name:
                    return couple[0]
            return name
        
        # Check if this pair matches any known chemical coupling
        is_chemical = False
        for couple in CHEMICAL_COUPLES:
            # Check if both elements are present in the pair (case-insensitive, partial match)
            if (couple[0] in f1 and couple[1] in f2) or (couple[0] in f2 and couple[1] in f1):
                is_chemical = True
                break
            # Also check for interaction terms that combine both elements
            if couple[0] in f1 and couple[1] in f1:
                is_chemical = True
                break
            if couple[0] in f2 and couple[1] in f2:
                is_chemical = True
                break
        
        if is_chemical:
            chemical_pairs.append({
                **pair,
                'type': 'chemical_coupling',
                'description': f"Likely chemical coupling between {couple[0]} and {couple[1]} (common in Al alloys)"
            })
        else:
            non_chemical_pairs.append({
                **pair,
                'type': 'non_chemical',
                'description': f"Non-chemical collinearity (likely process-driven or statistical artifact)"
            })
    
    # Generate descriptive framing
    framing = {
        'summary': f"Analyzed {len(collinear_pairs)} collinear pairs. "
                  f"{len(chemical_pairs)} identified as chemical couplings, "
                  f"{len(non_chemical_pairs)} as non-chemical.",
        'chemical_framing': "Chemical couplings reflect inherent metallurgical relationships "
                           "between alloying elements (e.g., Mg-Si forming Mg2Si precipitates). "
                           "These are expected and physically meaningful.",
        'non_chemical_framing': "Non-chemical collinearity may arise from process constraints "
                               "(e.g., certain temperature ranges favoring specific compositions) "
                               "or statistical artifacts. These require careful interpretation."
    }
    
    return {
        'chemical': chemical_pairs,
        'non_chemical': non_chemical_pairs,
        'descriptive_framing': framing
    }

def run_validation_pipeline(input_path: str = None, output_path: str = None, threshold: float = 0.8) -> dict:
    """
    Main pipeline function to load data, calculate correlations, detect collinearity,
    and identify chemical vs non-chemical couplings.
    """
    config = get_config()
    if output_path is None:
        output_path = config.get('paths', {}).get('validation_report', 'artifacts/reports/collinearity_report.json')
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        df = load_processed_data(input_path)
        
        # Identify numeric columns for correlation analysis
        # Exclude target variable 'grain_size' and non-numeric columns like 'source_study'
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if 'grain_size' in numeric_cols:
            numeric_cols.remove('grain_size')
        
        if not numeric_cols:
            logger.warning("No numeric features found for collinearity analysis.")
            report = {
                'status': 'skipped',
                'reason': 'No numeric features available',
                'collinear_pairs': [],
                'chemical_couplings': [],
                'non_chemical_collinearity': [],
                'descriptive_framing': {}
            }
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            return report

        logger.info(f"Calculating correlation matrix for {len(numeric_cols)} features...")
        corr_matrix = calculate_correlation_matrix(df, numeric_cols)
        
        logger.info(f"Detecting collinear pairs with threshold |r| > {threshold}...")
        collinear_pairs = detect_collinearity(corr_matrix, threshold)
        
        # Identify chemical couplings
        coupling_analysis = identify_chemical_couplings(collinear_pairs)
        
        report = {
            'status': 'success',
            'threshold': threshold,
            'features_analyzed': numeric_cols,
            'collinear_pairs_count': len(collinear_pairs),
            'collinear_pairs': collinear_pairs,
            'chemical_couplings': coupling_analysis['chemical'],
            'non_chemical_collinearity': coupling_analysis['non_chemical'],
            'descriptive_framing': coupling_analysis['descriptive_framing']
        }
        
        # Log summary
        if collinear_pairs:
            logger.warning(f"Found {len(collinear_pairs)} collinear pairs with |r| > {threshold}.")
            for pair in collinear_pairs:
                logger.warning(f"  - {pair['feature1']} vs {pair['feature2']}: r = {pair['correlation']:.4f}")
            
            logger.info(f"Chemical couplings: {len(coupling_analysis['chemical'])}")
            logger.info(f"Non-chemical collinearity: {len(coupling_analysis['non_chemical'])}")
            
            # Log descriptive framing
            logger.info("Descriptive Framing:")
            logger.info(f"  Summary: {coupling_analysis['descriptive_framing']['summary']}")
            logger.info(f"  Chemical: {coupling_analysis['descriptive_framing']['chemical_framing']}")
            logger.info(f"  Non-chemical: {coupling_analysis['descriptive_framing']['non_chemical_framing']}")
        else:
            logger.info(f"No collinear pairs found with |r| > {threshold}.")
        
        # Save report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report saved to {output_path}")
        return report

    except Exception as e:
        logger.error(f"Validation pipeline failed: {str(e)}")
        error_report = {
            'status': 'error',
            'error': str(e),
            'chemical_couplings': [],
            'non_chemical_collinearity': [],
            'descriptive_framing': {}
        }
        with open(output_path, 'w') as f:
            json.dump(error_report, f, indent=2)
        raise

def main():
    parser = argparse.ArgumentParser(description='Validate data for collinearity and identify chemical couplings.')
    parser.add_argument('--input', type=str, default=None, help='Path to processed CSV (default: from config)')
    parser.add_argument('--output', type=str, default=None, help='Path to output JSON report (default: from config)')
    parser.add_argument('--threshold', type=float, default=0.8, help='Correlation threshold for flagging (default: 0.8)')
    
    args = parser.parse_args()
    
    run_validation_pipeline(
        input_path=args.input,
        output_path=args.output,
        threshold=args.threshold
    )

if __name__ == '__main__':
    main()