"""
Helper script to execute the T013 integration test directly without pytest discovery overhead,
useful for CI or manual verification of the pipeline flow.
"""
import sys
import os
from pathlib import Path
import tempfile
import shutil
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.preprocess import run_preprocessing_pipeline
from src.utils.logging import get_logger

logger = get_logger(__name__)

def create_mock_ebird_data(num_rows: int = 200, seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)
    species_list = ['Turdus migratorius', 'Setophaga ruticilla', 'Catharus ustulatus']
    base_date = datetime(2023, 3, 1)
    
    data = {
        'species': np.random.choice(species_list, num_rows),
        'lat': np.random.uniform(30.0, 50.0, num_rows),
        'lon': np.random.uniform(-120.0, -80.0, num_rows),
        'date': [base_date + timedelta(days=int(d)) for d in np.random.randint(0, 90, num_rows)],
        'count': np.random.randint(1, 50, num_rows),
        'checklist_id': [f'CHK_{i:05d}' for i in range(num_rows)]
    }
    return pd.DataFrame(data)

def create_mock_climate_data(num_cells: int = 10, seed: int = 43) -> pd.DataFrame:
    np.random.seed(seed)
    lats = np.arange(30.0, 50.0, 2.0)
    lons = np.arange(-120.0, -80.0, 2.0)
    grid_cells = [f"{l:.1f}_{lon:.1f}" for l in lats for lon in lons][:num_cells]
    weeks = range(1, 14)
    
    records = []
    for cell in grid_cells:
        for week in weeks:
            records.append({
                'grid_cell': cell,
                'week': week,
                'mean_temperature': np.random.uniform(5.0, 20.0),
                'total_precipitation': np.random.uniform(0.0, 50.0),
                'extreme_weather_index': np.random.uniform(0.0, 1.0)
            })
    return pd.DataFrame(records)

def run_t013_manual_test():
    logger.info("Running T013 Manual Integration Test...")
    
    temp_dir = tempfile.mkdtemp(prefix="t013_manual_")
    temp_path = Path(temp_dir)
    
    try:
        # Setup directory structure
        (temp_path / "data" / "raw" / "ebird_sample").mkdir(parents=True, exist_ok=True)
        (temp_path / "data" / "raw" / "daymet").mkdir(parents=True, exist_ok=True)
        (temp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
        (temp_path / "data" / "interim").mkdir(parents=True, exist_ok=True)
        (temp_path / "logs").mkdir(parents=True, exist_ok=True)
        
        # Write mock data
        ebird_df = create_mock_ebird_data(num_rows=200)
        ebird_file = temp_path / "data" / "raw" / "ebird_sample" / "mock_ebird.parquet"
        ebird_df.to_parquet(ebird_file)
        
        climate_df = create_mock_climate_data(num_cells=10)
        climate_file = temp_path / "data" / "raw" / "daymet" / "mock_daymet.parquet"
        climate_df.to_parquet(climate_file)
        
        species_file = temp_path / "data" / "raw" / "migratory_list.json"
        with open(species_file, 'w') as f:
            json.dump(['Turdus migratorius', 'Setophaga ruticilla', 'Catharus ustulatus'], f)
        
        # Change to temp directory to simulate project root
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        logger.info(f"Running preprocessing pipeline in {temp_dir}...")
        run_preprocessing_pipeline()
        
        output_path = Path("data/processed/preprocessed_data.parquet")
        if not output_path.exists():
            raise FileNotFoundError(f"Pipeline did not produce output at {output_path}")
        
        df = pd.read_parquet(output_path)
        required_cols = ['species', 'grid_cell', 'year', 'week', 'first_arrival_date', 
                         'median_arrival_date', 'stopover_duration', 'mean_temperature', 
                         'total_precipitation', 'extreme_weather_index', 'is_imputed', 'data_quality']
        
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns in output: {missing}")
        
        logger.info("SUCCESS: T013 Integration Test passed.")
        logger.info(f"Output shape: {df.shape}")
        logger.info(f"Columns: {df.columns.tolist()}")
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    run_t013_manual_test()