import os
import sys
import hashlib
import shutil
import logging
from pathlib import Path
from typing import Dict, Any

from src.lib.config import get_config

logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def check_real_data_available(mode: str = "production") -> bool:
    """Check if real data files exist in expected locations."""
    config = get_config()
    raw_dir = config.DATA_DIR / "raw"
    
    ebird_path = raw_dir / "ebird" / "ebird_data.csv"
    climate_path = raw_dir / "climate" / "climate_data.parquet"
    
    return ebird_path.exists() and climate_path.exists()

def ensure_data_available(mode: str = "production") -> None:
    """
    T005 Implementation: Ensure data is available.
    Production Mode: Abort if real data missing.
    Development Mode: Generate synthetic data if missing.
    """
    config = get_config()
    raw_dir = config.DATA_DIR / "raw"
    ebird_path = raw_dir / "ebird" / "ebird_data.csv"
    climate_path = raw_dir / "climate" / "climate_data.parquet"
    
    # Create directories
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "ebird").mkdir(exist_ok=True)
    (raw_dir / "climate").mkdir(exist_ok=True)

    if check_real_data_available():
        logger.info("Real data found. Proceeding.")
        return

    if mode == "production":
        logger.error("Real data required for production run. Set --mode=synthetic for development only.")
        # SC-005: Fail loudly
        sys.exit(1)
    
    # Development/Synthetic Mode
    logger.info("Real data missing. Generating synthetic data (Development Mode)...")
    generate_synthetic_ebird_data(ebird_path)
    generate_synthetic_climate_data(climate_path)
    logger.info("Synthetic data generated successfully.")

def generate_synthetic_ebird_data(path: Path) -> None:
    """Generate synthetic eBird data matching schema."""
    import numpy as np
    import pandas as pd
    
    np.random.seed(42)
    n_rows = 10000
    
    data = {
        'species': np.random.choice(['Turdus migratorius', 'Setophaga ruticilla', 'Passer domesticus'], n_rows),
        'lat': np.random.uniform(25, 48, n_rows),
        'lon': np.random.uniform(-125, -70, n_rows),
        'date': pd.date_range('2023-03-01', periods=n_rows, freq='1min'),
        'count': np.random.poisson(5, n_rows),
        'checklist_id': [f'chk_{i}' for i in range(n_rows)]
    }
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)

def generate_synthetic_climate_data(path: Path) -> None:
    """Generate synthetic climate data matching schema."""
    import numpy as np
    import pandas as pd
    
    np.random.seed(42)
    n_rows = 5000
    
    data = {
        'lat': np.random.uniform(25, 48, n_rows),
        'lon': np.random.uniform(-125, -70, n_rows),
        'temp': np.random.normal(15, 5, n_rows),
        'week': np.random.randint(1, 53, n_rows),
        'precip': np.random.exponential(2, n_rows)
    }
    df = pd.DataFrame(data)
    df.to_parquet(path)

def run_download_pipeline(mode: str = "production") -> None:
    """Orchestrate download/synthesis."""
    ensure_data_available(mode=mode)
    logger.info("Download pipeline complete.")
