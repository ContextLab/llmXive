import os
import json
import hashlib
import pandas as pd
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
from statsmodels.stats.power import TTestIndPower

class CriticalValidationError(Exception):
    """Raised when all fetched datasets fail validation (e.g., N < 50)."""
    pass

def load_manifest(manifest_path: str) -> List[Dict[str, Any]]:
    """Load the datasets manifest from a YAML file."""
    with open(manifest_path, 'r') as f:
        data = yaml.safe_load(f)
    return data.get('datasets', [])

def calculate_checksum(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_dataset(url: str, output_path: str) -> bool:
    """Fetch a dataset from a URL and save it to the output path."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return True
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return False

def _record_violation(violations: List[Dict[str, Any]], dataset_name: str, reason: str, extra: Optional[Dict[str, Any]] = None):
    """Helper to append a violation record."""
    record = {"dataset": dataset_name, "reason": reason}
    if extra:
        record.update(extra)
    violations.append(record)

def _read_dataset_file(path: str) -> pd.DataFrame:
    """
    Read a dataset file, handling CSV and Excel formats.
    Returns a pandas DataFrame.
    """
    suffix = Path(path).suffix.lower()
    if suffix in {".xls", ".xlsx"}:
        return pd.read_excel(path)
    else:
        # Attempt CSV read; handle possible single‑column with commas embedded
        df = pd.read_csv(path, header=None)
        if df.shape[1] == 1 and ',' in df.iloc[0, 0]:
            df = pd.read_csv(path, sep=',')
        return df

def validate_dataset(df: pd.DataFrame, dataset_info: Dict[str, Any], violations: List[Dict[str, Any]]) -> bool:
    """
    Validate that the dataset contains continuous or categorical variables
    suitable for t-tests, ANOVA, or chi-squared tests.
    
    Requirements:
    - At least one numeric column (for t-test/ANOVA)
    - At least one categorical column OR target is categorical (for chi-squared)
    - Minimum 50 rows (FR-001)
    - Continuous variables must have variance > 0
    - Categorical variables must have at least 2 unique levels
    
    Returns True if the dataset passes all checks, False otherwise.
    """
    name = dataset_info.get('name', 'Unknown')
    n_rows = len(df)
    is_valid = True

    # Check N >= 50 (FR-001) – record but continue checking
    if n_rows < 50:
        _record_violation(
            violations,
            name,
            "N < 50",
            {"n_rows": n_rows, "threshold": 50, "status": "skipped"}
        )
        print(f"Dataset {name} has fewer than 50 rows ({n_rows}).")
        is_valid = False

    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

    has_numeric = len(numeric_cols) > 0
    has_categorical = len(categorical_cols) > 0

    if not has_numeric and not has_categorical:
        _record_violation(
            violations,
            name,
            "No numeric or categorical columns",
            {"n_rows": n_rows, "status": "skipped"}
        )
        print(f"Dataset {name} has no numeric or categorical columns. Skipping.")
        is_valid = False
        return is_valid  # cannot proceed further

    if not has_numeric:
        print(f"Warning: Dataset {name} has no numeric columns. Chi-squared only.")
    if not has_categorical:
        print(f"Warning: Dataset {name} has no categorical columns. T-test/ANOVA only.")

    # 1) Continuous variables must have variance > 0
    for col in numeric_cols:
        if df[col].var(ddof=0) == 0:
            _record_violation(
                violations,
                name,
                f"Numeric column '{col}' has zero variance",
                {"column": col, "status": "skipped"}
            )
            print(f"Dataset {name}: numeric column '{col}' has zero variance. Skipping.")
            is_valid = False

    # 2) Categorical variables must have at least 2 unique levels
    for col in categorical_cols:
        if df[col].nunique() < 2:
            _record_violation(
                violations,
                name,
                f"Categorical column '{col}' has fewer than 2 unique levels",
                {"column": col, "status": "skipped"}
            )
            print(f"Dataset {name}: categorical column '{col}' has <2 unique levels. Skipping.")
            is_valid = False

    return is_valid

def _compute_theoretical_power(n: int, effect_size: float = 0.5, alpha: float = 0.05) -> float:
    """
    Compute the theoretical power for a two‑sample t‑test given sample size `n`.
    Uses Cohen's d = effect_size.
    """
    analysis = TTestIndPower()
    # Assuming equal group sizes, each group gets n/2 observations
    return analysis.power(effect_size=effect_size, nobs1=n / 2, alpha=alpha, ratio=1.0)

def _serialize_json_safe(obj):
    """
    Helper for json.dump to convert NumPy scalar types to native Python types.
    """
    import numpy as np
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    if isinstance(obj, np.bool_):
        return bool(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def load_datasets(
    manifest_path: str = str(Path('data') / 'manifests' / 'datasets.yaml'),
    data_raw_dir: str = str(Path('data') / 'raw'),
    checksums_path: str = str(Path('data') / 'manifests' / 'checksums.json'),
    results_dir: str = "results"
) -> Dict[str, str]:
    """
    Main entry point to fetch, validate, and save datasets.
    
    Returns:
        Dictionary mapping dataset name to its SHA-256 checksum.
        
    Raises:
        CriticalValidationError: If all fetched datasets fail validation.
    """
    datasets = load_manifest(manifest_path)
    checksums = {}
    violations = []
    power_reports = []

    data_raw_path = Path(data_raw_dir)
    data_raw_path.mkdir(parents=True, exist_ok=True)

    # Ensure results directory exists for validation & power reports
    results_path = Path(results_dir)
    results_path.mkdir(parents=True, exist_ok=True)

    successful_count = 0

    for dataset_info in datasets:
        name = dataset_info['name']
        url = dataset_info['url']
        output_filename = f"{name}.csv" if not url.lower().endswith(('.xls', '.xlsx')) else f"{name}.xls"
        output_path = str(data_raw_path / output_filename)
        
        print(f"Fetching {name} from {url}...")
        if not fetch_dataset(url, output_path):
            print(f"Skipping {name} due to fetch failure.")
            continue
        
        # Load and validate
        try:
            df = _read_dataset_file(output_path)
            
            if not validate_dataset(df, dataset_info, violations):
                # Remove invalid file
                os.remove(output_path)
            else:
                successful_count += 1
                checksum = calculate_checksum(output_path)
                checksums[name] = checksum
                print(f"Saved {name}: {len(df)} rows, {df.shape[1]} columns. Checksum: {checksum[:16]}...")

                # Theoretical power calculation (SC-001)
                power = _compute_theoretical_power(n=len(df))
                power_reports.append({
                    "dataset": name,
                    "n_rows": int(len(df)),
                    "theoretical_power": float(power),
                    "power_warning": bool(power < 0.80)
                })
                
        except Exception as e:
            print(f"Error processing {name}: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)
            violations.append({
                "dataset": name,
                "reason": f"Processing error: {str(e)}",
                "status": "skipped"
            })
            continue

    # Save checksums
    with open(checksums_path, 'w') as f:
        json.dump(checksums, f, indent=2, default=_serialize_json_safe)
    print(f"Checksums saved to {checksums_path}")

    # Write validation report
    validation_report_path = results_path / "validation_report.json"
    report_data = {
        "total_datasets_attempted": len(datasets),
        "successful_datasets": successful_count,
        "violations": violations,
        "report_generated_at": pd.Timestamp.now().isoformat()
    }
    with open(validation_report_path, 'w') as f:
        json.dump(report_data, f, indent=2, default=_serialize_json_safe)
    print(f"Validation report saved to {validation_report_path}")

    # Write power report (T035b)
    power_report_path = results_path / "power_report.json"
    with open(power_report_path, 'w') as f:
        json.dump(power_reports, f, indent=2, default=_serialize_json_safe)
    print(f"Power report saved to {power_report_path}")

    # Critical check: If all fetched datasets failed validation
    if successful_count == 0 and len(datasets) > 0:
        raise CriticalValidationError(
            f"All {len(datasets)} datasets failed validation. "
            f"Violations: {len(violations)}. Pipeline cannot proceed."
        )

    return checksums
