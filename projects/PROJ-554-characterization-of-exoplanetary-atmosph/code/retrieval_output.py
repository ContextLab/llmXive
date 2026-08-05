import os
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd

from config import get_config
from utils import setup_logging, PipelineError
from data_models import RetrievalResult
from retrieval_output_schema import map_retrieval_result_to_schema, get_schema_columns

logger = logging.getLogger(__name__)

def process_retrieval_results(retrieval_results: List[RetrievalResult], output_path: Optional[str] = None) -> str:
    """
    Process a list of RetrievalResult objects and save them to a CSV file.

    Args:
        retrieval_results: List of RetrievalResult objects from the retrieval pipeline.
        output_path: Optional path for the output CSV. If None, uses config default.

    Returns:
        The path to the generated CSV file.

    Raises:
        PipelineError: If no results are provided or if the output directory cannot be created.
    """
    config = get_config()
    if output_path is None:
        output_path = str(config.output_dir / "processed" / "retrieval_results.csv")

    output_file = Path(output_path)
    output_dir = output_file.parent

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")

    if not retrieval_results:
        logger.warning("No retrieval results provided. Creating an empty CSV with schema headers.")
        schema_columns = get_schema_columns()
        df_empty = pd.DataFrame(columns=schema_columns)
        df_empty.to_csv(output_file, index=False)
        logger.info(f"Created empty retrieval results CSV at: {output_file}")
        return str(output_file)

    logger.info(f"Processing {len(retrieval_results)} retrieval results...")

    mapped_rows = []
    for i, result in enumerate(retrieval_results):
        try:
            mapped_row = map_retrieval_result_to_schema(result)
            mapped_rows.append(mapped_row)
        except Exception as e:
            logger.error(f"Failed to map retrieval result {i} (Planet: {result.planet_name}): {e}")
            # We do not halt; we log and skip, or we could insert a row with error flags if schema allows.
            # For now, we skip to ensure the CSV is valid.
            continue

    if not mapped_rows:
        logger.warning("No valid rows could be mapped. Creating empty CSV.")
        schema_columns = get_schema_columns()
        df_empty = pd.DataFrame(columns=schema_columns)
        df_empty.to_csv(output_file, index=False)
        return str(output_file)

    df = pd.DataFrame(mapped_rows)
    
    # Ensure numeric columns are numeric (handle potential string representations from data models)
    numeric_cols = ['log10_water_abundance', 'uncertainty_1sigma', 'snr', 'resolution']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df.to_csv(output_file, index=False)
    logger.info(f"Successfully saved {len(df)} retrieval results to {output_file}")
    return str(output_file)

def main():
    """
    Main entry point for the retrieval output generation.
    This function is designed to be called by a pipeline orchestrator.
    For demonstration, it attempts to load results from a mock source or config.
    In a real pipeline, results would be passed from the retrieval step.
    """
    setup_logging()
    config = get_config()
    
    # In a real scenario, this list would come from the output of T018b/T019
    # Since we cannot run the full retrieval here without real data files,
    # we assume the pipeline has populated a temporary state or we are called
    # with an argument. For this task, we ensure the function exists and works
    # if passed data.
    
    # To satisfy the requirement of "producing real outputs" when run:
    # We will check if there are existing metadata files to simulate a pipeline run
    # if the full retrieval hasn't happened, BUT the constraint says "NO synthetic".
    # Therefore, we must rely on the fact that T019/T018b would have populated
    # a list of RetrievalResult objects.
    
    # Since we are implementing T020 (output generation) and T019 (upper limits)
    # and T018b (retrieval) are marked done, we assume the data exists in memory
    # or a temporary file. However, to make this script runnable and produce
    # the artifact as requested, we must have input data.
    
    # Given the constraints of this environment (no real data files on disk yet
    # from previous tasks in this specific execution context), we cannot "fake" data.
    # But the task requires the script to run and write the file.
    # The correct approach for a pipeline step is to read from a previous step's output
    # or receive data via CLI/Env.
    
    # We will implement a check: if data/processed/retrieval_intermediate.json exists, load it.
    # If not, we raise an error to fail loudly, as per constraint #9.
    
    input_json_path = config.data_dir / "processed" / "retrieval_intermediate.json"
    
    if not input_json_path.exists():
        logger.error(f"Input file not found: {input_json_path}. "
                     "The retrieval step (T018b/T019) must run first and save intermediate results.")
        raise FileNotFoundError(f"Required input file missing: {input_json_path}")

    # Load intermediate results (assumed to be a JSON list of dicts)
    try:
        raw_data = pd.read_json(input_json_path)
        # Convert to RetrievalResult objects
        results = []
        for _, row in raw_data.iterrows():
            result = RetrievalResult(
                planet_name=row['planet_name'],
                equilibrium_temp=row.get('equilibrium_temp'),
                water_mixing_ratio=row.get('water_mixing_ratio'),
                uncertainty=row.get('uncertainty'),
                is_censored=bool(row.get('is_censored', False)),
                snr=row.get('snr'),
                resolution=row.get('resolution'),
                convergence_status=row.get('convergence_status', 'unknown')
            )
            results.append(result)
    except Exception as e:
        logger.error(f"Failed to load intermediate results: {e}")
        raise

    output_path = process_retrieval_results(results)
    logger.info(f"Task T020 completed. Output written to {output_path}")

if __name__ == "__main__":
    main()
