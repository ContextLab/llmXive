"""
Module for applying False Discovery Rate (FDR) correction to decoding results.
Implements Benjamini-Hochberg procedure across narrative categories and ROIs.
"""
import numpy as np
import json
import logging
from pathlib import Path
from statsmodels.stats.multitest import fdrcorrection
import code.config as config

logger = logging.getLogger(__name__)

def apply_fdr_to_results(results_path: str, output_path: str) -> dict:
    """
    Loads decoder metrics, extracts p-values, applies FDR correction,
    and saves the corrected results.

    Args:
        results_path: Path to the decoder metrics JSON (from T030/T031).
        output_path: Path where the FDR-corrected JSON will be written.

    Returns:
        A dictionary containing the corrected metrics.
    """
    logger.info(f"Loading decoder results from {results_path}")
    try:
        with open(results_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Decoder results file not found: {results_path}. "
                                "Ensure T030 and T031 have been completed.")

    # Extract p-values. We expect a list of results or a dict with a 'results' key.
    # Based on T030/T031 output schema, we assume a list of entries with p-values.
    # If the structure is flat, we adapt.
    entries = []
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict) and 'results' in data:
        entries = data['results']
    elif isinstance(data, dict):
        # Single entry case
        entries = [data]

    if not entries:
        logger.warning("No entries found in decoder results to correct.")
        return data

    # Collect p-values and metadata
    p_values = []
    metadata = []
    for i, entry in enumerate(entries):
        # Look for p-value key. T030 uses 'validation_p_value' or similar.
        # T031 might produce 'p_value' from permutation testing against null.
        p_val = entry.get('p_value')
        if p_val is None:
            p_val = entry.get('validation_p_value')
        
        if p_val is None:
            logger.warning(f"Entry {i} missing p-value. Skipping.")
            continue
        
        p_values.append(float(p_val))
        metadata.append(entry)

    if not p_values:
        logger.warning("No valid p-values found for FDR correction.")
        return data

    p_values = np.array(p_values)
    
    logger.info(f"Applying FDR correction (Benjamini-Hochberg) to {len(p_values)} hypotheses.")
    
    # Apply FDR correction
    # reject: boolean array indicating which hypotheses are rejected
    # pvals_corrected: adjusted p-values
    reject, pvals_corrected, _, _ = fdrcorrection(p_values, alpha=0.05, method='indep')

    # Update metadata with corrected values
    corrected_results = []
    for i, entry in enumerate(metadata):
        new_entry = entry.copy()
        new_entry['fdr_rejected'] = bool(reject[i])
        new_entry['fdr_corrected_p_value'] = float(pvals_corrected[i])
        corrected_results.append(new_entry)

    # Construct final output structure
    output_data = {
        'correction_method': 'Benjamini-Hochberg (FDR)',
        'alpha': 0.05,
        'n_hypotheses': len(p_values),
        'n_rejected': int(np.sum(reject)),
        'results': corrected_results
    }

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing FDR-corrected results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    return output_data

def run_fdr_correction_pipeline() -> None:
    """
    Main entry point to run FDR correction on the decoder analysis results.
    Reads from T030/T031 output and writes to results/fdr_corrected_metrics.json.
    """
    # Define paths based on config
    input_path = config.get_output_path('decoder_metrics.json')
    output_path = config.get_output_path('fdr_corrected_metrics.json')
    
    # If T030 output is a single file and T031 aggregates, we might need to 
    # combine them. For now, we assume T031's output (or a combined file) 
    # contains the p-values. 
    # If T031 produces 'results/permutation_pvalues.json', we might need to merge.
    # Assuming the primary p-values for narrative categories come from the 
    # decoder evaluation (T030/T031 combined logic).
    
    # Fallback: if the specific input path doesn't exist, try common locations
    if not Path(input_path).exists():
        # Try to find the most recent decoder metrics file
        possible_paths = [
            config.get_output_path('decoder_metrics.json'),
            'results/decoder_metrics.json',
            'results/combined_decoder_results.json'
        ]
        found = False
        for p in possible_paths:
            if Path(p).exists():
                input_path = p
                logger.info(f"Using alternative input path: {input_path}")
                found = True
                break
        if not found:
            raise FileNotFoundError("Could not locate decoder metrics file for FDR correction.")

    try:
        apply_fdr_to_results(input_path, output_path)
        logger.info("FDR correction completed successfully.")
    except Exception as e:
        logger.error(f"FDR correction failed: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_fdr_correction_pipeline()
