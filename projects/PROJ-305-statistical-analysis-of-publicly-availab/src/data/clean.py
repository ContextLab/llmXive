import gc
import logging
import os
import sys
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import psutil

# Constants for error codes
E_MAPPINGS_INVALID = "E_MAPPINGS_INVALID"
E_MEMORY_LIMIT = "E_MEMORY_LIMIT"
E_SCHEMA_MISSING = "E_SCHEMA_MISSING"


def setup_logging() -> logging.Logger:
    """Configure logging for the cleaning process."""
    logger = logging.getLogger("clean")
    logger.setLevel(logging.INFO)

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # File handler
    fh = logging.FileHandler(logs_dir / "clean.log")
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024**3)


def check_memory_usage(logger: logging.Logger, limit_gb: float = 7.0) -> bool:
    """Check if memory usage exceeds limit. Returns True if limit exceeded."""
    current_gb = get_memory_usage_gb()
    if current_gb > limit_gb:
        logger.error(f"MEMORY_LIMIT_EXCEEDED: {current_gb:.2f} GB > {limit_gb} GB")
        return True
    return False


def estimate_file_size_gb(file_path: Path) -> float:
    """Estimate file size in GB."""
    if not file_path.exists():
        return 0.0
    size_bytes = file_path.stat().st_size
    return size_bytes / (1024**3)


def load_meddra_mapping(mapping_path: Path, logger: logging.Logger) -> pd.DataFrame:
    """Load MedDRA to SOC mapping table."""
    logger.info(f"Loading MedDRA mapping from {mapping_path}")

    if not mapping_path.exists():
        logger.error(f"MedDRA mapping file not found: {mapping_path}")
        raise FileNotFoundError(f"MedDRA mapping file not found: {mapping_path}")

    try:
        mapping_df = pd.read_csv(mapping_path)

        # Validate required columns
        required_cols = ["LLT_CODE", "SOC_CODE", "SOC_NAME"]
        missing_cols = [col for col in required_cols if col not in mapping_df.columns]

        if missing_cols:
            logger.error(f"MedDRA mapping missing required columns: {missing_cols}")
            raise ValueError(f"MedDRA mapping missing columns: {missing_cols}")

        logger.info(f"Loaded {len(mapping_df)} MedDRA mappings")
        return mapping_df

    except Exception as e:
        logger.error(f"Failed to load MedDRA mapping: {str(e)}")
        raise


def map_soc_to_name(
    row: pd.Series, mapping_df: pd.DataFrame, logger: logging.Logger
) -> str:
    """Map LLT or SOC_CODE to SOC_NAME using the mapping table."""
    llt_code = row.get("LLT", "")
    soc_code = row.get("SOC_CODE", "")

    # Try LLT first
    if pd.notna(llt_code) and llt_code != "":
        match = mapping_df[mapping_df["LLT_CODE"] == str(llt_code)]
        if not match.empty:
            return match.iloc[0]["SOC_NAME"]

    # Then try SOC_CODE
    if pd.notna(soc_code) and soc_code != "":
        match = mapping_df[mapping_df["SOC_CODE"] == str(soc_code)]
        if not match.empty:
            return match.iloc[0]["SOC_NAME"]

    return "UNKNOWN"


def process_chunk(
    chunk: pd.DataFrame, mapping_df: pd.DataFrame, logger: logging.Logger
) -> pd.DataFrame:
    """Process a single chunk of data."""
    # Filter out null/empty VAX_TYPE
    chunk = chunk[chunk["VAX_TYPE"].notna() & (chunk["VAX_TYPE"] != "")]
    chunk = chunk[chunk["VAX_TYPE"].apply(lambda x: isinstance(x, str))]

    # Filter out missing REPT_DATE
    chunk = chunk[chunk["REPT_DATE"].notna()]

    # Map SOC codes to SOC_NAME
    chunk["SOC_NAME"] = chunk.apply(
        lambda row: map_soc_to_name(row, mapping_df, logger), axis=1
    )

    return chunk


def process_data(
    input_files: List[Path],
    mapping_df: pd.DataFrame,
    logger: logging.Logger,
    chunk_size: int = 100_000,
) -> Dict[str, pd.DataFrame]:
    """Process all input files (CSV or Parquet) with memory‑aware chunked processing."""
    all_data = []
    total_rows = 0

    for file_path in input_files:
        logger.info(f"Processing file: {file_path}")

        file_size_gb = estimate_file_size_gb(file_path)
        use_chunked = file_size_gb > 5.0 or check_memory_usage(logger)

        if use_chunked:
            logger.info(
                f"Using chunked processing for {file_path} (size: {file_size_gb:.2f} GB)"
            )
            tracemalloc.start()

            # For chunked reading, only CSV supports chunksize; Parquet will be read fully
            if file_path.suffix.lower() == ".csv":
                reader = pd.read_csv(file_path, chunksize=chunk_size)
            else:
                # Parquet is not chunked; load whole file (it should fit within memory limits)
                df_full = pd.read_parquet(file_path)
                reader = [df_full]

            for chunk in reader:
                if check_memory_usage(logger):
                    tracemalloc.stop()
                    raise MemoryError(f"Memory limit exceeded while processing {file_path}")

                processed_chunk = process_chunk(chunk, mapping_df, logger)
                all_data.append(processed_chunk)
                total_rows += len(processed_chunk)

                if total_rows % 1_000_000 == 0:
                    logger.info(f"Processed {total_rows:,} rows")
                    current, peak = tracemalloc.get_traced_memory()
                    logger.info(
                        f"Current memory: {current / 1024 / 1024:.2f} MB, "
                        f"Peak: {peak / 1024 / 1024:.2f} MB"
                    )

            tracemalloc.stop()
            gc.collect()
        else:
            logger.info(f"Loading full file into memory: {file_path}")
            if file_path.suffix.lower() == ".csv":
                df = pd.read_csv(file_path)
            else:
                df = pd.read_parquet(file_path)

            processed_df = process_chunk(df, mapping_df, logger)
            all_data.append(processed_df)
            total_rows += len(processed_df)

    logger.info(f"Combining {len(all_data)} processed chunks")
    combined_df = pd.concat(all_data, ignore_index=True)

    # Create vaccine group labels
    covid_mask = combined_df["VAX_TYPE"].str.contains("COVID", case=False, na=False)
    flu_mask = combined_df["VAX_TYPE"].str.contains("Influenza", case=False, na=False)

    combined_df["VAX_GROUP"] = "Non-COVID-Non-Flu"
    combined_df.loc[covid_mask, "VAX_GROUP"] = "COVID-19"
    combined_df.loc[~covid_mask & flu_mask, "VAX_GROUP"] = "Flu-only"

    logger.info("Vaccine group assignment completed")

    return {"combined": combined_df}


def save_outputs(
    data: Dict[str, pd.DataFrame],
    output_dir: Path,
    logger: logging.Logger,
) -> None:
    """Save processed data and generate summary/validation logs."""
    output_dir.mkdir(parents=True, exist_ok=True)

    combined_df = data["combined"]

    # Save the full cleaned dataset (required by downstream tasks)
    cleaned_path = output_dir / "cleaned.parquet"
    logger.info(f"Saving cleaned dataset to {cleaned_path}")
    combined_df.to_parquet(cleaned_path, index=False)

    # Also save a CSV for human inspection
    csv_path = output_dir / "cleaned.csv"
    logger.info(f"Saving CSV version to {csv_path}")
    combined_df.to_csv(csv_path, index=False)

    # Write clean summary log
    total_rows = len(combined_df)
    valid_soc = combined_df["SOC_NAME"].notna() & (combined_df["SOC_NAME"] != "")
    valid_count = valid_soc.sum()
    coverage = (valid_count / total_rows) * 100 if total_rows > 0 else 0.0

    summary_path = Path("logs") / "clean_summary.txt"
    logger.info(f"Writing clean summary to {summary_path}")
    summary_path.write_text(
        f"Total rows: {total_rows}\\n"
        f"Rows with valid SOC_NAME: {valid_count}\\n"
        f"Coverage: {coverage:.2f}%\\n",
        encoding="utf-8",
    )

    # Validate cleaned dataset against schema
    try:
        from src.data.validate import load_schema, validate_data, _write_log_file

        schema_path = Path(
            "specs",
            "001-statistical-analysis-of-publicly-availab",
            "contracts",
            "cleaned_dataset.schema.yaml",
        )
        schema = load_schema(schema_path)
        # Use the same validation routine as the raw validator
        if validate_data(combined_df, schema):
            # Write success log (mirroring validate.py naming convention)
            (Path("logs") / "validate_clean_pass.txt").write_text(
                "PASS\\n", encoding="utf-8"
            )
            logger.info("Cleaned dataset validation passed")
        else:
            # The validate_data function already writes a fail log; we just raise
            raise RuntimeError("Cleaned dataset failed schema validation")
    except Exception as e:
        logger.error(f"Validation of cleaned dataset failed: {e}")
        raise


def main() -> None:
    """Main entry point for data cleaning."""
    logger = setup_logging()
    logger.info("Starting data cleaning process")

    # Start memory tracking
    tracemalloc.start()

    try:
        # Define project‑relative paths
        base_dir = Path(__file__).parent.parent.parent
        data_dir = base_dir / "data"
        raw_dir = data_dir / "raw"
        processed_dir = data_dir / "processed"
        mapping_path = data_dir / "meddra_to_soc.csv"

        # Ensure output directory exists
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Locate input files (CSV or Parquet)
        input_files = list(raw_dir.glob("vaers_*.csv")) + list(
            raw_dir.glob("vaers_*.parquet")
        )

        if not input_files:
            logger.error(f"No VAERS data files found in {raw_dir}")
            sys.exit(1)

        logger.info(
            f"Found {len(input_files)} input files: {[f.name for f in input_files]}"
        )

        # Load MedDRA mapping
        mapping_df = load_meddra_mapping(mapping_path, logger)

        # Process data
        data = process_data(input_files, mapping_df, logger)

        # Save outputs and run validation
        save_outputs(data, processed_dir, logger)

        # Final memory stats
        current, peak = tracemalloc.get_traced_memory()
        logger.info(
            f"Final memory usage: Current {current / 1024 / 1024:.2f} MB, "
            f"Peak {peak / 1024 / 1024:.2f} MB"
        )
        logger.info(f"Peak memory usage: {peak / 1024 / 1024 / 1024:.2f} GB")

        logger.info("Data cleaning completed successfully")

    except Exception as e:
        logger.error(f"Data cleaning failed: {e}")
        raise
    finally:
        tracemalloc.stop()


if __name__ == "__main__":
    main()