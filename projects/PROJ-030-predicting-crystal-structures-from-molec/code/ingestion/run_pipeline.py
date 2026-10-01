import os
import sys
import json
import logging
import traceback
from pathlib import Path

from ingestion.load_cod import stream_cod_organic
from ingestion.parse_cif import process_cif_batch
from ingestion.fingerprint import generate_fingerprints_for_dataset
from ingestion.dataset_builder import handle_polymorphism, save_dataset

def setup_pipeline_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/pipeline.log")
        ]
    )

def run_download_and_parse():
    logging.info("Starting download and parse step...")
    cif_files = stream_cod_organic()
    parsed_data = process_cif_batch(cif_files)
    logging.info(f"Parsed {len(parsed_data)} CIF files.")
    return parsed_data

def run_fingerprinting_and_finalization(parsed_data):
    logging.info("Starting fingerprinting and finalization step...")
    fingerprints = generate_fingerprints_for_dataset(parsed_data)
    polymorphic_data = handle_polymorphism(fingerprints)
    logging.info(f"Processed {len(polymorphic_data)} polymorphic records.")
    return polymorphic_data

def run_full_pipeline():
    setup_pipeline_logging()
    try:
        parsed_data = run_download_and_parse()
        polymorphic_data = run_fingerprinting_and_finalization(parsed_data)
        save_dataset(polymorphic_data, "data/processed/crystal_dataset.csv")
        logging.info("Pipeline completed successfully.")
    except Exception as e:
        logging.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_full_pipeline()