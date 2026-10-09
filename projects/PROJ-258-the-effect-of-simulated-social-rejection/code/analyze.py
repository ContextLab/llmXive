"""
Entry‑point script for task T010.

It reads the pre‑computed feature file (features_ds000208.csv) and the
design decision stored in data/processed/metadata.json, runs the appropriate
ANOVA, and writes the raw statistics to data/processed/analysis_raw.json.
"""
import os
import logging
from config import get_path
from analysis import run_analysis_raw

def main():
    # Resolve standard project paths
    processed_dir = get_path('processed')
    feature_path = os.path.join(processed_dir, 'features_ds000208.csv')
    metadata_path = os.path.join(processed_dir, 'metadata.json')
    output_path = os.path.join(processed_dir, 'analysis_raw.json')

    # Ensure directories exist (they should, but be defensive)
    os.makedirs(processed_dir, exist_ok=True)

    # Run the T010 analysis
    run_analysis_raw(feature_path, metadata_path, output_path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()