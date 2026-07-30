"""
Data ingestion, cleaning, and descriptor computation for ceramic Weibull modulus prediction.
"""
import pandas as pd
import logging
import re
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional, Tuple
import json

from . import logger
from .config import get_data_source_url, get_config_value
from chemparse import Composition

# Configure module logger
module_logger = logger.get_logger(__name__)


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def validate_url_for_fetch(url: str) -> bool:
    """
    Validate URL for fetching data.
    Checks scheme (http/https) and domain.
    """
    if not is_valid_url(url):
        return False
    parsed = urlparse(url)
    return parsed.scheme in ['http', 'https']


def fetch_data(source_url: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch raw ceramic data from a source URL or load from a local fallback file.
    
    Args:
        source_url: URL to fetch data from. If None, attempts to load from config or fallback.
        
    Returns:
        DataFrame with raw ceramic entries.
        
    Raises:
        RuntimeError: If data cannot be fetched or loaded.
    """
    if source_url is None:
        source_url = get_data_source_url()
    
    # Attempt to fetch from URL
    if source_url and validate_url_for_fetch(source_url):
        try:
            module_logger.info(f"Attempting to fetch data from {source_url}")
            # Placeholder for actual fetch logic (e.g., using requests)
            # For now, we assume the data is available in a specific format
            # In a real implementation, this would use requests.get()
            # and parse the response (JSON, CSV, etc.)
            raise NotImplementedError("URL fetching logic not yet implemented for this environment")
        except Exception as e:
            module_logger.warning(f"Failed to fetch from URL: {e}. Attempting fallback.")
    
    # Fallback: Load from local file if configured
    fallback_path = get_config_value("DATA_FALLBACK_PATH")
    if fallback_path and Path(fallback_path).exists():
        module_logger.info(f"Loading data from fallback file: {fallback_path}")
        try:
            df = pd.read_csv(fallback_path)
            module_logger.info(f"Successfully loaded {len(df)} rows from fallback.")
            return df
        except Exception as e:
            module_logger.error(f"Failed to load fallback data: {e}")
            raise RuntimeError(f"Data fetch failed and fallback load failed: {e}")
    
    raise RuntimeError("No valid data source available. Configure DATA_SOURCE_URL or DATA_FALLBACK_PATH.")


def validate_data_gap(df: pd.DataFrame, min_samples: int = 30) -> bool:
    """
    Validate that the dataset has sufficient samples.
    
    Args:
        df: Input DataFrame.
        min_samples: Minimum number of valid entries required.
        
    Returns:
        True if N >= min_samples, False otherwise.
        
    Raises:
        RuntimeError: If N < min_samples, halting execution.
    """
    # Count valid entries (assuming 'weibull_modulus' is the target)
    valid_count = df['weibull_modulus'].notna().sum()
    
    if valid_count < min_samples:
        msg = f"Data Gap Detected: Only {valid_count} valid entries found. Minimum required is {min_samples}. Halting execution."
        module_logger.critical(msg)
        # Generate Data Availability Report
        report_path = Path("data/artifacts/data_availability_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "status": "HALTED",
            "reason": "Insufficient data",
            "valid_entries": int(valid_count),
            "required_entries": min_samples,
            "message": "Data Gap Protocol triggered. Please acquire more data."
        }
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        raise RuntimeError(msg)
    
    module_logger.info(f"Data Gap Check Passed: {valid_count} valid entries found.")
    return True


def _extract_sample_count(series: pd.Series) -> Tuple[pd.Series, pd.Series]:
    """
    Extract sample count from fields named 'N', 'sample_size', or 'n'.
    Returns the extracted count and a flag for missing/invalid.
    """
    count_col = None
    for col in ['N', 'sample_size', 'n']:
        if col in series.index:
            count_col = col
            break
    
    if count_col is None:
        # Default to 1 if no count column found, or handle as error
        module_logger.warning("No sample count column found ('N', 'sample_size', 'n'). Assuming count=1.")
        return pd.Series(1, index=series.index), pd.Series(False, index=series.index)
    
    counts = series[count_col].copy()
    # Ensure numeric
    counts = pd.to_numeric(counts, errors='coerce')
    # Fill NaN with 1 (assuming single sample if missing)
    counts = counts.fillna(1)
    
    # Flag for missing original count
    missing_flag = series[count_col].isna()
    
    return counts, missing_flag


def _handle_range_values(series: pd.Series, column: str) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Handle range values in a specific column.
    Extracts midpoint, sets is_range_flag, and calculates range_uncertainty.
    """
    values = series[column].copy()
    is_range = pd.Series(False, index=series.index)
    range_original = pd.Series("", index=series.index)
    range_uncertainty = pd.Series(0.0, index=series.index)
    
    # Regex to match "min-max" or "min to max"
    pattern = re.compile(r'([\d.]+)\s*[-to]+\s*([\d.]+)', re.IGNORECASE)
    
    for idx, val in values.items():
        if pd.isna(val):
            continue
        val_str = str(val)
        match = pattern.search(val_str)
        if match:
            is_range.loc[idx] = True
            range_original.loc[idx] = val_str
            min_val = float(match.group(1))
            max_val = float(match.group(2))
            midpoint = (min_val + max_val) / 2.0
            uncertainty = (max_val - min_val) / 2.0
            values.loc[idx] = midpoint
            range_uncertainty.loc[idx] = uncertainty
    
    return values, is_range, range_original, range_uncertainty


def _impute_missing_values(df: pd.DataFrame, group_col: Optional[str] = None) -> pd.DataFrame:
    """
    Impute missing values in processing parameters.
    Strategy: Group median -> Global median.
    
    Args:
        df: Input DataFrame.
        group_col: Column to group by for group median imputation.
        
    Returns:
        DataFrame with imputed values.
    """
    processing_params = ['sintering_temp', 'pressure', 'time']
    df = df.copy()
    
    for param in processing_params:
        if param not in df.columns:
            continue
        
        missing_mask = df[param].isna()
        if not missing_mask.any():
            continue
        
        if group_col and group_col in df.columns:
            # Group median
            group_medians = df.groupby(group_col)[param].transform('median')
            imputed_values = group_medians.where(~missing_mask, df[param])
            # If group median is still NaN, fall back to global median
            global_median = df[param].median()
            imputed_values = imputed_values.where(~imputed_values.isna(), global_median)
        else:
            # Global median
            global_median = df[param].median()
            imputed_values = df[param].fillna(global_median)
        
        # Mark imputed rows
        df[f'{param}_imputed'] = missing_mask
        df[param] = imputed_values
        module_logger.debug(f"Imputed {missing_mask.sum()} missing values in {param} using {group_col or 'global'} median.")
    
    return df


def clean_data(df: pd.DataFrame, min_samples: int = 30) -> pd.DataFrame:
    """
    Clean and preprocess the raw ceramic data.
    
    Steps:
    1. Filter for N >= min_samples.
    2. Handle range values.
    3. Impute missing processing params.
    4. Handle non-stoichiometric phases.
    
    Args:
        df: Raw DataFrame.
        min_samples: Minimum sample count required.
        
    Returns:
        Cleaned DataFrame.
    """
    df = df.copy()
    module_logger.info(f"Starting data cleaning on {len(df)} rows.")
    
    # 1. Extract and filter sample count
    counts, missing_count_flag = _extract_sample_count(df)
    df['sample_count'] = counts
    
    # Log exclusions for N < min_samples
    excluded_n = df[df['sample_count'] < min_samples]
    if len(excluded_n) > 0:
        module_logger.warning(f"Excluding {len(excluded_n)} rows due to sample count < {min_samples}.")
        for idx in excluded_n.index:
            module_logger.info(f"Exclusion: N < {min_samples} at index {idx}")
    
    df = df[df['sample_count'] >= min_samples].reset_index(drop=True)
    module_logger.info(f"Data filtered to {len(df)} rows after sample count check.")
    
    # 2. Handle range values for 'weibull_modulus' if needed
    if 'weibull_modulus' in df.columns:
        # Assuming weibull_modulus might be a range
        # If it's already numeric, skip. If it's object/string, handle range.
        if df['weibull_modulus'].dtype == 'object':
            df['weibull_modulus'], df['is_range_flag'], df['range_original'], df['range_uncertainty'] = \
                _handle_range_values(df, 'weibull_modulus')
        else:
            df['is_range_flag'] = False
            df['range_original'] = ""
            df['range_uncertainty'] = 0.0
    else:
        df['is_range_flag'] = False
        df['range_original'] = ""
        df['range_uncertainty'] = 0.0
    
    # 3. Impute missing processing params
    # Determine group column if available (e.g., 'material_class')
    group_col = 'material_class' if 'material_class' in df.columns else None
    df = _impute_missing_values(df, group_col)
    
    # 4. Handle non-stoichiometric phases
    # Check for 'composition' column and validate stoichiometry
    if 'composition' in df.columns:
        non_stoich_indices = []
        for idx, comp_str in df['composition'].items():
            try:
                # Attempt to parse composition
                comp = Composition(comp_str)
                if comp.is_non_stoichiometric:
                    non_stoich_indices.append(idx)
            except Exception:
                non_stoich_indices.append(idx)
        
        if non_stoich_indices:
            module_logger.warning(f"Found {len(non_stoich_indices)} non-stoichiometric or invalid compositions.")
            for idx in non_stoich_indices:
                comp_val = df.loc[idx, 'composition']
                # Log exclusion or fallback
                # For this implementation, we log and exclude for safety, 
                # but the spec says "log warning, exclude, OR impute using nearest neighbor"
                # We choose to exclude and log.
                module_logger.info(f"Exclusion: Invalid/Non-stoichiometric composition '{comp_val}' at index {idx}")
        
        # Drop non-stoichiometric rows
        df = df.drop(non_stoich_indices).reset_index(drop=True)
    
    module_logger.info(f"Data cleaning complete. Final rows: {len(df)}")
    return df


def compute_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute elemental descriptors for each ceramic entry.
    
    Calculates:
    - Mean atomic radius
    - Electronegativity std
    - Cation Size Variance
    - Valence Electron Concentration (VEC)
    - Primary Anion/Cation Group
    
    Args:
        df: Cleaned DataFrame with 'composition' column.
        
    Returns:
        DataFrame with added descriptor columns.
    """
    df = df.copy()
    module_logger.info("Computing descriptors...")
    
    # Initialize descriptor columns
    descriptors = [
        'mean_atomic_radius', 'electronegativity_std', 'cation_size_variance',
        'valence_electron_concentration', 'primary_anion_cation_group'
    ]
    for desc in descriptors:
        df[desc] = 0.0
    
    # Periodic table data (simplified for demo; in real impl, use a library like mendeleev)
    # Mapping of element symbols to properties
    # This is a minimal subset for demonstration. A full implementation would use a library.
    element_data = {
        'Al': {'radius': 143, 'electronegativity': 1.61, 'valence': 3, 'group': 13, 'is_cation': True},
        'Si': {'radius': 117, 'electronegativity': 1.90, 'valence': 4, 'group': 14, 'is_cation': True},
        'O': {'radius': 66, 'electronegativity': 3.44, 'valence': 2, 'group': 16, 'is_cation': False},
        'Ti': {'radius': 147, 'electronegativity': 1.54, 'valence': 4, 'group': 4, 'is_cation': True},
        'Zr': {'radius': 160, 'electronegativity': 1.33, 'valence': 4, 'group': 4, 'is_cation': True},
        'Hf': {'radius': 159, 'electronegativity': 1.30, 'valence': 4, 'group': 4, 'is_cation': True},
        'Ba': {'radius': 222, 'electronegativity': 0.89, 'valence': 2, 'group': 2, 'is_cation': True},
        'Ca': {'radius': 197, 'electronegativity': 1.00, 'valence': 2, 'group': 2, 'is_cation': True},
        'Mg': {'radius': 160, 'electronegativity': 1.31, 'valence': 2, 'group': 2, 'is_cation': True},
        'Y': {'radius': 180, 'electronegativity': 1.22, 'valence': 3, 'group': 3, 'is_cation': True},
        'La': {'radius': 187, 'electronegativity': 1.10, 'valence': 3, 'group': 3, 'is_cation': True},
        'Ce': {'radius': 182, 'electronegativity': 1.12, 'valence': 4, 'group': 3, 'is_cation': True},
        'Fe': {'radius': 126, 'electronegativity': 1.83, 'valence': 3, 'group': 8, 'is_cation': True},
        'Ni': {'radius': 124, 'electronegativity': 1.91, 'valence': 2, 'group': 10, 'is_cation': True},
        'Cu': {'radius': 128, 'electronegativity': 1.90, 'valence': 2, 'group': 11, 'is_cation': True},
        'Zn': {'radius': 134, 'electronegativity': 1.65, 'valence': 2, 'group': 12, 'is_cation': True},
        'Sn': {'radius': 140, 'electronegativity': 1.96, 'valence': 4, 'group': 14, 'is_cation': True},
        'Pb': {'radius': 175, 'electronegativity': 2.33, 'valence': 4, 'group': 14, 'is_cation': True},
        'Nb': {'radius': 146, 'electronegativity': 1.60, 'valence': 5, 'group': 5, 'is_cation': True},
        'Ta': {'radius': 146, 'electronegativity': 2.36, 'valence': 5, 'group': 5, 'is_cation': True},
        'Mo': {'radius': 139, 'electronegativity': 2.16, 'valence': 6, 'group': 6, 'is_cation': True},
        'W': {'radius': 139, 'electronegativity': 2.36, 'valence': 6, 'group': 6, 'is_cation': True},
        'V': {'radius': 134, 'electronegativity': 1.63, 'valence': 5, 'group': 5, 'is_cation': True},
        'Cr': {'radius': 128, 'electronegativity': 1.66, 'valence': 3, 'group': 6, 'is_cation': True},
        'Mn': {'radius': 127, 'electronegativity': 1.55, 'valence': 2, 'group': 7, 'is_cation': True},
        'Co': {'radius': 125, 'electronegativity': 1.88, 'valence': 2, 'group': 9, 'is_cation': True},
        'Ga': {'radius': 135, 'electronegativity': 1.81, 'valence': 3, 'group': 13, 'is_cation': True},
        'Ge': {'radius': 122, 'electronegativity': 2.01, 'valence': 4, 'group': 14, 'is_cation': True},
        'As': {'radius': 119, 'electronegativity': 2.18, 'valence': 3, 'group': 15, 'is_cation': False},
        'Sb': {'radius': 140, 'electronegativity': 2.05, 'valence': 3, 'group': 15, 'is_cation': False},
        'Bi': {'radius': 155, 'electronegativity': 2.02, 'valence': 3, 'group': 15, 'is_cation': False},
        'S': {'radius': 104, 'electronegativity': 2.58, 'valence': 2, 'group': 16, 'is_cation': False},
        'Se': {'radius': 117, 'electronegativity': 2.55, 'valence': 2, 'group': 16, 'is_cation': False},
        'Te': {'radius': 137, 'electronegativity': 2.10, 'valence': 2, 'group': 16, 'is_cation': False},
        'F': {'radius': 64, 'electronegativity': 3.98, 'valence': 1, 'group': 17, 'is_cation': False},
        'Cl': {'radius': 99, 'electronegativity': 3.16, 'valence': 1, 'group': 17, 'is_cation': False},
        'Br': {'radius': 114, 'electronegativity': 2.96, 'valence': 1, 'group': 17, 'is_cation': False},
        'I': {'radius': 133, 'electronegativity': 2.66, 'valence': 1, 'group': 17, 'is_cation': False},
    }
    
    def parse_and_compute(comp_str: str) -> Dict[str, float]:
        try:
            comp = Composition(comp_str)
            elements = comp.elements
            counts = comp.counts
            
            total_atoms = sum(counts)
            sum_radius = 0.0
            sum_en = 0.0
            sum_en_sq = 0.0
            sum_valence = 0.0
            cation_radii = []
            cation_groups = []
            
            for elem, count in zip(elements, counts):
                elem_str = elem.symbol
                if elem_str not in element_data:
                    # Fallback: skip or use average? For now, skip and log
                    module_logger.warning(f"Element {elem_str} not found in periodic table data. Skipping.")
                    continue
                
                data = element_data[elem_str]
                sum_radius += data['radius'] * count
                sum_en += data['electronegativity'] * count
                sum_en_sq += (data['electronegativity'] ** 2) * count
                sum_valence += data['valence'] * count
                
                if data['is_cation']:
                    cation_radii.append(data['radius'])
                    cation_groups.append(data['group'])
            
            if total_atoms == 0 or len(cation_radii) == 0:
                return {
                    'mean_atomic_radius': 0.0,
                    'electronegativity_std': 0.0,
                    'cation_size_variance': 0.0,
                    'valence_electron_concentration': 0.0,
                    'primary_anion_cation_group': 0
                }
            
            mean_radius = sum_radius / total_atoms
            mean_en = sum_en / total_atoms
            variance_en = (sum_en_sq / total_atoms) - (mean_en ** 2)
            std_en = variance_en ** 0.5 if variance_en > 0 else 0.0
            
            # Cation Size Variance
            mean_cation_radius = sum(cation_radii) / len(cation_radii)
            cation_var = sum((r - mean_cation_radius) ** 2 for r in cation_radii) / len(cation_radii)
            
            # Valence Electron Concentration
            vec = sum_valence / total_atoms
            
            # Primary Anion/Cation Group
            # Use the most frequent group among cations
            if cation_groups:
                from collections import Counter
                group_counts = Counter(cation_groups)
                primary_group = group_counts.most_common(1)[0][0]
            else:
                primary_group = 0
            
            return {
                'mean_atomic_radius': mean_radius,
                'electronegativity_std': std_en,
                'cation_size_variance': cation_var,
                'valence_electron_concentration': vec,
                'primary_anion_cation_group': primary_group
            }
        except Exception as e:
            module_logger.error(f"Error parsing composition {comp_str}: {e}")
            return {
                'mean_atomic_radius': 0.0,
                'electronegativity_std': 0.0,
                'cation_size_variance': 0.0,
                'valence_electron_concentration': 0.0,
                'primary_anion_cation_group': 0
            }
    
    # Apply to each row
    results = df['composition'].apply(parse_and_compute)
    for desc in descriptors:
        df[desc] = results.apply(lambda x: x[desc])
    
    module_logger.info("Descriptor computation complete.")
    return df


def validate_no_missing_predictors(df: pd.DataFrame) -> bool:
    """
    Validate that no primary predictor columns have missing values after imputation.
    
    Primary predictors: composition, weibull_modulus, and computed descriptors.
    
    Args:
        df: DataFrame after cleaning and descriptor computation.
        
    Returns:
        True if no missing values, False otherwise.
    """
    predictors = ['composition', 'weibull_modulus', 'mean_atomic_radius', 'electronegativity_std',
                  'cation_size_variance', 'valence_electron_concentration', 'primary_anion_cation_group',
                  'sintering_temp']
    
    missing_found = False
    for col in predictors:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                module_logger.error(f"Missing values found in primary predictor '{col}': {missing_count}")
                missing_found = True
        else:
            module_logger.error(f"Primary predictor column '{col}' not found in DataFrame.")
            missing_found = True
    
    if missing_found:
        module_logger.critical("Validation failed: Missing values in primary predictors.")
    else:
        module_logger.info("Validation passed: No missing values in primary predictors.")
    
    return not missing_found


def main():
    """
    Main entry point for the ingestion pipeline.
    """
    module_logger.info("Starting data ingestion pipeline.")
    
    try:
        # 1. Fetch Data
        df = fetch_data()
        module_logger.info(f"Fetched {len(df)} raw rows.")
        
        # 2. Validate Data Gap
        validate_data_gap(df, min_samples=30)
        
        # 3. Clean Data
        df_clean = clean_data(df, min_samples=30)
        module_logger.info(f"Cleaned data has {len(df_clean)} rows.")
        
        # 4. Compute Descriptors
        df_descriptors = compute_descriptors(df_clean)
        
        # 5. Validate No Missing Predictors
        validate_no_missing_predictors(df_descriptors)
        
        # Save output
        output_path = Path("data/processed/ceramic_dataset_cleaned.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_descriptors.to_csv(output_path, index=False)
        module_logger.info(f"Cleaned dataset saved to {output_path}")
        
    except Exception as e:
        module_logger.critical(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()