import os
import sys
import hashlib
import shutil
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import yaml

# Add parent to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def archive_real_data(data_dir: Path, archive_dir: Path) -> None:
    """Archive real data files."""
    archive_dir.mkdir(parents=True, exist_ok=True)
    for file_path in data_dir.glob("*"):
        if file_path.is_file():
            shutil.copy2(file_path, archive_dir / file_path.name)
    logger.info(f"Archived real data to {archive_dir}")

def generate_synthetic_ebird_data(output_path: Path, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic eBird data matching the schema."""
    np.random.seed(seed)
    n_rows = 10000
    
    data = {
        "species": np.random.choice(["Turdus migratorius", "Setophaga ruticilla", "Cardinalis cardinalis"], n_rows),
        "lat": np.random.uniform(25, 50, n_rows),
        "lon": np.random.uniform(-125, -70, n_rows),
        "date": pd.date_range("2020-01-01", periods=n_rows, freq="D").to_series().sample(n_rows).reset_index(drop=True),
        "count": np.random.poisson(5, n_rows),
        "checklist_id": [f"CHECK_{i}" for i in range(n_rows)]
    }
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df.to_csv(output_path, index=False)
    logger.info(f"Generated synthetic eBird data: {output_path}")
    return df

def generate_synthetic_climate_data(output_path: Path, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic climate data matching the schema."""
    np.random.seed(seed)
    n_rows = 5000
    
    data = {
        "lat": np.random.uniform(25, 50, n_rows),
        "lon": np.random.uniform(-125, -70, n_rows),
        "temp": np.random.normal(15, 5, n_rows),
        "week": np.random.randint(1, 53, n_rows),
        "precip": np.random.exponential(2, n_rows)
    }
    df = pd.DataFrame(data)
    df.to_parquet(output_path, index=False)
    logger.info(f"Generated synthetic climate data: {output_path}")
    return df

def write_synthetic_data(data_dir: Path, seed: int = 42) -> None:
    """Write synthetic data files."""
    data_dir.mkdir(parents=True, exist_ok=True)
    ebird_path = data_dir / "synthetic_ebird.csv"
    climate_path = data_dir / "synthetic_climate.parquet"
    
    generate_synthetic_ebird_data(ebird_path, seed)
    generate_synthetic_climate_data(climate_path, seed)

def write_state_file(state_path: Path, artifact_hashes: dict, updated_at: str) -> None:
    """Write state file with checksums."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_data = {
        "artifact_hashes": artifact_hashes,
        "updated_at": updated_at
    }
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f)
    logger.info(f"State file written: {state_path}")

def check_real_data_available(data_dir: Path) -> bool:
    """Check if real data files exist."""
    ebird_path = data_dir / "ebird" / "ebird_data.csv"
    climate_path = data_dir / "climate" / "climate_data.parquet"
    return ebird_path.exists() and climate_path.exists()

def ensure_data_available(data_dir: Path, state_path: Path, seed: int = 42) -> None:
    """Ensure data is available, generating synthetic if needed in dev mode."""
    if check_real_data_available(data_dir):
        logger.info("Real data found. Proceeding with real data.")
        archive_real_data(data_dir, data_dir / "archive")
        # Compute checksums for real data
        artifact_hashes = {}
        for f in data_dir.glob("ebird/*.csv"):
            artifact_hashes[f.name] = compute_sha256(f)
        for f in data_dir.glob("climate/*.parquet"):
            artifact_hashes[f.name] = compute_sha256(f)
        write_state_file(state_path, artifact_hashes, "real_data")
    else:
        logger.warning("Real data not found. Generating synthetic data for development.")
        write_synthetic_data(data_dir, seed)
        # Compute checksums for synthetic data
        artifact_hashes = {}
        for f in data_dir.glob("synthetic_ebird.csv"):
            artifact_hashes[f.name] = compute_sha256(f)
        for f in data_dir.glob("synthetic_climate.parquet"):
            artifact_hashes[f.name] = compute_sha256(f)
        write_state_file(state_path, artifact_hashes, "synthetic_data")

def run_download_pipeline(data_dir: Path = None, state_dir: Path = None, seed: int = 42) -> None:
    """Main download pipeline entry point."""
    if data_dir is None:
        data_dir = project_root / "data" / "raw"
    if state_dir is None:
        state_dir = project_root / "state"
    
    state_path = state_dir / "projects" / "PROJ-132-statistical-analysis-of-publicly-availab.yaml"
    ensure_data_available(data_dir, state_path, seed)
