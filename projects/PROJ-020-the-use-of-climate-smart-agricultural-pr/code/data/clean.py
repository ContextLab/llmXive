"""
Data cleaning, merging, imputation, and sampling pipeline for CSA analysis.
Implements T016, T017, T018, and T018b.
"""
import os
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from utils.logging import get_logger, log_operation, ReproducibilityLogger
from utils.config import get_raw_data_dir, get_processed_data_dir, get_state_dir, get_target_countries, get_target_years

# Initialize logger
logger = get_logger("data_clean")

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth (km)."""
    R = 6371.0  # Earth radius in km
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def merge_climate_data(df_lsms: pd.DataFrame, df_climate: pd.DataFrame, max_dist_km: float = 100.0) -> pd.DataFrame:
    """
    Merge climate data to LSMS data based on spatial proximity.
    Uses Haversine formula for distance calculation.
    """
    if df_climate.empty or df_lsms.empty:
        logger.warning("Empty dataframe provided for climate merge.")
        return df_lsms

    # Ensure coordinates are numeric
    df_lsms = df_lsms.copy()
    df_climate = df_climate.copy()

    # Drop rows with missing coordinates
    df_lsms = df_lsms.dropna(subset=['latitude', 'longitude'])

    merged_rows = []
    unmatched_count = 0

    for idx, row in df_lsms.iterrows():
        best_match = None
        min_dist = float('inf')

        for c_idx, c_row in df_climate.iterrows():
            dist = haversine_distance(
                row['latitude'], row['longitude'],
                c_row['latitude'], c_row['longitude']
            )
            if dist <= max_dist_km and dist < min_dist:
                min_dist = dist
                best_match = c_row

        if best_match is not None:
            new_row = row.to_dict()
            new_row.update(best_match.to_dict())
            new_row['climate_dist_km'] = min_dist
            merged_rows.append(new_row)
        else:
            unmatched_count += 1

    logger.info(f"Merged {len(merged_rows)} rows; {unmatched_count} unmatched due to distance > {max_dist_km}km.")
    return pd.DataFrame(merged_rows)

def clean_and_merge(lsms_data: Dict[str, pd.DataFrame], climate_data: Dict[str, pd.DataFrame], faostat_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Clean and merge LSMS, Climate, and FAOSTAT data.
    Returns a single merged DataFrame.
    """
    # Start with LSMS data (assuming it's the primary unit of analysis: household)
    # Combine all country LSMS data
    all_lsms = []
    for country, df in lsms_data.items():
        df = df.copy()
        df['country'] = country
        all_lsms.append(df)
    
    if not all_lsms:
        raise ValueError("No LSMS data provided for merging.")

    df_lsms = pd.concat(all_lsms, ignore_index=True)

    # Merge Climate Data (simplified: assume climate data is already aggregated or matched)
    # In a real scenario, we would iterate through climate data and match by coordinates
    # For this implementation, we assume climate_data is a dict of country -> df, 
    # and we perform a spatial join or nearest neighbor match if coordinates exist.
    # If climate_data keys match country codes, we might join on country + year if available.
    
    # Placeholder for complex spatial join if needed; currently assuming direct match or no climate if empty
    # If climate_data exists, we attempt to merge if 'latitude'/'longitude' exist in both
    if climate_data:
        all_climate = []
        for country, df in climate_data.items():
            df = df.copy()
            df['country'] = country
            all_climate.append(df)
        if all_climate:
            df_climate = pd.concat(all_climate, ignore_index=True)
            df_lsms = merge_climate_data(df_lsms, df_climate)

    # Merge FAOSTAT (usually by Country + Year)
    if faostat_data:
        all_faostat = []
        for country, df in faostat_data.items():
            df = df.copy()
            df['country'] = country
            all_faostat.append(df)
        if all_faostat:
            df_faostat = pd.concat(all_faostat, ignore_index=True)
            # Merge on country and year if available
            merge_keys = ['country', 'year']
            if all(k in df_lsms.columns and k in df_faostat.columns for k in merge_keys):
                df_lsms = df_lsms.merge(df_faostat, on=merge_keys, how='left')
            else:
                # Fallback: merge on country only if year is missing
                if 'country' in df_lsms.columns and 'country' in df_faostat.columns:
                    df_lsms = df_lsms.merge(df_faostat, on='country', how='left')

    return df_lsms

def apply_imputation(df: pd.DataFrame, strategy: str = 'mean') -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Apply imputation strategy to missing values.
    """
    df = df.copy()
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    imputation_report = {}

    for col in numeric_cols:
        if df[col].isna().any():
            if strategy == 'mean':
                val = df[col].mean()
            elif strategy == 'median':
                val = df[col].median()
            else:
                val = 0
            
            df[col] = df[col].fillna(val)
            imputation_report[col] = {'strategy': strategy, 'value': val, 'missing_count': int(df[col].isna().sum())}

    return df, imputation_report

def validate_imputation_quality(df: pd.DataFrame) -> bool:
    """
    Validate that key predictors have no missing values after imputation.
    """
    key_predictors = ['csa_index', 'hdds', 'digital_access', 'finance_access']
    for col in key_predictors:
        if col in df.columns and df[col].isna().any():
            logger.warning(f"Key predictor {col} still has missing values.")
            return False
    return True

def get_imputation_report(report: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert imputation report to DataFrame for logging.
    """
    return pd.DataFrame([report])

@log_operation
def run_sampling_pipeline(
    raw_lsms_path: Optional[str] = None,
    raw_climate_path: Optional[str] = None,
    raw_faostat_path: Optional[str] = None,
    output_path: Optional[str] = None,
    ipw_output_path: Optional[str] = None
) -> None:
    """
    Main pipeline: Download (if paths provided), Clean, Merge, Impute, Sample.
    Calculates Merge Success Rate (T018b) and outputs IPW weights (T018).
    """
    processed_dir = get_processed_data_dir()
    state_dir = get_state_dir()
    
    # If paths are not provided, assume data is already downloaded to raw/
    # For T018b, we need to calculate merge success rate.
    # We assume the data is loaded into memory as DataFrames.
    # In a real run, we would load from the raw files.
    
    # Simulate loading data (In real execution, load from disk)
    # Since T013-T015 are implemented, we assume data exists in data/raw/
    # We will load them here if they exist.
    
    lsms_data = {}
    climate_data = {}
    faostat_data = {}
    
    countries = get_target_countries()
    years = get_target_years()
    
    # Load LSMS (Mocking load for now, assuming T013-T015 populated data/raw/)
    # In a real scenario, we'd iterate and load parquet/csv from data/raw/
    for country in countries:
        # Check for LSMS file
        lsms_file = Path(raw_lsms_path) if raw_lsms_path else Path(get_raw_data_dir()) / f"{country}_lsms.parquet"
        if lsms_file.exists():
            lsms_data[country] = pd.read_parquet(lsms_file)
        else:
            # Fallback to searching data/raw/
            for f in Path(get_raw_data_dir()).glob(f"{country}*"):
                if f.suffix == '.parquet' or f.suffix == '.csv':
                    df = pd.read_parquet(f) if f.suffix == '.parquet' else pd.read_csv(f)
                    lsms_data[country] = df
                    break
    
    # Load Climate
    for country in countries:
        climate_file = Path(raw_climate_path) if raw_climate_path else Path(get_raw_data_dir()) / f"{country}_climate.parquet"
        if climate_file.exists():
            climate_data[country] = pd.read_parquet(climate_file)
        else:
            for f in Path(get_raw_data_dir()).glob(f"{country}*climate*"):
                if f.suffix == '.parquet' or f.suffix == '.csv':
                    df = pd.read_parquet(f) if f.suffix == '.parquet' else pd.read_csv(f)
                    climate_data[country] = df
                    break

    # Load FAOSTAT
    for country in countries:
        faostat_file = Path(raw_faostat_path) if raw_faostat_path else Path(get_raw_data_dir()) / f"{country}_faostat.parquet"
        if faostat_file.exists():
            faostat_data[country] = pd.read_parquet(faostat_file)
        else:
            for f in Path(get_raw_data_dir()).glob(f"{country}*faostat*"):
                if f.suffix == '.parquet' or f.suffix == '.csv':
                    df = pd.read_parquet(f) if f.suffix == '.parquet' else pd.read_csv(f)
                    faostat_data[country] = df
                    break

    if not lsms_data:
        raise FileNotFoundError("No LSMS data found in raw directory. Run download pipeline first.")

    # Clean and Merge
    logger.info("Starting clean and merge...")
    df_merged = clean_and_merge(lsms_data, climate_data, faostat_data)
    
    # T018b: Calculate Merge Success Rate
    # "Number of successfully merged records" / "Total available non-duplicate LSMS records" * 100
    total_lsms_records = sum(len(df) for df in lsms_data.values())
    merged_records = len(df_merged)
    
    # Calculate missingness rate for key predictors
    key_cols = ['hdds', 'csa_index', 'digital_access', 'finance_access']
    missing_cols = [col for col in key_cols if col in df_merged.columns]
    if missing_cols:
        missingness = df_merged[missing_cols].isna().sum().sum() / (len(df_merged) * len(missing_cols))
    else:
        missingness = 0.0

    merge_stats = {
        "merge_success_rate_pct": (merged_records / total_lsms_records * 100) if total_lsms_records > 0 else 0.0,
        "total_available_records": total_lsms_records,
        "merged_records": merged_records,
        "missingness_rate": float(missingness)
    }
    
    stats_path = Path(processed_dir) / "merge_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(merge_stats, f, indent=2)
    logger.info(f"Merge stats written to {stats_path}")

    # Imputation
    logger.info("Applying imputation...")
    df_imputed, imp_report = apply_imputation(df_merged)
    
    # Validate
    if not validate_imputation_quality(df_imputed):
        logger.warning("Imputation validation failed.")

    # T018: Stratified Sampling & IPW Weights
    # Check memory limit (7GB)
    # Estimate memory: len * width * 8 bytes (rough)
    estimated_mb = df_imputed.memory_usage(deep=True).sum() / (1024 * 1024)
    should_sample = estimated_mb > 7000  # 7GB threshold

    if should_sample:
        logger.info(f"Data size {estimated_mb:.2f}MB > 7GB. Applying stratified sampling.")
        # Stratify by country
        strata = df_imputed['country'].unique()
        target_n_per_stratum = 5000
        
        sampled_dfs = []
        ipw_data = []
        
        for stratum in strata:
            df_stratum = df_imputed[df_imputed['country'] == stratum]
            n_stratum = len(df_stratum)
            
            if n_stratum > target_n_per_stratum:
                # Sample
                df_sample = df_stratum.sample(n=target_n_per_stratum, random_state=42)
                sampling_frac = target_n_per_stratum / n_stratum
            else:
                df_sample = df_stratum
                sampling_frac = 1.0
            
            sampled_dfs.append(df_sample)
            ipw_data.append({
                'country': stratum,
                'stratum_size': n_stratum,
                'sample_size': len(df_sample),
                'sampling_fraction': sampling_frac,
                'ipw': 1.0 / sampling_frac if sampling_frac > 0 else 0.0
            })
        
        df_final = pd.concat(sampled_dfs, ignore_index=True)
        df_ipw = pd.DataFrame(ipw_data)
    else:
        logger.info(f"Data size {estimated_mb:.2f}MB <= 7GB. Retaining all data.")
        df_final = df_imputed
        # Create IPW weights for full data (weight = 1)
        strata = df_final['country'].unique()
        ipw_data = []
        for stratum in strata:
            n_stratum = len(df_final[df_final['country'] == stratum])
            ipw_data.append({
                'country': stratum,
                'stratum_size': n_stratum,
                'sample_size': n_stratum,
                'sampling_fraction': 1.0,
                'ipw': 1.0
            })
        df_ipw = pd.DataFrame(ipw_data)

    # Verify target N >= 5000 per country
    for stratum in df_final['country'].unique():
        n = len(df_final[df_final['country'] == stratum])
        if n < 5000:
            logger.warning(f"Target N >= 5000 for {stratum} not met. Available: {n}.")

    # Output
    output_file = Path(output_path) if output_path else Path(processed_dir) / "merged_sample.parquet"
    df_final.to_parquet(output_file, index=False)
    logger.info(f"Final dataset written to {output_file}")

    # Output IPW weights
    ipw_file = Path(ipw_output_path) if ipw_output_path else Path(processed_dir) / "ipw_weights.parquet"
    df_ipw.to_parquet(ipw_file, index=False)
    logger.info(f"IPW weights written to {ipw_file}")

def main():
    """Entry point for the clean pipeline."""
    run_sampling_pipeline()

if __name__ == "__main__":
    main()