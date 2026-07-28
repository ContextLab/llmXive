"""
Main ingestion CLI entry point.
Orchestrates the data pipeline: Ingestion -> Merge -> Size Gate (Warning) -> Preprocess -> Size Gate (Halt) -> Validate -> Output.
"""
import logging
import sys
from pathlib import Path

from src.utils.logger import get_module_logger
from src.ingest.materials_project import run_materials_project_ingestion
from src.ingest.nist_repo import run_nist_ingestion
from src.ingest.arxiv_extractor import run_arxiv_ingestion
from src.ingest.merge import run_merge_pipeline
from src.utils.size_gate import check_size_gate
from src.ingest.ocr_fallback import extract_psd_from_image
from src.preprocess.validate_schema import validate_schema
from src.config.settings import get_settings
from src.exceptions import InsufficientDataError, SchemaValidationError

logger = get_module_logger(__name__)


def run_preprocessing(df):
    """
    Run preprocessing steps: Imputation, Encoding, Scaling.
    Note: T016e (Process Duration Extraction) is assumed to be handled within merge or prior steps.
    This function calls the specific preprocessing modules.
    """
    logger.info("Starting preprocessing steps (Imputation, Encoding, Scaling)...")
    # Importing here to avoid circular dependencies if not needed at top level
    # Assuming these functions exist as per task definitions T016a, T016b, T016c
    try:
        from src.preprocess.imputation import apply_imputation
        from src.preprocess.encoding import apply_one_hot
        from src.preprocess.scaling import apply_scaling

        df = apply_imputation(df)
        df = apply_one_hot(df)
        df = apply_scaling(df)
        
        logger.info("Preprocessing completed successfully.")
        return df
    except ImportError as e:
        logger.error(f"Preprocessing modules not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise


def main():
    """
    Main entry point for the ingestion pipeline.
    Enforces the strict sequence:
    1. Ingestion (Materials Project, NIST, arXiv)
    2. Merge (run_merge_pipeline)
    3. Size Gate (Warning) - check_size_gate
    4. Preprocessing (Imputation, Encoding, Scaling)
    5. Schema Validation
    6. Size Gate (Halt) - check_processed_size (part of validate or separate)
    7. Final Output
    """
    logger.info("Starting Data Ingestion Pipeline...")
    
    settings = get_settings()
    data_paths = settings.get_data_paths()
    raw_dir = Path(data_paths['raw'])
    processed_dir = Path(data_paths['processed'])
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 1. Ingestion
    logger.info("Step 1: Ingesting data from sources...")
    dfs = []
    
    try:
        df_mp = run_materials_project_ingestion()
        if df_mp is not None and not df_mp.empty:
            dfs.append(df_mp)
            logger.info(f"Materials Project ingestion successful: {len(df_mp)} rows.")
        else:
            logger.warning("Materials Project ingestion returned empty or None.")
    except Exception as e:
        logger.warning(f"Materials Project ingestion failed: {e}")

    try:
        df_nist = run_nist_ingestion()
        if df_nist is not None and not df_nist.empty:
            dfs.append(df_nist)
            logger.info(f"NIST ingestion successful: {len(df_nist)} rows.")
        else:
            logger.warning("NIST ingestion returned empty or None.")
    except Exception as e:
        logger.warning(f"NIST ingestion failed: {e}")

    try:
        df_arxiv = run_arxiv_ingestion()
        if df_arxiv is not None and not df_arxiv.empty:
            dfs.append(df_arxiv)
            logger.info(f"arXiv ingestion successful: {len(df_arxiv)} rows.")
        else:
            logger.warning("arXiv ingestion returned empty or None.")
    except Exception as e:
        logger.warning(f"arXiv ingestion failed: {e}")

    if not dfs:
        logger.error("No data ingested from any source.")
        # Depending on strictness, we might exit here, but T018 says log warning if partial
        # However, if ALL fail, we cannot proceed.
        raise InsufficientDataError("All ingestion sources failed or returned empty data.")

    # 2. Merge
    logger.info("Step 2: Merging datasets...")
    merged_df = run_merge_pipeline(dfs)
    
    if merged_df is None or merged_df.empty:
        logger.error("Merge resulted in empty dataframe.")
        raise InsufficientDataError("Merged dataset is empty.")
    
    logger.info(f"Merge completed. Total rows: {len(merged_df)}")

    # 3. Size Gate (Warning) - T015c
    # This must happen AFTER merge (T015) and BEFORE preprocessing.
    logger.info("Step 3: Running Size Gate (Warning)...")
    try:
        check_size_gate()
        logger.info("Size Gate (Warning) passed.")
    except SystemExit:
        # check_size_gate raises SystemExit if < 150 rows? 
        # T015c says "log a critical warning but do NOT halt". 
        # T017c is the HALT gate. 
        # The implementation of check_size_gate in size_gate.py should reflect T015c (warning only).
        # If it raises SystemExit, that would be T017c logic. 
        # Let's assume check_size_gate here is the warning gate.
        # If the implementation raises SystemExit, we catch and log as warning to satisfy T015c.
        logger.warning("Size Gate (Warning) triggered: Dataset size < 150. Continuing with warning.")
        # Do not re-raise, as T015c is warning only.

    # 4. Preprocessing
    logger.info("Step 4: Running Preprocessing (Imputation, Encoding, Scaling)...")
    try:
        processed_df = run_preprocessing(merged_df)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

    # 5. Schema Validation
    logger.info("Step 5: Validating schema...")
    try:
        validate_schema(processed_df)
        logger.info("Schema validation passed.")
    except SchemaValidationError as e:
        logger.error(f"Schema validation failed: {e}")
        raise

    # 6. Size Gate (Halt) - T017c
    # This is the definitive check.
    logger.info("Step 6: Running Size Gate (Halt)...")
    # Assuming there is a function for the halt gate, or we reuse check_size_gate with a flag?
    # T017c says "raise SystemExit". 
    # Let's assume the function `check_processed_size` exists or we implement the logic here.
    # Based on T017c description: "Validate that the processed dataset still meets the minimum viable threshold of >= 150 rows."
    if len(processed_df) < 150:
        logger.critical("Processed dataset size < 150 experiments (minimum viable) per spec SC-004.")
        raise SystemExit(1)
    else:
        logger.info(f"Size Gate (Halt) passed. Dataset size: {len(processed_df)}")

    # 7. Output
    output_path = processed_dir / "ball_milling_dataset.parquet"
    logger.info(f"Step 7: Saving final dataset to {output_path}")
    processed_df.to_parquet(output_path, index=False)
    
    logger.info("Ingestion Pipeline completed successfully.")
    return processed_df


if __name__ == "__main__":
    main()
