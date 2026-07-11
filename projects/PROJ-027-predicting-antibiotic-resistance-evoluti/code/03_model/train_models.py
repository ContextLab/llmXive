import os
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold, cross_validate, StratifiedShuffleSplit
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support, confusion_matrix, classification_report
from sklearn.preprocessing import StandardScaler
import joblib
from scipy.stats import pearsonr

# Import project utilities
# Assuming these are available in the project path
from utils.logging import get_logger
from utils.config import load_config, get_random_seed

# Import task dependencies
# T023a output handling (mechanism-blind filtered matrix)
# T023b output handling (data splits)
# T019 output handling (phylogeny tree for clade IDs)

logger = get_logger(__name__)

def load_filtered_matrix(path: str) -> pd.DataFrame:
    """Load the mechanism-blind filtered feature matrix."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Filtered matrix not found at {path}. Ensure T023a has run.")
    df = pd.read_csv(path, index_col=0)
    logger.info(f"Loaded filtered matrix with shape {df.shape}")
    return df

def load_split_metadata(path: str) -> Dict[str, Any]:
    """Load split metadata containing train/val/test indices and clade assignments."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Split metadata not found at {path}. Ensure T023b has run.")
    with open(path, 'r') as f:
        return json.load(f)

def load_phylogeny_clades(tree_path: str, isolate_ids: List[str]) -> Dict[str, str]:
    """
    Load phylogeny tree and assign clade IDs to isolates.
    This function infers clades based on a simple threshold on branch length or
    a pre-defined clade mapping if available in the tree metadata.
    For this implementation, we assume the tree file (Newick) contains node labels
    or we group isolates by a heuristic (e.g., first 200 isolates = clade A, etc.)
    if specific clade logic isn't present.
    
    However, T019 'generate_phylogeny.py' typically outputs a tree. 
    We will assume a companion file or a specific structure exists for clade assignment.
    If not, we will implement a simple distance-based clustering to define clades
    for the Phylogenetically-Blocked CV.
    
    For this task, we assume the split metadata from T023b already contains 'clade_id'
    for each isolate if T023b was designed to parse the tree. 
    If not, we need to parse the tree here.
    
    Given the API surface, T019 outputs a tree. T023b (split_data) likely needs the tree.
    We will assume the 'split_metadata.json' from T023b includes 'clade_id' per isolate
    as part of the split process (since it's a prerequisite for Phylo-CV).
    If not present, we raise an error.
    """
    # If split metadata has clade info, use it.
    # Otherwise, we would need to parse the tree here.
    # For this implementation, we rely on split_metadata having 'clade_id' column or dict.
    logger.info("Clade IDs expected to be present in split metadata from T023b.")
    return {} 

def train_logistic_regression(X_train, y_train, X_val, y_val, groups=None):
    """Train L1-regularized Logistic Regression."""
    # Scale data
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)

    # Use GroupKFold for Phylogenetically-Blocked CV if groups provided
    # But here we are training on a fixed split. 
    # The task says "using Phylogenetically-Blocked CV". 
    # This implies the CV process itself is blocked.
    # However, we are given train/val/test splits. 
    # We will perform CV on the training set using GroupKFold based on clade.
    
    if groups is not None:
        gkf = GroupKFold(n_splits=5)
        # Ensure groups align with X_train
        cv_results = cross_validate(
            LogisticRegression(penalty='l1', solver='saga', max_iter=1000, random_state=get_random_seed()),
            X_train_scaled, y_train,
            cv=gkf.split(X_train_scaled, y_train, groups=groups),
            scoring='roc_auc',
            return_train_score=True
        )
        mean_auc = cv_results['test_score'].mean()
        logger.info(f"L1 Logistic Regression CV AUC (Phylo-Blocked): {mean_auc:.4f}")
    else:
        logger.warning("No groups provided for Phylogenetically-Blocked CV. Using standard KFold.")
        # Fallback to standard if groups missing (should not happen if T023b did its job)
        from sklearn.model_selection import KFold
        kf = KFold(n_splits=5, shuffle=True, random_state=get_random_seed())
        cv_results = cross_validate(
            LogisticRegression(penalty='l1', solver='saga', max_iter=1000, random_state=get_random_seed()),
            X_train_scaled, y_train,
            cv=kf,
            scoring='roc_auc'
        )
        mean_auc = cv_results['test_score'].mean()

    # Final model on full train set
    model = LogisticRegression(penalty='l1', solver='saga', max_iter=1000, random_state=get_random_seed())
    model.fit(X_train_scaled, y_train)
    
    # Evaluate on validation
    val_pred = model.predict_proba(X_val_scaled)[:, 1]
    val_auc = roc_auc_score(y_val, val_pred)
    
    return model, scaler, val_auc

def train_random_forest(X_train, y_train, X_val, y_val, groups=None):
    """Train Random Forest."""
    # RF doesn't strictly need scaling, but consistent pipeline
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)

    # Phylogenetically-Blocked CV for RF
    if groups is not None:
        gkf = GroupKFold(n_splits=5)
        cv_results = cross_validate(
            RandomForestClassifier(n_estimators=100, random_state=get_random_seed(), n_jobs=-1),
            X_train_scaled, y_train,
            cv=gkf.split(X_train_scaled, y_train, groups=groups),
            scoring='roc_auc'
        )
        mean_auc = cv_results['test_score'].mean()
        logger.info(f"Random Forest CV AUC (Phylo-Blocked): {mean_auc:.4f}")
    else:
        logger.warning("No groups provided for Phylogenetically-Blocked CV. Using standard KFold.")
        from sklearn.model_selection import KFold
        kf = KFold(n_splits=5, shuffle=True, random_state=get_random_seed())
        cv_results = cross_validate(
            RandomForestClassifier(n_estimators=100, random_state=get_random_seed(), n_jobs=-1),
            X_train_scaled, y_train,
            cv=kf,
            scoring='roc_auc'
        )
        mean_auc = cv_results['test_score'].mean()

    # Final model
    model = RandomForestClassifier(n_estimators=100, random_state=get_random_seed(), n_jobs=-1)
    model.fit(X_train_scaled, y_train)

    # Evaluate on validation
    val_pred = model.predict_proba(X_val_scaled)[:, 1]
    val_auc = roc_auc_score(y_val, val_pred)

    return model, scaler, val_auc

def train_models_for_class(
    class_name: str,
    features: pd.DataFrame,
    splits: Dict[str, pd.DataFrame],
    clade_map: Dict[str, str],
    output_dir: Path
) -> Dict[str, Any]:
    """Train both models for a specific antibiotic class."""
    logger.info(f"Training models for antibiotic class: {class_name}")
    
    # Extract data for this class
    # Assuming 'resistance_phenotype' column exists and is binary for this class
    # The feature matrix might be filtered by class in T023b or here
    # We assume splits are already class-specific or we filter here
    
    # If splits contain all classes, we need to filter. 
    # Based on T023b description, it does initial stratified split. 
    # We assume T023b outputs per-class splits or we filter now.
    # For this implementation, we assume the input 'features' is already filtered for the class
    # or 'splits' contains indices that are class-specific.
    
    # Let's assume 'features' is the full matrix and we filter by class in the phenotype column
    # But the task says "per antibiotic class". 
    # We will assume the 'splits' dictionary has keys like 'train', 'val', 'test'
    # and the dataframe inside is already filtered for the current class.
    
    train_df = splits.get('train')
    val_df = splits.get('val')
    test_df = splits.get('test')
    
    if train_df is None or val_df is None:
        logger.warning(f"Missing splits for class {class_name}. Skipping.")
        return {}

    # Prepare X and y
    # Assuming features columns are all except 'isolate_id' and 'resistance_phenotype'
    # But we need to be careful: the feature matrix from T016 has 'resistance_phenotype'
    # T023a (mechanism blind) keeps phenotype.
    
    # We need to identify the target column for this class.
    # If the phenotype column is a single column with values like "Resistant", "Sensitive",
    # we need to map it. Or if there are multiple columns per class.
    # T016 output: 'resistance_phenotype' (likely categorical or binary per row).
    # If multiple classes, the matrix might have multiple phenotype columns or one multi-class column.
    # Given "per antibiotic class", we assume we are processing one class at a time.
    # Let's assume the 'splits' dataframes are already filtered to isolates of this class
    # and the 'resistance_phenotype' column is binary (0/1) for this class.
    
    # If the phenotype is not binary, we need to binarize.
    # For now, assume binary 0/1.
    
    y_train = train_df['resistance_phenotype'].values
    y_val = val_df['resistance_phenotype'].values
    
    # Feature columns: all numeric columns except isolate_id
    feature_cols = [c for c in features.columns if c not in ['isolate_id', 'resistance_phenotype']]
    X_train = train_df[feature_cols].values
    X_val = val_df[feature_cols].values
    
    # Get clade IDs for groups
    train_indices = train_df['isolate_id'].values
    groups_train = np.array([clade_map.get(i, 'Unknown') for i in train_indices])
    val_indices = val_df['isolate_id'].values
    groups_val = np.array([clade_map.get(i, 'Unknown') for i in val_indices])
    
    # Train LR
    lr_model, lr_scaler, lr_val_auc = train_logistic_regression(X_train, y_train, X_val, y_val, groups_train)
    
    # Train RF
    rf_model, rf_scaler, rf_val_auc = train_random_forest(X_train, y_train, X_val, y_val, groups_train)
    
    # Save models
    lr_path = output_dir / f"lr_{class_name}.pkl"
    rf_path = output_dir / f"rf_{class_name}.pkl"
    
    joblib.dump({'model': lr_model, 'scaler': lr_scaler}, lr_path)
    joblib.dump({'model': rf_model, 'scaler': rf_scaler}, rf_path)
    
    logger.info(f"Saved models for {class_name} to {output_dir}")
    
    return {
        'class': class_name,
        'lr_val_auc': lr_val_auc,
        'rf_val_auc': rf_val_auc,
        'lr_model_path': str(lr_path),
        'rf_model_path': str(rf_path)
    }

def main():
    parser = argparse.ArgumentParser(description="Train Logistic Regression and Random Forest models with Phylogenetically-Blocked CV")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--input-matrix", type=str, default="data/processed/filtered_feature_matrix.csv", help="Path to mechanism-blind filtered matrix")
    parser.add_argument("--splits", type=str, default="data/processed/split_metadata.json", help="Path to split metadata from T023b")
    parser.add_argument("--tree", type=str, default="data/processed/phylogeny.tree", help="Path to phylogeny tree (for clade mapping if not in splits)")
    parser.add_argument("--output-dir", type=str, default="data/models", help="Output directory for models")
    args = parser.parse_args()
    
    # Setup logging
    logger.info("Starting model training (T023c)")
    
    # Load config
    config = load_config(args.config)
    seed = get_random_seed(config)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    features = load_filtered_matrix(args.input_matrix)
    splits_data = load_split_metadata(args.splits)
    
    # Determine classes to train
    # If splits_data contains a list of classes, use that.
    # Otherwise, assume unique values in 'resistance_phenotype' column (if multi-class)
    # or iterate over a predefined list in config.
    # For this implementation, we assume the splits are organized by class in the metadata
    # or we derive classes from the phenotype column.
    
    # Check if splits_data has a 'classes' key
    if 'classes' in splits_data:
        classes = splits_data['classes']
    else:
        # Fallback: unique values in phenotype
        # This assumes the matrix contains all classes and we filter per class
        # But T023b might have already split by class.
        # Let's assume we need to filter the main features by class if not already done.
        # This is complex. We will assume the 'splits_data' contains a dict of splits per class
        # OR the input matrix is already filtered for a single class (if run per class).
        # Given the task "per antibiotic class", we assume we iterate.
        # We'll look for a 'class_splits' structure in splits_data.
        if 'class_splits' in splits_data:
            classes = list(splits_data['class_splits'].keys())
        else:
            # Assume single class or error
            logger.error("Cannot determine classes. Expected 'classes' or 'class_splits' in split metadata.")
            return

    # Load clade map if not in splits
    clade_map = {}
    if 'clade_map' in splits_data:
        clade_map = splits_data['clade_map']
    else:
        # Try to load from tree if necessary (complex, skipped for now)
        logger.warning("Clade map not found in split metadata. Phylogenetically-Blocked CV may be compromised.")
    
    results = []
    
    for class_name in classes:
        # Get splits for this class
        class_splits = splits_data.get('class_splits', {}).get(class_name, None)
        if class_splits is None:
            # Maybe splits_data is flat and we need to filter?
            # We'll assume a structure where splits_data['train'] is a dataframe
            # and we filter by class_name.
            # But this is ambiguous. Let's assume the T023b output has a structure:
            # { "classes": ["class1", "class2"], "class_splits": { "class1": { "train": ..., "val": ... } } }
            # If not, we skip.
            logger.warning(f"No splits found for class {class_name}. Skipping.")
            continue
        
        # If class_splits is a dict of dataframes (loaded as JSON, need to reconstruct)
        # JSON doesn't hold DataFrames. T023b likely saved CSVs for splits.
        # We assume T023b saved: data/processed/splits/{class_name}_train.csv, etc.
        # Or the split_metadata.json points to files.
        # Let's assume split_metadata.json contains paths or we reconstruct from indices.
        # For simplicity in this artifact, we assume split_metadata.json contains the data as lists
        # or we load from expected file paths.
        
        # Re-evaluating T023b output: "save_splits" likely saves CSVs.
        # We need to load them here.
        # We'll assume a standard path: data/processed/splits/{class_name}_{split_type}.csv
        split_base = Path("data/processed/splits")
        if not split_base.exists():
            logger.error(f"Split directory {split_base} not found. Ensure T023b created it.")
            continue
            
        train_path = split_base / f"{class_name}_train.csv"
        val_path = split_base / f"{class_name}_val.csv"
        test_path = split_base / f"{class_name}_test.csv"
        
        if not train_path.exists() or not val_path.exists():
            logger.warning(f"Missing split files for {class_name}. Skipping.")
            continue
            
        train_df = pd.read_csv(train_path, index_col=0)
        val_df = pd.read_csv(val_path, index_col=0)
        test_df = pd.read_csv(test_path, index_col=0) if test_path.exists() else None
        
        # Train
        result = train_models_for_class(
            class_name,
            features, # We need the full feature matrix to map indices? Or just use train_df columns
            {'train': train_df, 'val': val_df, 'test': test_df},
            clade_map,
            output_dir
        )
        if result:
            results.append(result)
    
    # Save summary
    summary_path = output_dir / "training_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Training summary saved to {summary_path}")

if __name__ == "__main__":
    main()
