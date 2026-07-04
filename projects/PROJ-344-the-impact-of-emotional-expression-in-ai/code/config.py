"""
Configuration settings for the llmXive research pipeline.
Defines paths, thresholds, and schema references for data validation.
"""
import os

# Project Root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data Paths
DATA_RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
DATA_FEATURES_DIR = os.path.join(PROJECT_ROOT, "data", "features")

# Output Paths
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")
STATE_DIR = os.path.join(PROJECT_ROOT, "state")

# Schema Paths (relative to project root)
DATASET_SCHEMA_PATH = os.path.join(
    PROJECT_ROOT, "specs", "001-emotional-synchrony-trust", "contracts", "dataset_schema.yaml"
)
FEATURE_SCHEMA_PATH = os.path.join(
    PROJECT_ROOT, "specs", "001-emotional-synchrony-trust", "contracts", "feature_extraction_schema.yaml"
)

# Validation Thresholds (FR-001 compliance)
# Minimum required metadata fields for any data file
REQUIRED_METADATA_FIELDS = [
    "interaction_id",
    "participant_id",
    "timestamp",
    "modality",
    "source_type"
]

# Allowed modalities
ALLOWED_MODALITIES = ["facial", "vocal", "text", "multimodal"]

# Required columns in processed feature datasets
REQUIRED_FEATURE_COLUMNS = [
    "interaction_id",
    "timestamp",
    "feature_name",
    "value"
]
