import sys
import os
from pathlib import Path
from config import ensure_directories, RANDOM_SEED, SAMPLE_LIMIT
from config_validation import validate_configuration
from logging_config import get_logger, log_pipeline_start, log_pipeline_end, log_provenance
from data_ingestion import run_ingestion_pipeline
from diversity import run_diversity_pipeline
from transformation import run_transformation_pipeline
from analysis import run_analysis_pipeline

def main():
    """Orchestrate the full pipeline."""
    log_pipeline_start("Gut Microbiome and Cognitive Performance Analysis")
    
    try:
        # 1. Setup
        ensure_directories()
        validate_configuration()
        
        # 2. Data Ingestion (T011-T015)
        run_ingestion_pipeline()
        
        # 3. Diversity Analysis (T020)
        run_diversity_pipeline()
        
        # 4. Transformation (T021)
        run_transformation_pipeline()
        
        # 5. Analysis (T022, T023, T024)
        run_analysis_pipeline()
        
        log_pipeline_end("Pipeline completed successfully.")
        
    except Exception as e:
        log_pipeline_end("Pipeline failed.", error=str(e))
        raise

if __name__ == "__main__":
    main()
