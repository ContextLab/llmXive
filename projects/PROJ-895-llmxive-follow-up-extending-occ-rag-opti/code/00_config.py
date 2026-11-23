import os
import torch

class Config:
    """
    Configuration for the OCC-RAG sensitivity analysis and pruning pipeline.
    Empirical values are placeholders until determined by T008.3.
    """
    # Random Seeds
    SAMPLE_SEED = 42
    
    # CPU/Resource Constraints
    MAX_RAM_THRESHOLD = 7.0  # GB
    
    # Structural Placeholders (to be populated by T008.3)
    MASK_FRACTION = None
    RETENTION_PCT = None
    FINE_TUNE_SAMPLE_SIZE = None
    
    # Thresholds for Edge Cases
    THRESHOLD = 0.01  # Minimum sensitivity delta to consider a parameter critical
    
    # Paths
    DATA_RAW_DIR = "data/raw"
    DATA_PROCESSED_DIR = "data/processed"
    MODEL_PATH = "nlp4research/occ-rag-1.7b-frozen"
    DATASET_PATH = "nlp4research/occ-rag-synthetic-corpus"

def validate_config():
    """
    Validates that critical configuration parameters are set.
    Raises ValueError if empirical values are still None.
    """
    missing = []
    if Config.MASK_FRACTION is None:
        missing.append("MASK_FRACTION")
    if Config.RETENTION_PCT is None:
        missing.append("RETENTION_PCT")
    if Config.FINE_TUNE_SAMPLE_SIZE is None:
        missing.append("FINE_TUNE_SAMPLE_SIZE")
    
    if missing:
        raise ValueError(f"Empirical configuration values not set: {missing}. Run T008.3 first.")
    
    if Config.MASK_FRACTION < 0 or Config.MASK_FRACTION > 1:
        raise ValueError("MASK_FRACTION must be between 0 and 1.")
    if Config.RETENTION_PCT < 0 or Config.RETENTION_PCT > 100:
        raise ValueError("RETENTION_PCT must be between 0 and 100.")
    
    return True
