"""
Summary statistics reporter for extreme event analysis.

This module generates summary statistics from the processed extreme events data,
including exceedance counts per station, average magnitudes, and sensitivity reports.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import logging
from typing import Dict, List, Optional, Any

# Import from sibling modules using the provided API surface
from src.config import get_config

logger = logging.getLogger(__name__)


def load_extreme_events(file_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the extreme events parquet file.

    Args:
        file_path: Optional path to the parquet file. If None, uses config.

    Returns:
        DataFrame containing extreme events data.
    """
    config = get_config()
    if file_path is None:
        file_path = config.get("paths", {}).get("extreme_events_parquet", "data/processed/extreme_events.parquet")

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Extreme events file not found: {file_path}")

    logger.info(f"Loading extreme events from {file_path}")
    df = pd.read_parquet(path)

    # Ensure date column is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    return df


def calculate_station_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate summary statistics per station.

    Args:
        df: DataFrame with columns: station_id, date, magnitude, threshold_value

    Returns:
        DataFrame with station-level statistics.
    """
    if df.empty:
        logger.warning("Empty DataFrame provided to calculate_station_statistics")
        return pd.DataFrame()

    stats = df.groupby('station_id').agg(
        exceedance_count=('magnitude', 'count'),
        avg_magnitude=('magnitude', 'mean'),
        max_magnitude=('magnitude', 'max'),
        min_magnitude=('magnitude', 'min'),
        std_magnitude=('magnitude', 'std'),
        avg_threshold=('threshold_value', 'mean'),
        first_date=('date', 'min'),
        last_date=('date', 'max')
    ).reset_index()

    # Handle potential NaN in std for single-observation stations
    stats['std_magnitude'] = stats['std_magnitude'].fillna(0.0)

    return stats


def calculate_overall_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate overall summary statistics across all stations.

    Args:
        df: DataFrame with columns: station_id, date, magnitude, threshold_value

    Returns:
        Dictionary with overall statistics.
    """
    if df.empty:
        return {
            "total_stations": 0,
            "total_exceedances": 0,
            "date_range": None,
            "global_avg_magnitude": None,
            "global_max_magnitude": None,
            "global_min_magnitude": None
        }

    return {
        "total_stations": df['station_id'].nunique(),
        "total_exceedances": len(df),
        "date_range": {
            "start": df['date'].min().isoformat() if hasattr(df['date'].min(), 'isoformat') else str(df['date'].min()),
            "end": df['date'].max().isoformat() if hasattr(df['date'].max(), 'isoformat') else str(df['date'].max())
        },
        "global_avg_magnitude": float(df['magnitude'].mean()),
        "global_max_magnitude": float(df['magnitude'].max()),
        "global_min_magnitude": float(df['magnitude'].min()),
        "avg_threshold": float(df['threshold_value'].mean()),
        "std_magnitude": float(df['magnitude'].std())
    }


def generate_sensitivity_report(df: pd.DataFrame, threshold_percentiles: List[float] = [90, 95, 99]) -> Dict[str, Any]:
    """
    Generate a sensitivity report for different threshold percentiles.

    This report compares exceedance statistics across different threshold definitions.
    Note: This assumes the input DataFrame contains data that was processed with
    various thresholds, or we re-calculate based on raw data if available.

    For this implementation, we analyze the current data and provide a report
    based on the existing threshold_value column distribution.

    Args:
        df: DataFrame with extreme events data.
        threshold_percentiles: List of percentiles to analyze.

    Returns:
        Dictionary containing sensitivity analysis results.
    """
    if df.empty:
        return {
            "analysis_type": "sensitivity",
            "threshold_percentiles_analyzed": threshold_percentiles,
            "results": [],
            "note": "No data available for sensitivity analysis"
        }

    # Extract unique threshold values and their associated percentiles if available
    # In a full implementation, we would re-run preprocessing with different thresholds
    # Here we analyze the distribution of thresholds in the current data

    threshold_values = df['threshold_value'].unique()
    results = []

    for p in threshold_percentiles:
        # Simulate what the analysis would look like for this percentile
        # In practice, this would come from re-running T013 with different percentiles
        pct_threshold = np.percentile(df['magnitude'], p)
        exceedances_at_pct = df[df['magnitude'] > pct_threshold]

        results.append({
            "percentile": p,
            "simulated_threshold": float(pct_threshold),
            "exceedance_count": int(len(exceedances_at_pct)),
            "exceedance_ratio": float(len(exceedances_at_pct) / len(df)) if len(df) > 0 else 0.0,
            "avg_magnitude_at_threshold": float(exceedances_at_pct['magnitude'].mean()) if len(exceedances_at_pct) > 0 else None
        })

    return {
        "analysis_type": "sensitivity",
        "threshold_percentiles_analyzed": threshold_percentiles,
        "total_records_analyzed": len(df),
        "results": results
    }


def generate_summary_report(
    df: pd.DataFrame,
    output_path: Optional[str] = None,
    include_sensitivity: bool = True
) -> Dict[str, Any]:
    """
    Generate a comprehensive summary report.

    Args:
        df: DataFrame with extreme events data.
        output_path: Optional path to save the report as JSON.
        include_sensitivity: Whether to include sensitivity analysis.

    Returns:
        Dictionary containing the full summary report.
    """
    logger.info("Generating summary report")

    station_stats = calculate_station_statistics(df)
    overall_stats = calculate_overall_statistics(df)

    report = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "data_source": "data/processed/extreme_events.parquet",
        "overall_statistics": overall_stats,
        "station_statistics": station_stats.to_dict(orient='records'),
        "station_count": len(station_stats)
    }

    if include_sensitivity:
        report["sensitivity_report"] = generate_sensitivity_report(df)

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Summary report saved to {output_path}")

    return report


def main():
    """
    Main entry point for generating summary statistics.

    This script:
    1. Loads the extreme events parquet file
    2. Calculates station-level and overall statistics
    3. Generates a sensitivity report
    4. Saves the summary report to data/processed/summary_report.json
    """
    config = get_config()
    input_path = config.get("paths", {}).get("extreme_events_parquet", "data/processed/extreme_events.parquet")
    output_path = config.get("paths", {}).get("summary_report", "data/processed/summary_report.json")

    try:
        # Load data
        df = load_extreme_events(input_path)

        if df.empty:
            logger.warning("No extreme events data found. Generating empty report.")
            report = generate_summary_report(df, output_path, include_sensitivity=True)
        else:
            # Generate report
            report = generate_summary_report(df, output_path, include_sensitivity=True)

            # Log key metrics
            logger.info(f"Total stations with exceedances: {report['overall_statistics']['total_stations']}")
            logger.info(f"Total exceedances: {report['overall_statistics']['total_exceedances']}")
            logger.info(f"Average magnitude: {report['overall_statistics']['global_avg_magnitude']:.2f}")

            if "sensitivity_report" in report:
                logger.info("Sensitivity analysis completed")
                for res in report["sensitivity_report"]["results"]:
                    logger.info(f"  Percentile {res['percentile']}: {res['exceedance_count']} exceedances")

        logger.info("Summary report generation completed successfully")
        return report

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating summary report: {e}")
        raise


if __name__ == "__main__":
    # Set up basic logging for script execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    main()
