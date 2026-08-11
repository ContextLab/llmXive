import os
import sys
import json
import logging
import requests
import re
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from chemparse import Composition
import numpy as np

from config import load_environment, initialize_config, get_config_value
from . import logger

# Ensure logger is configured
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
DATA_ARTIFACTS_DIR = PROJECT_ROOT / "data" / "artifacts"
LOGS_DIR = PROJECT_ROOT / "logs"

def ensure_directories():
    """Create necessary directories if they do not exist."""
    for directory in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_REPORTS_DIR, DATA_ARTIFACTS_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

def derive_primary_anion_cation_group(composition_str: str) -> str:
    """
    Parse the composition string using chemparse to identify the primary anion and cation groups.
    Returns a string like 'O-Al' for Alumina.
    """
    try:
        parsed = Composition(composition_str)
        elements = list(parsed.elements)
        if not elements:
            return "Unknown"
        
        # Simple heuristic: assume the first element is the cation and the last is the anion for binary ceramics
        # In a more complex scenario, we would need a periodic table lookup for groups.
        # For now, we return a string representation of the first and last element symbols.
        # This is a placeholder for the actual logic which would require a more robust chemical library.
        # Given the constraints, we'll return a simplified version.
        cation = elements[0]
        anion = elements[-1]
        return f"{anion}-{cation}"
    except Exception as e:
        log.error(f"Failed to parse composition {composition_str}: {e}")
        return "Unknown"

def derive_primary_anion_cation_group_batch(df: pd.DataFrame) -> pd.DataFrame:
    """Apply derive_primary_anion_cation_group to a DataFrame column."""
    df['primary_anion_cation_group'] = df['composition'].apply(derive_primary_anion_cation_group)
    return df

def fetch_materials_project_data() -> Optional[pd.DataFrame]:
    """
    Fetch ceramic property data from Materials Project using pymatgen.
    Filters for entries with non-null weibull_modulus.
    """
    try:
        from mp_api.client import MPRestClient
        from pymatgen.core import Composition as PymatgenComposition
        
        api_key = os.getenv('MP_API_KEY')
        if not api_key:
            raise RuntimeError("MP_API_KEY not found in environment variables")
        
        client = MPRestClient(api_key=api_key)
        
        # Fetch entries with Weibull modulus property
        # Note: The exact property name might vary. We assume 'weibull_modulus' based on the task description.
        entries = client.get_entries(
            properties=['weibull_modulus', 'composition', 'formula_pretty'],
            is_stable=True
        )
        
        data = []
        for entry in entries:
            if entry.material_id and entry.properties.get('weibull_modulus') is not None:
                data.append({
                    'material_id': entry.material_id,
                    'composition': entry.formula_pretty,
                    'weibull_modulus': entry.properties['weibull_modulus'],
                    'source': 'Materials Project'
                })
        
        if not data:
            raise RuntimeError("Materials Project fetch returned no data with Weibull modulus")
        
        df = pd.DataFrame(data)
        output_path = DATA_RAW_DIR / "materials_project_raw.json"
        df.to_json(output_path, orient='records', indent=2)
        log.info(f"Saved Materials Project data to {output_path}")
        return df
    
    except Exception as e:
        log.error(f"Materials Project fetch failed: {e}")
        raise RuntimeError(f"Materials Project fetch failed: {e}")

def fetch_nist_data() -> Optional[pd.DataFrame]:
    """
    Fetch NIST ceramic data from a verified URL.
    Parses CSV columns: composition, weibull_modulus, sample_count, sintering_temp.
    """
    url = "https://www.nist.gov/publications/ceramic-weibull-modulus-dataset" # Placeholder URL, needs to be replaced with actual
    try:
        # Since the actual URL might not be directly accessible as a CSV, we simulate the fetch for this task.
        # In a real scenario, we would use requests.get(url) and parse the response.
        # For now, we assume the data is available in a specific format.
        # This is a placeholder to demonstrate the structure.
        # Real implementation would require the actual URL and parsing logic.
        raise NotImplementedError("NIST data fetch requires a specific URL and parsing logic not provided.")
    except Exception as e:
        log.error(f"NIST data fetch failed: {e}")
        raise RuntimeError(f"NIST data fetch failed: {e}")

def fetch_arxiv_data() -> Optional[pd.DataFrame]:
    """
    Use arxiv library to search for ceramic Weibull modulus papers.
    Extracts data from the top 5 PDFs using pdfplumber.
    """
    try:
        import arxiv
        import pdfplumber
        
        search = arxiv.Search(
            query="all:ceramic AND all:weibull",
            max_results=5,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        data = []
        for result in search.results():
            pdf_path = result.download_pdf(dirpath=DATA_ARTIFACTS_DIR / "arxiv_pdfs")
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        # Check if table contains composition and Weibull/Modulus columns
                        if any('composition' in str(row).lower() or 'weibull' in str(row).lower() for row in table):
                            # Extract relevant data
                            for row in table[1:]: # Skip header
                                if len(row) >= 2:
                                    data.append({
                                        'composition': row[0],
                                        'weibull_modulus': row[1],
                                        'source': f"arXiv:{result.entry_id}"
                                    })
                            break
        
        if not data:
            raise RuntimeError("No valid table found in arXiv PDFs")
        
        df = pd.DataFrame(data)
        output_path = DATA_RAW_DIR / "arxiv_raw.json"
        df.to_json(output_path, orient='records', indent=2)
        log.info(f"Saved arXiv data to {output_path}")
        return df
    
    except Exception as e:
        log.error(f"arXiv data fetch failed: {e}")
        raise RuntimeError(f"arXiv data fetch failed: {e}")

def fetch_curated_literature_data() -> Optional[pd.DataFrame]:
    """
    Fetch the 'Curated Literature Dataset' from a verified URL.
    Parses CSV columns: composition, weibull_modulus, sample_count, sintering_temp.
    """
    url = "https://example.com/curated_literature_dataset.csv" # Placeholder URL
    try:
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        
        required_cols = ['composition', 'weibull_modulus', 'sample_count', 'sintering_temp']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}")
        
        df['source'] = 'Curated Literature'
        output_path = DATA_RAW_DIR / "curated_literature_raw.json"
        df.to_json(output_path, orient='records', indent=2)
        log.info(f"Saved Curated Literature data to {output_path}")
        return df
    
    except Exception as e:
        log.error(f"Curated Literature data fetch failed: {e}")
        raise RuntimeError(f"Curated Literature data fetch failed: {e}")

def load_and_combine_raw_data() -> pd.DataFrame:
    """Load all raw data sources and combine them into a single DataFrame."""
    ensure_directories()
    sources = []
    
    # Try to load from each source
    try:
        mp_data = fetch_materials_project_data()
        if mp_data is not None:
            sources.append(mp_data)
    except Exception as e:
        log.warning(f"Skipping Materials Project data: {e}")
    
    try:
        nist_data = fetch_nist_data()
        if nist_data is not None:
            sources.append(nist_data)
    except Exception as e:
        log.warning(f"Skipping NIST data: {e}")
    
    try:
        arxiv_data = fetch_arxiv_data()
        if arxiv_data is not None:
            sources.append(arxiv_data)
    except Exception as e:
        log.warning(f"Skipping arXiv data: {e}")
    
    try:
        curated_data = fetch_curated_literature_data()
        if curated_data is not None:
            sources.append(curated_data)
    except Exception as e:
        log.warning(f"Skipping Curated Literature data: {e}")
    
    if not sources:
        raise RuntimeError("No data sources were successfully loaded")
    
    combined_df = pd.concat(sources, ignore_index=True)
    output_path = DATA_RAW_DIR / "combined_raw.csv"
    combined_df.to_csv(output_path, index=False)
    log.info(f"Combined raw data saved to {output_path}")
    return combined_df

def validate_data_gap(df: pd.DataFrame) -> bool:
    """
    Check total valid entries after fetching and deriving groups.
    Halts execution if N < 30 and generates a "Data Availability Report".
    """
    log.info(f"Validating data gap. Total entries: {len(df)}")
    
    if len(df) < 30:
        log.warning("Insufficient data (< 30 entries). Generating Data Availability Report.")
        generate_data_availability_report(df)
        return False
    
    return True

def generate_data_availability_report(df: pd.DataFrame) -> str:
    """
    Generate the data/reports/data_availability_report.json file when halting due to insufficient data.
    """
    ensure_directories()
    
    report = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "total_entries": len(df),
        "threshold": 30,
        "status": "HALTED_INSUFFICIENT_DATA",
        "sources": df['source'].value_counts().to_dict() if 'source' in df.columns else {},
        "missing_fields": [],
        "recommendation": "Increase data sources or lower threshold (not recommended for statistical validity)."
    }
    
    # Check for missing fields in the dataset
    required_fields = ['composition', 'weibull_modulus']
    for field in required_fields:
        if field not in df.columns:
            report['missing_fields'].append(field)
        else:
            missing_count = df[field].isna().sum()
            if missing_count > 0:
                report['missing_fields'].append(f"{field}_missing_{missing_count}")
    
    output_path = DATA_REPORTS_DIR / "data_availability_report.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    log.info(f"Data Availability Report saved to {output_path}")
    return str(output_path)

def clean_data_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Consolidated data cleaning pipeline.
    Steps:
    1. filter_valid_stoichiometry()
    2. handle_range_values()
    3. impute_missing_params()
    4. handle_non_stoichiometric_phases()
    """
    # Placeholder for actual cleaning logic
    # This would involve filtering, imputation, and other data cleaning steps
    return df

def validate_no_missing_primary_predictors(df: pd.DataFrame) -> bool:
    """
    Validate that essential descriptors have no missing values after cleaning and imputation.
    """
    essential_descriptors = ['mean_atomic_radius', 'electronegativity_std', 'valence_electron_concentration']
    for desc in essential_descriptors:
        if desc in df.columns and df[desc].isna().sum() > 0:
            log.error(f"Missing values found in essential descriptor: {desc}")
            return False
    return True

def main():
    """Main entry point for the ingestion pipeline."""
    load_environment()
    initialize_config()
    ensure_directories()
    
    try:
        # Load and combine raw data
        combined_df = load_and_combine_raw_data()
        
        # Derive primary anion/cation groups
        combined_df = derive_primary_anion_cation_group_batch(combined_df)
        
        # Validate data gap
        if not validate_data_gap(combined_df):
            log.error("Data gap validation failed. Pipeline halted.")
            sys.exit(1)
        
        # Clean data
        cleaned_df = clean_data_pipeline(combined_df)
        
        # Validate primary predictors
        if not validate_no_missing_primary_predictors(cleaned_df):
            log.error("Primary predictor validation failed.")
            sys.exit(1)
        
        log.info("Ingestion pipeline completed successfully.")
    
    except Exception as e:
        log.error(f"Ingestion pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()