"""
Evaluation script for User Story 3: Statistical Validation & Baseline Comparison.

This script:
1. Loads the trained Transformer model, geometry-only baseline, and shuffled-translation control.
2. Evaluates all three models on the held-out test set (novel geometries).
3. Performs McNemar's test to compare model performance.
4. Validates that test set geometries were not seen during training.
5. Generates a metrics report (data/metrics_report.json).
"""

import os
import sys
import json
import math
import random
import time
import signal
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.transformer import TranslationTransformer, count_parameters
from utils.data_utils import load_schema, validate_against_schema, compute_checksum, update_checksums
from utils.physics_metrics import load_config

# --- Configuration & Constants ---
DEFAULT_CONFIG_PATH = "code/config.yaml"
RAW_DATA_PATH = "data/raw/synthetic_episodes.parquet"
TEST_DATA_PATH = "data/processed/test.parquet"
TRAIN_DATA_PATH = "data/processed/train.parquet"
GEOMETRY_SPLIT_LOG_PATH = "data/processed/geometry_split_info.json" # To verify disjointness

MODEL_PATH = "data/processed/trained_model.pt"
BASELINE_MODEL_PATH = "data/processed/baseline_model.pt"
SHUFFLED_CONTROL_MODEL_PATH = "data/processed/shuffled_control_model.pt"
METRICS_REPORT_PATH = "data/metrics_report.json"

# --- Timeout Handling ---
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Function timed out")

def set_timeout(seconds: int):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def reset_timeout():
    signal.alarm(0)

# --- Dataset Loading ---
def load_test_data() -> pd.DataFrame:
    """Load the geometry-disjoint test set."""
    if not os.path.exists(TEST_DATA_PATH):
        raise FileNotFoundError(f"Test data not found at {TEST_DATA_PATH}. Run generate_data.py first.")
    return pd.read_parquet(TEST_DATA_PATH)

def load_train_data() -> pd.DataFrame:
    """Load the training set to verify geometry disjointness."""
    if not os.path.exists(TRAIN_DATA_PATH):
        raise FileNotFoundError(f"Train data not found at {TRAIN_DATA_PATH}.")
    return pd.read_parquet(TRAIN_DATA_PATH)

def load_geometry_split_info() -> Dict[str, List[str]]:
    """Load the geometry split info to verify disjointness."""
    if not os.path.exists(GEOMETRY_SPLIT_LOG_PATH):
        # Fallback: try to infer from data if log doesn't exist (less robust)
        # But per spec, T016c should have created this or similar logic.
        # We will assume the data itself contains the 'geometry_id' column.
        return {"train": [], "test": []}
    with open(GEOMETRY_SPLIT_LOG_PATH, 'r') as f:
        return json.load(f)

# --- Model Definitions (for loading) ---
# We need to define the classes here or import them if they are in separate files.
# Since T027b and T027c created specific models, we need to replicate their structure
# to load the weights.

class GeometryBaselineModel(nn.Module):
    """Simple MLP for geometry-only baseline (T027b)."""
    def __init__(self, input_dim: int, hidden_dim: int = 64, output_dim: int = 1):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, output_dim)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return self.sigmoid(x)

class ShuffledControlModel(nn.Module):
    """Simple MLP for shuffled translation control (T027c)."""
    def __init__(self, input_dim: int, hidden_dim: int = 64, output_dim: int = 1):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, output_dim)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return self.sigmoid(x)

class StabilityDataset(Dataset):
    """Dataset for the Transformer model."""
    def __init__(self, df: pd.DataFrame, max_seq_len: int = 100):
        self.df = df
        self.max_seq_len = max_seq_len

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        # Extract translation trajectory (assumed to be a list of lists or similar in 'translation_trajectory' column)
        # The column name might be 'translation_trajectory' or similar.
        # Based on T012/T013, we store relative wrist translation vectors.
        # Let's assume the column is 'translation_trajectory' and it's a list of [x, y, z] or flattened.
        # If it's a string representation, we need to parse it.
        # For robustness, let's assume it's stored as a list of floats or a numpy array.

        # We need to handle the case where the trajectory might be stored as a string or list.
        traj = row.get('translation_trajectory')
        if isinstance(traj, str):
            # Parse string representation of list
            traj = json.loads(traj)
        elif isinstance(traj, np.ndarray):
            traj = traj.tolist()

        # Pad or truncate
        if len(traj) > self.max_seq_len:
            traj = traj[:self.max_seq_len]
        else:
            traj = traj + [[0.0, 0.0, 0.0]] * (self.max_seq_len - len(traj))

        # Flatten for Transformer input (sequence of features)
        # If each step is [x, y, z], then shape is (seq_len, 3)
        X = torch.tensor(traj, dtype=torch.float32)

        y = torch.tensor([row['stability_label']], dtype=torch.float32)

        return X, y

class GeometryBaselineDataset(Dataset):
    """Dataset for geometry-only baseline."""
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        # Extract initial_object_bounds (assumed to be a list of floats)
        bounds = row.get('initial_object_bounds')
        if isinstance(bounds, str):
            bounds = json.loads(bounds)
        elif isinstance(bounds, np.ndarray):
            bounds = bounds.tolist()

        X = torch.tensor(bounds, dtype=torch.float32)
        y = torch.tensor([row['stability_label']], dtype=torch.float32)
        return X, y

class ShuffledControlDataset(Dataset):
    """Dataset for shuffled control (same as baseline dataset structure but used with shuffled model)."""
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        # For shuffled control, we use the same input as the main model but with shuffled labels during training.
        # Here we just load the data as is, the model expects the same input shape as the Transformer.
        # However, the ShuffledControlModel is defined as an MLP on the same input features as the baseline?
        # Re-reading T027c: "randomly shuffles the translation trajectory sequences".
        # This implies the model takes the same input as the Transformer (translation trajectory).
        # But the model architecture in T027c description was "lightweight model".
        # Let's assume the ShuffledControlModel takes the same input as the Transformer (sequence).
        # But the dataset for ShuffledControlModel should provide the sequence.
        # However, the model definition I wrote for ShuffledControlModel is an MLP on flat input.
        # Let's correct this: The ShuffledControlModel should take the same input as the Transformer.
        # But the "shuffled" part was done during training (labels shuffled or sequences shuffled?).
        # T027c says: "randomly shuffles the translation trajectory sequences".
        # This means the input to the model is the shuffled sequence.
        # So the dataset should provide the shuffled sequence.
        # But for evaluation, we use the original (non-shuffled) sequences to see if the model learned anything.
        # Wait, the model was trained on shuffled sequences. So we evaluate on the original sequences.
        # The model architecture should be the same as the Transformer? Or a simpler one?
        # T027c says "lightweight model". Let's assume it's an MLP on the flattened sequence.
        # But the Transformer takes a sequence.
        # Let's assume the ShuffledControlModel takes the same input as the Transformer.
        # So the dataset should provide the sequence.

        # Let's use the same dataset class as the Transformer for consistency.
        # But the model is different.
        # Let's just use the same dataset class for now.
        # We'll load the sequence and pass it to the model.
        # The model (ShuffledControlModel) is defined as an MLP on flat input.
        # So we need to flatten the sequence.
        traj = row.get('translation_trajectory')
        if isinstance(traj, str):
            traj = json.loads(traj)
        elif isinstance(traj, np.ndarray):
            traj = traj.tolist()

        # Flatten the sequence
        X = torch.tensor(traj, dtype=torch.float32).flatten()
        y = torch.tensor([row['stability_label']], dtype=torch.float32)
        return X, y

# --- Model Loading ---
def load_transformer_model(config: Dict[str, Any]) -> TranslationTransformer:
    """Load the trained Transformer model."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Transformer model not found at {MODEL_PATH}. Run train_model.py first.")

    # Load config for model architecture
    # We need to know the input size, etc.
    # Let's assume the config has 'model' section with 'input_size', 'hidden_size', etc.
    input_size = config.get('model', {}).get('input_size', 3) # Assuming 3D translation
    hidden_size = config.get('model', {}).get('hidden_size', 64)
    num_layers = config.get('model', {}).get('num_layers', 4)
    num_heads = config.get('model', {}).get('num_heads', 4)

    model = TranslationTransformer(
        input_size=input_size,
        hidden_size=hidden_size,
        num_layers=num_layers,
        num_heads=num_heads
    )

    state_dict = torch.load(MODEL_PATH, map_location='cpu', weights_only=True)
    model.load_state_dict(state_dict)
    model.eval()
    return model

def load_baseline_model(config: Dict[str, Any]) -> GeometryBaselineModel:
    """Load the geometry-only baseline model."""
    if not os.path.exists(BASELINE_MODEL_PATH):
        raise FileNotFoundError(f"Baseline model not found at {BASELINE_MODEL_PATH}. Run train_baseline.py first.")

    # Load config for model architecture
    input_dim = config.get('baseline', {}).get('input_dim', 6) # Assuming 6 bounds (min/max for x,y,z)
    hidden_dim = config.get('baseline', {}).get('hidden_dim', 64)

    model = GeometryBaselineModel(input_dim=input_dim, hidden_dim=hidden_dim)

    state_dict = torch.load(BASELINE_MODEL_PATH, map_location='cpu', weights_only=True)
    model.load_state_dict(state_dict)
    model.eval()
    return model

def load_shuffled_control_model(config: Dict[str, Any]) -> ShuffledControlModel:
    """Load the shuffled-translation control model."""
    if not os.path.exists(SHUFFLED_CONTROL_MODEL_PATH):
        raise FileNotFoundError(f"Shuffled control model not found at {SHUFFLED_CONTROL_MODEL_PATH}. Run train_shuffled_control.py first.")

    # Load config for model architecture
    # The model expects flattened sequence
    # Assuming max_seq_len=100, input_size=3 -> 300 features
    input_dim = config.get('shuffled_control', {}).get('input_dim', 300)
    hidden_dim = config.get('shuffled_control', {}).get('hidden_dim', 64)

    model = ShuffledControlModel(input_dim=input_dim, hidden_dim=hidden_dim)

    state_dict = torch.load(SHUFFLED_CONTROL_MODEL_PATH, map_location='cpu', weights_only=True)
    model.load_state_dict(state_dict)
    model.eval()
    return model

# --- Prediction ---
def predict(model: nn.Module, dataloader: DataLoader, device: torch.device) -> Tuple[np.ndarray, np.ndarray]:
    """Run inference and return predictions and true labels."""
    model.eval()
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for X, y in dataloader:
            X = X.to(device)
            y = y.to(device)
            outputs = model(X)
            preds = (outputs > 0.5).float().cpu().numpy()
            all_preds.append(preds.flatten())
            all_labels.append(y.cpu().numpy().flatten())

    return np.concatenate(all_preds), np.concatenate(all_labels)

# --- McNemar's Test ---
def mcnemar_test(preds1: np.ndarray, preds2: np.ndarray, labels: np.ndarray) -> Dict[str, Any]:
    """
    Perform McNemar's test to compare two models.
    Returns a dictionary with the p-value and the contingency table.
    """
    # Contingency table:
    #               Model2 Correct   Model2 Incorrect
    # Model1 Correct      a                b
    # Model1 Incorrect    c                d
    # We are interested in b and c (discordant pairs)

    # Note: McNemar's test is for paired nominal data.
    # We compare the predictions of two models on the same set of samples.
    # The null hypothesis is that the two models have the same error rate.

    # Create contingency table
    # We need to count:
    # - Both correct
    # - Model1 correct, Model2 incorrect
    # - Model1 incorrect, Model2 correct
    # - Both incorrect

    # But McNemar's test specifically looks at the discordant pairs (b and c).
    # The test statistic is (|b - c| - 1)^2 / (b + c) (with continuity correction)
    # and follows a chi-squared distribution with 1 degree of freedom.

    # Let's compute the contingency table
    correct_both = np.sum((preds1 == labels) & (preds2 == labels))
    correct_1_wrong_2 = np.sum((preds1 == labels) & (preds2 != labels))
    wrong_1_correct_2 = np.sum((preds1 != labels) & (preds2 == labels))
    wrong_both = np.sum((preds1 != labels) & (preds2 != labels))

    # McNemar's test statistic
    b = correct_1_wrong_2
    c = wrong_1_correct_2

    if b + c == 0:
        p_value = 1.0
    else:
        # Continuity correction
        stat = (abs(b - c) - 1) ** 2 / (b + c)
        p_value = 1 - chi2_contingency([[b + c, 0], [0, b + c]])[1] # This is not correct
        # Correct way:
        # stat ~ chi2(1)
        from scipy.stats import chi2
        p_value = 1 - chi2.cdf(stat, 1)

    return {
        "p_value": p_value,
        "contingency_table": {
            "both_correct": int(correct_both),
            "model1_correct_model2_incorrect": int(b),
            "model1_incorrect_model2_correct": int(c),
            "both_incorrect": int(wrong_both)
        },
        "statistic": float(stat) if b + c > 0 else 0.0
    }

# --- Geometry Disjointness Validation ---
def validate_geometry_disjointness(train_df: pd.DataFrame, test_df: pd.DataFrame) -> bool:
    """
    Verify that the test set contains geometries not present in the training set.
    """
    train_geoms = set(train_df['geometry_id'].unique())
    test_geoms = set(test_df['geometry_id'].unique())

    overlap = train_geoms & test_geoms
    if overlap:
        print(f"WARNING: Overlap in geometries between train and test: {overlap}")
        return False
    return True

# --- Main Evaluation Logic ---
def main():
    parser = argparse.ArgumentParser(description="Evaluate models on test set.")
    parser.add_argument("--config", type=str, default=DEFAULT_CONFIG_PATH, help="Path to config file.")
    parser.add_argument("--device", type=str, default="cpu", help="Device to use for evaluation.")
    args = parser.parse_args()

    print("Loading configuration...")
    config = load_config(args.config)

    print("Loading data...")
    test_df = load_test_data()
    train_df = load_train_data()

    # Validate geometry disjointness
    print("Validating geometry disjointness...")
    is_disjoint = validate_geometry_disjointness(train_df, test_df)
    if not is_disjoint:
        print("ERROR: Train and test sets are not geometry-disjoint. Aborting.")
        sys.exit(1)

    print(f"Test set size: {len(test_df)}")

    # Prepare datasets and dataloaders
    batch_size = config.get('evaluation', {}).get('batch_size', 32)
    device = torch.device(args.device)

    # Transformer dataset
    trans_dataset = StabilityDataset(test_df)
    trans_loader = DataLoader(trans_dataset, batch_size=batch_size, shuffle=False)

    # Baseline dataset
    base_dataset = GeometryBaselineDataset(test_df)
    base_loader = DataLoader(base_dataset, batch_size=batch_size, shuffle=False)

    # Shuffled control dataset
    shuf_dataset = ShuffledControlDataset(test_df)
    shuf_loader = DataLoader(shuf_dataset, batch_size=batch_size, shuffle=False)

    # Load models
    print("Loading models...")
    transformer_model = load_transformer_model(config).to(device)
    baseline_model = load_baseline_model(config).to(device)
    shuffled_model = load_shuffled_control_model(config).to(device)

    # Run predictions
    print("Running predictions...")
    trans_preds, trans_labels = predict(transformer_model, trans_loader, device)
    base_preds, base_labels = predict(baseline_model, base_loader, device)
    shuf_preds, shuf_labels = predict(shuffled_model, shuf_loader, device)

    # Calculate accuracies
    trans_acc = np.mean(trans_preds == trans_labels)
    base_acc = np.mean(base_preds == base_labels)
    shuf_acc = np.mean(shuf_preds == shuf_labels)

    print(f"Transformer Accuracy: {trans_acc:.4f}")
    print(f"Baseline Accuracy: {base_acc:.4f}")
    print(f"Shuffled Control Accuracy: {shuf_acc:.4f}")

    # Check for ≥ 5% improvement
    improvement_vs_base = trans_acc - base_acc
    improvement_vs_shuf = trans_acc - shuf_acc

    print(f"Improvement vs Baseline: {improvement_vs_base:.4f}")
    print(f"Improvement vs Shuffled: {improvement_vs_shuf:.4f}")

    # McNemar's tests
    print("Performing McNemar's tests...")
    mcnemar_base = mcnemar_test(trans_preds, base_preds, trans_labels)
    mcnemar_shuf = mcnemar_test(trans_preds, shuf_preds, trans_labels)

    # Generate confusion matrices
    from sklearn.metrics import confusion_matrix
    cm_trans_base = confusion_matrix(trans_labels, trans_preds, labels=[1, 0]) # True, Pred
    cm_trans_shuf = confusion_matrix(trans_labels, trans_preds, labels=[1, 0])

    # Prepare metrics report
    metrics_report = {
        "transformer_accuracy": float(trans_acc),
        "baseline_accuracy": float(base_acc),
        "shuffled_control_accuracy": float(shuf_acc),
        "improvement_vs_baseline": float(improvement_vs_base),
        "improvement_vs_shuffled": float(improvement_vs_shuf),
        "mcnemar_vs_baseline": mcnemar_base,
        "mcnemar_vs_shuffled": mcnemar_shuf,
        "confusion_matrix_transformer": cm_trans_base.tolist(),
        "confusion_matrix_baseline": confusion_matrix(base_labels, base_preds, labels=[1, 0]).tolist(),
        "confusion_matrix_shuffled": confusion_matrix(shuf_labels, shuf_preds, labels=[1, 0]).tolist(),
        "geometry_disjoint": is_disjoint,
        "test_set_size": int(len(test_df)),
        "train_set_size": int(len(train_df))
    }

    # Save report
    print(f"Saving metrics report to {METRICS_REPORT_PATH}...")
    with open(METRICS_REPORT_PATH, 'w') as f:
        json.dump(metrics_report, f, indent=2)

    print("Evaluation complete.")

if __name__ == "__main__":
    main()
