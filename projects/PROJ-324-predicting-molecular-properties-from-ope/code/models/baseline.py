import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Crippen

# Ensure logger setup
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class CrippenCalc:
    """Wrapper for Crippen atomic contribution calculations."""
    
    @staticmethod
    def get_contributions(smiles: str) -> Dict[str, float]:
        """
        Calculate Crippen contributions for logP and Molar Refractivity (MR).
        Note: Crippen's original method targets logP and MR. 
        For solubility and boiling point, we use logP as a proxy or return NaN 
        if the specific property is not directly calculable by this method.
        """
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {"logP": np.nan, "solubility": np.nan, "boiling_point": np.nan}
        
        # Calculate logP and MR
        logP = Crippen.LogP(mol)
        mr = Crippen.MR(mol)
        
        # Map to expected properties
        # Note: Boiling point and Solubility are not directly Crippen properties.
        # We return the calculated logP for logP, and NaN for others to indicate
        # the baseline method's limitation for those specific targets in this context.
        # However, per task T014a, we must output values. We will output NaN for 
        # properties not directly supported by Crippen, to be imputed in T014b.
        return {
            "logP": logP,
            "solubility": np.nan,  # Not directly supported by Crippen
            "boiling_point": np.nan # Not directly supported by Crippen
        }

def get_crippen_contributions(smiles: str) -> Dict[str, float]:
    """Convenience wrapper for CrippenCalc."""
    return CrippenCalc.get_contributions(smiles)

def compute_crippen_contributions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Crippen contributions for all molecules in a dataframe.
    Adds columns: predicted_logP, predicted_solubility, predicted_boiling_point.
    """
    logger.info(f"Computing Crippen contributions for {len(df)} molecules...")
    
    results = []
    for i, row in df.iterrows():
        smiles = row['smiles']
        props = get_crippen_contributions(smiles)
        results.append({
            'smiles': smiles,
            'predicted_logP': props['logP'],
            'predicted_solubility': props['solubility'],
            'predicted_boiling_point': props['boiling_point']
        })
    
    return pd.DataFrame(results)

def save_predictions(predictions_df: pd.DataFrame, output_path: str):
    """Save predictions to a CSV file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    predictions_df.to_csv(output_path, index=False)
    logger.info(f"Saved predictions to {output_path}")

def process_dataset(input_path: str, output_path: str):
    """
    Process a dataset: load, compute Crippen contributions, save.
    """
    logger.info(f"Loading dataset from {input_path}...")
    df = pd.read_csv(input_path)
    
    if 'smiles' not in df.columns:
        raise ValueError(f"Input file {input_path} must contain a 'smiles' column.")
    
    predictions = compute_crippen_contributions(df)
    save_predictions(predictions, output_path)
    return predictions

def impute_undefined_atoms(predictions_df: pd.DataFrame, 
                           train_set_path: str, 
                           output_path: str):
    """
    T014b: Impute undefined atoms (NaN values) by setting their predicted values 
    to the mean of the training set for the corresponding property.
    
    Args:
        predictions_df: DataFrame with columns 'predicted_logP', 'predicted_solubility', 
                        'predicted_boiling_point'.
        train_set_path: Path to the training set CSV (data/derived/train_set.csv) 
                        which contains experimental values to calculate means from?
                        OR: The task implies using the mean of the TRAINING SET'S 
                        PREDICTIONS? 
                        Re-reading T014b: "setting their predicted values to the mean 
                        of the training set for the corresponding property."
                        Usually, this means the mean of the experimental values in the 
                        training set, or the mean of the baseline predictions on the 
                        training set. Given the context of "undefined atoms" (where 
                        Crippen fails to calculate), imputing with the mean of the 
                        *training set's experimental values* is the standard baseline 
                        approach for missing predictions.
                        
                        However, the prompt says "mean of the training set for the 
                        corresponding property". If the training set has experimental 
                        values, we use those. If we only have predictions, we use those.
                        The training set CSV (T011.5) contains experimental values.
                        We will calculate the mean of the experimental values for the 
                        properties present in the training set and use that to impute.
    
    Process:
        1. Load train_set.csv to get experimental values for logP, solubility, boiling_point.
        2. Calculate mean for each property.
        3. Fill NaN in predictions_df with these means.
        4. Save to output_path.
    """
    logger.info("T014b: Imputing undefined atoms...")
    
    if not os.path.exists(train_set_path):
        raise FileNotFoundError(f"Training set not found at {train_set_path}. "
                                "Please ensure T011.5 (Split Dataset) is completed.")
    
    train_df = pd.read_csv(train_set_path)
    
    # Identify experimental columns in training set
    # Expected columns based on T011.5: 'smiles', 'property_name', 'value' (long format) 
    # OR 'logP', 'solubility', 'boiling_point' (wide format).
    # T009/T010.1 output format is usually long: smiles, property_name, value.
    # T011.5 splits this. Let's handle both or assume wide if long is not detected.
    
    means = {}
    target_props = ['logP', 'solubility', 'boiling_point']
    pred_cols = ['predicted_logP', 'predicted_solubility', 'predicted_boiling_point']
    
    for prop, pred_col in zip(target_props, pred_cols):
        if pred_col not in predictions_df.columns:
            continue
        
        # Calculate mean from training set experimental values
        # If train_df is wide (columns: smiles, logP, solubility...)
        if prop in train_df.columns:
            mean_val = train_df[prop].mean()
        # If train_df is long (columns: smiles, property_name, value)
        elif 'property_name' in train_df.columns and 'value' in train_df.columns:
            subset = train_df[train_df['property_name'] == prop]
            mean_val = subset['value'].mean()
        else:
            # Fallback: if no experimental data, use 0 or NaN (but task says impute)
            logger.warning(f"Could not find experimental {prop} in training set. Imputing with 0.")
            mean_val = 0.0
        
        means[pred_col] = mean_val
        logger.info(f"Mean for {prop}: {mean_val:.4f}")
    
    # Impute
    for col, mean_val in means.items():
        predictions_df[col] = predictions_df[col].fillna(mean_val)
    
    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    predictions_df.to_csv(output_path, index=False)
    logger.info(f"Imputed predictions saved to {output_path}")
    
    return predictions_df

def main():
    """Main entry point for T014a and T014b execution."""
    # Paths
    diverse_subset_path = "data/derived/diverse_subset.csv"
    train_set_path = "data/derived/train_set.csv"
    raw_predictions_path = "data/derived/baseline_predictions_raw.csv" # T014a output
    imputed_predictions_path = "data/derived/baseline_predictions_imputed.csv" # T014b output
    
    # Ensure T014a ran first (or run it here if needed, but task is T014b)
    # We assume T014a output exists or we run it.
    if not os.path.exists(raw_predictions_path):
        logger.info("Raw predictions not found. Running T014a first...")
        process_dataset(diverse_subset_path, raw_predictions_path)
    
    # Run T014b
    logger.info(f"Loading raw predictions from {raw_predictions_path}...")
    raw_df = pd.read_csv(raw_predictions_path)
    
    imputed_df = impute_undefined_atoms(raw_df, train_set_path, imputed_predictions_path)
    
    # Also, T014.5 requires extracting test predictions. 
    # While T014.5 is a separate task, T014b's output is the imputed full set.
    # We ensure the imputed file is written.
    
    logger.info("T014b completed successfully.")

if __name__ == "__main__":
    main()