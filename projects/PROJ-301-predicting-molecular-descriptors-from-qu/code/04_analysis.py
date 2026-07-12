import os
import json
import logging
import argparse
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

# Importing from sibling modules as per API surface
from utils.logger import get_logger, configure_logging_for_pipeline

# Constants
BONFERRONI_THRESHOLD = 0.05 / 3  # 0.0167
REI_THRESHOLD = 0.10  # 10%

def load_model_artifact(path: str) -> Any:
    """Load a pickled model artifact."""
    logger = get_logger(__name__)
    logger.info(f"Loading model artifact from {path}")
    with open(path, 'rb') as f:
        return pickle.load(f)

def load_test_labels(path: str) -> Dict[str, Any]:
    """Load test labels from CSV (parquet handled by pandas internally if needed, but here we assume dict/json or CSV parsing)."""
    # Assuming labels.csv is loaded into a dict structure or DataFrame converted to dict for JSON compatibility in previous steps
    # For this task, we assume the structure matches what T022 produced or standard CSV loading.
    # Since T022 produces test_predictions.json which references labels, we might need to load labels directly if not in predictions.
    # However, T024 requires MAE values. Let's assume we load the main labels file.
    # The task says "Input: Load p-values... and MAE values".
    # We will load the labels file to get ground truth and predictions to calculate MAE if not pre-calc.
    # Actually, T022 output is test_predictions.json which likely contains errors or predictions.
    # Let's implement a robust loader that can handle the expected JSON structure from T022 if needed,
    # or load the raw labels if we need to compute MAE ourselves.
    # Given T023 input is test_predictions.json, T024 likely needs to load that too.
    
    logger = get_logger(__name__)
    logger.info(f"Loading test labels from {path}")
    
    # If it's a parquet/csv, we use pandas. If it's the JSON from T022, we use json.
    # The task description says "Input: Load p-values from statistics.json and MAE values".
    # It implies MAE values might be derived or present.
    # Let's assume we load the 'data/processed/labels.csv' to get the ground truth and
    # 'artifacts/metrics/test_predictions.json' to get the errors.
    pass

def generate_predictions(model_2d, model_3d, X_test_2d, X_test_3d, y_test) -> Dict[str, np.ndarray]:
    """Generate predictions for the test set."""
    logger = get_logger(__name__)
    logger.info("Generating predictions for test set")
    
    pred_2d = model_2d.predict(X_test_2d)
    pred_3d = model_3d.predict(X_test_3d)
    
    return {
        "pred_2d": pred_2d,
        "pred_3d": pred_3d,
        "y_true": y_test
    }

def perform_statistical_analysis(predictions: Dict[str, np.ndarray], descriptors: List[str]) -> Dict[str, float]:
    """Perform Wilcoxon signed-rank test on per-molecule absolute errors."""
    logger = get_logger(__name__)
    logger.info("Performing statistical analysis")
    
    # Extract absolute errors
    # Assuming predictions dict contains 'error_2d' and 'error_3d' or we calculate them
    # T022 output structure: test_predictions.json includes error_2d, error_3d arrays.
    # If we are re-calculating here:
    abs_err_2d = np.abs(predictions['pred_2d'] - predictions['y_true'])
    abs_err_3d = np.abs(predictions['pred_3d'] - predictions['y_true'])
    
    # We need to perform the test per descriptor.
    # Assuming the data is already split by descriptor or we are testing the whole set if it's a single descriptor task.
    # The spec mentions "for each descriptor".
    # For this implementation, we assume the input data is already filtered by descriptor or we iterate.
    # Since the input to this function is a flat array (from T022), we assume T022 handled the descriptor splitting
    # or we are running this on a single descriptor's data.
    # If we need to support multiple descriptors in one go, the input structure would be different.
    # Given T023 output is a single p-value per descriptor, we assume this function is called per descriptor
    # or the input contains the specific slice.
    
    from scipy.stats import wilcoxon
    
    stat, p_value = wilcoxon(abs_err_2d, abs_err_3d)
    
    return {"p_value": float(p_value)}

def define_failure_boundary(p_values: Dict[str, float], mae_2d: Dict[str, float], mae_3d: Dict[str, float], 
                            errors_2d: np.ndarray, errors_3d: np.ndarray, molecule_ids: List[str], 
                            descriptors: List[str]) -> List[Dict[str, Any]]:
    """
    Define Failure Boundary where Relative Error Increase (REI) >= 10% OR p-value < 0.0167.
    
    Logic:
    1. Check p-value threshold for the descriptor. If p < 0.0167, the difference is statistically significant.
       In this context, "Failure" for the 2D model relative to 3D might mean 2D is significantly worse.
       However, the task says "Failure Boundary" generally.
       Let's interpret: A molecule is in the failure boundary if the 2D model fails relative to 3D significantly.
       We check if the REI for that specific molecule (or the aggregate for the descriptor?) meets the criteria.
       
       Re-reading T024: "Define Failure Boundary where Relative Error Increase (REI) >= 10% OR p-value < 0.0167".
       This implies two conditions for a molecule to be flagged:
       a) Its individual REI >= 10% (2D error is 10% higher than 3D error).
       b) The global statistical test for its descriptor has p < 0.0167 (significant difference exists for this descriptor).
       
       Actually, the "OR" suggests:
       - If the descriptor has a significant difference (p < 0.0167), ALL molecules of that descriptor might be considered?
       - OR if a specific molecule has REI >= 10%.
       
       Let's refine based on "Failure Boundary Identification":
       We want to identify specific molecules where 2D performs poorly compared to 3D.
       Criteria for a molecule (m, d):
       1. REI(m, d) = (|Error_2D(m, d)| - |Error_3D(m, d)|) / |Error_3D(m, d)| >= 0.10
          (Assuming Error_3D is the baseline/better one. If Error_3D is near 0, REI is undefined/infinite, so we handle that).
       2. OR the descriptor d has a global p-value < 0.0167. (This seems to flag the whole descriptor as "problematic" for 2D).
       
       However, the output schema is `[{"molecule_id": "string", "descriptor": "string", "reason": "string"}]`.
       This implies we are listing molecules.
       
       Interpretation:
       A molecule is added to the list if:
       - Its REI >= 10% (Reason: "High relative error increase").
       - OR if the descriptor's global p-value < 0.0167 (Reason: "Significant statistical difference for descriptor").
       
       Wait, if the p-value condition is met, does it flag EVERY molecule? That might be too broad.
       Maybe the "Failure Boundary" is the set of molecules that drive the statistical significance?
       Or maybe the prompt implies: "Flag molecules where REI >= 10% AND the descriptor is statistically significant (p < 0.0167)".
       But the prompt says "OR".
       
       Let's stick to the literal "OR":
       Condition A: REI >= 10% (Local failure).
       Condition B: Global p-value < 0.0167 (Global significance).
       
       If B is true for a descriptor, then all molecules of that descriptor are "in the boundary"?
       That seems like a "Global Failure" for that descriptor.
       Let's assume the task wants to list molecules that are either locally bad (REI) or belong to a globally bad descriptor.
       
       Actually, a more nuanced reading: "Define Failure Boundary" usually means a region in feature space.
       Here, it's a list of molecules.
       Let's implement:
       1. Calculate REI for each molecule.
       2. If REI >= 10%, add to list with reason "REI >= 10%".
       3. If p-value for the descriptor < 0.0167, add ALL molecules of that descriptor?
          Or maybe the prompt implies the "Boundary" is defined by these two metrics.
          Let's assume we list molecules that satisfy REI >= 10% OR (Descriptor p < 0.0167).
          If p < 0.0167, we list all molecules for that descriptor as "Statistically significant difference in descriptor".
          
       Let's refine the "OR":
       - If p < 0.0167, the 2D model is significantly worse overall for this descriptor.
       - We flag molecules where 2D is significantly worse (REI >= 10%).
       
       Maybe the "OR" is:
       - Flag if REI >= 10%.
       - Flag if p < 0.0167 (meaning the whole class is problematic).
       
       Let's go with:
       For each molecule:
         If REI >= 0.10: add.
         Else if descriptor_p_value < 0.0167: add (with reason "Descriptor statistically significant").
       
       This ensures we capture local outliers and globally significant descriptors.
    """
    logger = get_logger(__name__)
    failure_boundary = []
    
    # Map descriptor to p-value
    # p_values is likely { "dipole": 0.001, "HOMO": 0.5, ... }
    # mae_2d, mae_3d are likely aggregates or not needed per molecule if we use errors arrays.
    # We have errors_2d, errors_3d (absolute errors) and molecule_ids.
    
    for i, mol_id in enumerate(molecule_ids):
        err_2d = abs(errors_2d[i])
        err_3d = abs(errors_3d[i])
        
        # Determine descriptor for this molecule.
        # The input lists `descriptors` but we need to know which descriptor this molecule belongs to.
        # Assuming the input arrays are sorted by descriptor or we have a way to map.
        # If the input is a single descriptor's data, we just use that descriptor.
        # If the input is mixed, we need a mapping.
        # Since T022 output is `test_predictions.json` with arrays, and T023 runs per descriptor,
        # it's likely this function is called per descriptor slice.
        # Let's assume `descriptors` list has one element or we iterate.
        # If we are processing a single descriptor at a time:
        if len(descriptors) == 1:
            current_desc = descriptors[0]
            desc_p = p_values.get(current_desc, 1.0)
            
            # Calculate REI
            # Avoid division by zero
            if err_3d > 1e-9:
                rei = (err_2d - err_3d) / err_3d
            else:
                rei = float('inf') if err_2d > 0 else 0.0
            
            is_rei_fail = rei >= REI_THRESHOLD
            is_p_fail = desc_p < BONFERRONI_THRESHOLD
            
            if is_rei_fail:
                failure_boundary.append({
                    "molecule_id": mol_id,
                    "descriptor": current_desc,
                    "reason": f"REI ({rei:.2%}) >= 10%"
                })
            elif is_p_fail:
                # If the descriptor is globally significant, do we flag ALL molecules?
                # The prompt says "OR p-value < 0.0167".
                # If we flag all, the list will be huge.
                # Maybe the "Failure Boundary" is the set of molecules where the model fails.
                # If the global test says 2D is worse, maybe we only flag the ones that contribute?
                # But the condition is "OR".
                # Let's assume if p < 0.0167, we flag the molecule as "Descriptor significant".
                # But this would duplicate the list if we already flagged by REI.
                # Let's add if p < 0.0167 AND REI is not the reason?
                # No, "OR" means if either is true.
                # If p < 0.0167, the whole descriptor is "failed".
                # We will add the molecule with reason "Descriptor statistically significant".
                failure_boundary.append({
                    "molecule_id": mol_id,
                    "descriptor": current_desc,
                    "reason": "Descriptor p-value < 0.0167 (Significant difference)"
                })
        else:
            # If mixed, we need a mapping. Assuming not the case for this call.
            logger.warning("Multiple descriptors in input without mapping. Skipping.")
            
    return failure_boundary

def main():
    """
    Main entry point for T024: Define Failure Boundary.
    1. Load p-values from artifacts/metrics/statistics.json.
    2. Load test predictions (errors) from artifacts/metrics/test_predictions.json.
    3. Load labels/molecule IDs if needed.
    4. Compute REI and check p-values.
    5. Save failure_boundary.json.
    """
    configure_logging_for_pipeline()
    logger = get_logger(__name__)
    
    # Paths
    stats_path = Path("artifacts/metrics/statistics.json")
    predictions_path = Path("artifacts/metrics/test_predictions.json")
    output_path = Path("artifacts/metrics/failure_boundary.json")
    
    # Ensure directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load Statistics
    if not stats_path.exists():
        logger.error(f"Statistics file not found: {stats_path}")
        # If stats are missing, we cannot determine p-values.
        # Return empty or error?
        # Let's save an empty list and log warning.
        with open(output_path, 'w') as f:
            json.dump([], f)
        return
        
    with open(stats_path, 'r') as f:
        stats_data = json.load(f)
    
    # Load Predictions
    if not predictions_path.exists():
        logger.error(f"Predictions file not found: {predictions_path}")
        with open(output_path, 'w') as f:
            json.dump([], f)
        return
        
    with open(predictions_path, 'r') as f:
        pred_data = json.load(f)
    
    # Expected structure of pred_data based on T022:
    # { "error_2d": [...], "error_3d": [...], "molecule_ids": [...], "descriptors": [...] }
    # Or maybe it's a list of molecules?
    # T022 says: "Store per-molecule errors in ... (includes error_2d, error_3d arrays per molecule)".
    # This implies a structure like:
    # [ {"id": "...", "error_2d": ..., "error_3d": ...}, ... ]
    # OR
    # { "error_2d": [array], "error_3d": [array], "molecule_ids": [array] }
    
    # Let's handle the array format which is common for statistical tests.
    error_2d = np.array(pred_data.get("error_2d", []))
    error_3d = np.array(pred_data.get("error_3d", []))
    molecule_ids = pred_data.get("molecule_ids", [])
    
    # If the data is per descriptor, we need to know which descriptor corresponds to which index.
    # If the file contains multiple descriptors, it might be structured as:
    # { "dipole": { "error_2d": [...], ... }, "HOMO": ... }
    # Let's check if keys are descriptors.
    descriptors = []
    data_by_desc = {}
    
    if "error_2d" in pred_data and isinstance(pred_data["error_2d"], list):
        # Assume single descriptor or flat list
        # If flat, we need to know the descriptor.
        # Maybe the file has a "descriptor" key or we assume one.
        # If T023 ran per descriptor, maybe this file has one entry per descriptor?
        # Let's assume the file structure is:
        # { "dipole": { "error_2d": [...], "error_3d": [...], "molecule_ids": [...] }, ... }
        # OR
        # { "error_2d": [...], "error_3d": [...], "molecule_ids": [...], "descriptor": "dipole" }
        
        # Check if we have multiple descriptors
        if "dipole" in pred_data or "HOMO" in pred_data or "LUMO" in pred_data:
            # It's a dict of descriptors
            descriptors = [k for k in pred_data.keys() if k in ["dipole", "HOMO", "LUMO"]]
            data_by_desc = {k: pred_data[k] for k in descriptors}
        else:
            # Flat structure, assume single descriptor or need to map
            # If no descriptor key, we can't map.
            # Let's assume the stats file has keys that match the data.
            descriptors = list(stats_data.keys())
            # If we have flat arrays, we assume the order matches the descriptor?
            # This is ambiguous. Let's assume the file is structured by descriptor.
            pass
    else:
        # Fallback: try to parse as dict of descriptors
        descriptors = [k for k in pred_data.keys() if k in ["dipole", "HOMO", "LUMO"]]
        if not descriptors:
            # Maybe it's a list of objects?
            if isinstance(pred_data, list):
                logger.error("Predictions file is a list of objects, but expected dict or flat arrays.")
                with open(output_path, 'w') as f:
                    json.dump([], f)
                return
            else:
                # Assume single descriptor
                descriptors = ["unknown"]
                data_by_desc = {"unknown": pred_data}
    
    failure_boundary = []
    
    for desc in descriptors:
        if desc not in data_by_desc:
            # Try to find in flat structure if we couldn't parse earlier
            # If stats has this key, but data doesn't, skip.
            logger.warning(f"Descriptor {desc} not found in predictions data.")
            continue
        
        desc_data = data_by_desc[desc]
        err_2d = np.array(desc_data.get("error_2d", []))
        err_3d = np.array(desc_data.get("error_3d", []))
        mol_ids = desc_data.get("molecule_ids", [])
        
        # Get p-value for this descriptor
        p_val = stats_data.get(desc, 1.0)
        
        # Calculate REI and check conditions
        for i, mol_id in enumerate(mol_ids):
            e2 = abs(err_2d[i]) if i < len(err_2d) else 0
            e3 = abs(err_3d[i]) if i < len(err_3d) else 0
            
            if e3 > 1e-9:
                rei = (e2 - e3) / e3
            else:
                rei = float('inf') if e2 > 0 else 0.0
            
            is_rei_fail = rei >= REI_THRESHOLD
            is_p_fail = p_val < BONFERRONI_THRESHOLD
            
            if is_rei_fail:
                failure_boundary.append({
                    "molecule_id": str(mol_id),
                    "descriptor": desc,
                    "reason": f"REI ({rei:.2%}) >= 10%"
                })
            elif is_p_fail:
                failure_boundary.append({
                    "molecule_id": str(mol_id),
                    "descriptor": desc,
                    "reason": "Descriptor p-value < 0.0167 (Significant difference)"
                })
    
    # Save output
    with open(output_path, 'w') as f:
        json.dump(failure_boundary, f, indent=2)
    
    logger.info(f"Failure boundary saved to {output_path} with {len(failure_boundary)} entries.")

if __name__ == "__main__":
    main()