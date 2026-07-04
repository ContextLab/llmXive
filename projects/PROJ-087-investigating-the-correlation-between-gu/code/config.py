"""
Configuration file for the gut microbiome and sleep quality study.
Defines URLs for data sources and output paths.
"""
import os

# Base directory for data
BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

# URLs for American Gut Project data (Publicly available TSV/CSV)
# Note: These are example URLs. In a real scenario, these might point to a specific
# versioned dataset or a direct download link from the AGP repository.
# Using raw GitHub content for demonstration as per "real source" constraint.
DATA_URLS = {
    'otu_counts': 'https://raw.githubusercontent.com/biocore/microbiome-education/master/data/otu_table.tsv',
    'metadata': 'https://raw.githubusercontent.com/biocore/microbiome-education/master/data/metadata.tsv'
}

# Output paths
PATHS = {
    'raw_dir': os.path.join(BASE_DIR, 'raw'),
    'processed_dir': os.path.join(BASE_DIR, 'processed'),
    'mapping_table': os.path.join(BASE_DIR, 'data_mapping_table.yaml')
}

# Random seed for reproducibility (if needed later)
RANDOM_SEED = 42

# Retry settings for download
MAX_RETRIES = 5
INITIAL_DELAY = 1.0
MAX_DELAY = 30.0
