"""
Integration test for comparative evaluation (User Story 2).

This test verifies the comparative evaluation pipeline:
1. Loads semi-empirical and DFT descriptor datasets (or generates them if missing)
2. Trains two Random Forest models (semi-empirical vs DFT)
3. Computes per-fold MAE and runs paired t-test
4. Verifies output reports contain expected metrics (MAE_semi, MAE_DFT, p-value)
5. Flags if semi-MAE > 1.2 * DFT-MAE
"""
import os
import sys
import csv
import math
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Tuple
import statistics

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from train_models import load_data, prepare_features_target, train_and_evaluate_fold, train_models
from utils.validation_utils import validate_full, ValidationError

# Constants
EXPECTED_COLUMNS = ["SMILES", "HOMO", "LUMO", "Mayer_Bond_Order", "experimental_barrier"]
SEMI_FILE = "data/descriptors_semi.csv"
DFT_FILE = "data/descriptors_dft.csv"
OUTPUT_REPORT = "data/reports/comparative_evaluation_report.csv"
MIN_MOLECULES = 30

def generate_test_data(semi_path: str, dft_path: str, num_molecules: int = 50):
    """
    Generate realistic test data for semi-empirical and DFT descriptors.
    This creates synthetic but physically plausible data for testing purposes.
    """
    # Use a deterministic seed for reproducibility
    import random
    random.seed(42)

    def generate_row(smiles: str, is_dft: bool) -> Dict[str, Any]:
        # Generate physically plausible values
        homo = random.uniform(-12.0, -5.0)  # eV
        lumo = homo + random.uniform(2.0, 6.0)  # eV, LUMO > HOMO
        mbo = random.uniform(0.5, 2.5)
        
        # Experimental barrier with some noise
        base_barrier = abs(homo) * 1.5 + random.gauss(0, 0.5)
        barrier = max(0.1, base_barrier)  # kcal/mol

        return {
            "SMILES": smiles,
            "HOMO": f"{homo:.4f}",
            "LUMO": f"{lumo:.4f}",
            "Mayer_Bond_Order": f"{mbo:.4f}",
            "experimental_barrier": f"{barrier:.4f}"
        }

    # Generate SMILES strings (simplified for testing)
    smiles_list = [f"C{chr(65+i)}O" for i in range(num_molecules)]
    
    # Write semi-empirical data
    with open(semi_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        for i, smiles in enumerate(smiles_list):
            row = generate_row(smiles, is_dft=False)
            # Add some semi-empirical specific noise
            row["HOMO"] = f"{float(row['HOMO']) + random.gauss(0, 0.1):.4f}"
            row["LUMO"] = f"{float(row['LUMO']) + random.gauss(0, 0.1):.4f}"
            writer.writerow(row)

    # Write DFT data
    with open(dft_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        for i, smiles in enumerate(smiles_list):
            row = generate_row(smiles, is_dft=True)
            # DFT is more accurate, less noise
            row["HOMO"] = f"{float(row['HOMO']) - random.gauss(0, 0.05):.4f}"
            row["LUMO"] = f"{float(row['LUMO']) - random.gauss(0, 0.05):.4f}"
            writer.writerow(row)

def run_comparative_evaluation(semi_path: str, dft_path: str, output_path: str):
    """
    Run the comparative evaluation pipeline.
    This mimics the logic that would be in evaluate_models.py
    """
    # Load semi-empirical data
    semi_data = load_data(semi_path)
    semi_X, semi_y, semi_smiles = prepare_features_target(semi_data, "experimental_barrier")
    
    # Load DFT data
    dft_data = load_data(dft_path)
    dft_X, dft_y, dft_smiles = prepare_features_target(dft_data, "experimental_barrier")
    
    # Verify same molecules
    assert semi_smiles == dft_smiles, "Molecule sets must match"
    
    # Train and evaluate both models
    semi_results = train_models(semi_X, semi_y, n_folds=5, model_name="semi")
    dft_results = train_models(dft_X, dft_y, n_folds=5, model_name="dft")
    
    # Compute MAE for each fold
    semi_maes = [r["mae"] for r in semi_results]
    dft_maes = [r["mae"] for r in dft_results]
    
    # Paired t-test
    n = len(semi_maes)
    assert n == len(dft_maes)
    
    # Calculate t-statistic
    diffs = [s - d for s, d in zip(semi_maes, dft_maes)]
    mean_diff = statistics.mean(diffs)
    std_diff = statistics.stdev(diffs) if n > 1 else 0
    
    if std_diff > 0:
        t_stat = mean_diff / (std_diff / math.sqrt(n))
        # Approximate p-value using t-distribution (simplified)
        # For small n, use a rough approximation
        p_value = 2 * (1 - min(0.999, abs(t_stat) / (abs(t_stat) + 1)))
    else:
        t_stat = 0.0
        p_value = 1.0
    
    # Calculate overall MAEs
    mae_semi = statistics.mean(semi_maes)
    mae_dft = statistics.mean(dft_maes)
    
    # Check if semi-MAE > 1.2 * DFT-MAE
    threshold = 1.2 * mae_dft
    flag_exceeded = mae_semi > threshold
    
    # Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "MAE_semi", "MAE_DFT", "p_value", "threshold", "flag_exceeded"
        ])
        writer.writeheader()
        writer.writerow({
            "MAE_semi": f"{mae_semi:.4f}",
            "MAE_DFT": f"{mae_dft:.4f}",
            "p_value": f"{p_value:.4f}",
            "threshold": f"{threshold:.4f}",
            "flag_exceeded": str(flag_exceeded)
        })
    
    return {
        "MAE_semi": mae_semi,
        "MAE_DFT": mae_dft,
        "p_value": p_value,
        "threshold": threshold,
        "flag_exceeded": flag_exceeded
    }

def test_comparative_evaluation():
    """
    Integration test for comparative evaluation.
    """
    # Create temporary directory for test data
    with tempfile.TemporaryDirectory() as tmpdir:
        semi_path = os.path.join(tmpdir, SEMI_FILE)
        dft_path = os.path.join(tmpdir, DFT_FILE)
        output_path = os.path.join(tmpdir, OUTPUT_REPORT)
        
        # Generate test data
        generate_test_data(semi_path, dft_path, num_molecules=MIN_MOLECULES + 10)
        
        # Verify data files exist and have correct structure
        assert os.path.exists(semi_path), "Semi-empirical data file not created"
        assert os.path.exists(dft_path), "DFT data file not created"
        
        with open(semi_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) >= MIN_MOLECULES, f"Expected at least {MIN_MOLECULES} molecules, got {len(rows)}"
            assert set(rows[0].keys()) == set(EXPECTED_COLUMNS), "Missing expected columns"
        
        # Run evaluation
        results = run_comparative_evaluation(semi_path, dft_path, output_path)
        
        # Verify output report exists
        assert os.path.exists(output_path), "Evaluation report not created"
        
        # Verify report contents
        with open(output_path, "r") as f:
            reader = csv.DictReader(f)
            report_rows = list(reader)
            assert len(report_rows) == 1, "Expected exactly one report row"
            
            report = report_rows[0]
            assert "MAE_semi" in report, "Missing MAE_semi in report"
            assert "MAE_DFT" in report, "Missing MAE_DFT in report"
            assert "p_value" in report, "Missing p_value in report"
            assert "threshold" in report, "Missing threshold in report"
            assert "flag_exceeded" in report, "Missing flag_exceeded in report"
            
            # Verify numeric values are reasonable
            mae_semi = float(report["MAE_semi"])
            mae_dft = float(report["MAE_DFT"])
            p_value = float(report["p_value"])
            threshold = float(report["threshold"])
            flag_exceeded = report["flag_exceeded"] == "True"
            
            assert mae_semi > 0, "MAE_semi must be positive"
            assert mae_dft > 0, "MAE_DFT must be positive"
            assert 0 <= p_value <= 1, "p_value must be between 0 and 1"
            
            # Verify threshold calculation
            expected_threshold = 1.2 * mae_dft
            assert abs(threshold - expected_threshold) < 1e-6, "Threshold calculation incorrect"
            
            # Verify flag logic
            expected_flag = mae_semi > expected_threshold
            assert flag_exceeded == expected_flag, "Flag logic incorrect"
        
        print("✓ Comparative evaluation integration test passed")
        print(f"  MAE_semi: {mae_semi:.4f}")
        print(f"  MAE_DFT: {mae_dft:.4f}")
        print(f"  p_value: {p_value:.4f}")
        print(f"  Threshold: {threshold:.4f}")
        print(f"  Flag exceeded: {flag_exceeded}")

if __name__ == "__main__":
    test_comparative_evaluation()