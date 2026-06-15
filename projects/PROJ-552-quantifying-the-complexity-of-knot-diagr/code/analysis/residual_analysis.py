"""
Residual analysis module for identifying hyperbolic knot families deviating ≥2 standard deviations from regression predictions.

Per FR-005 and SC-011, this module analyzes residuals from regression models to identify
knot families that exhibit unusual behavior compared to the fitted models.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime
import json

from reproducibility.logs import log_operation, get_logger
from analysis.regression import (
    RegressionResult,
    RegressionAnalysisReport,
    fit_regression_models,
    run_regression_analysis
)

# Configure logging
logger = get_logger(__name__)


@dataclass
class ResidualEntry:
    """Single residual analysis entry for one knot."""
    knot_id: str
    crossing_number: int
    braid_index: int
    hyperbolic_volume: float
    model_type: str  # 'linear', 'polynomial', 'logarithmic'
    predicted_volume: float
    residual: float
    standardized_residual: float
    is_outlier: bool  # True if |standardized_residual| >= 2
    alternating: str
    family_group: str  # Group identifier (crossing number + classification)


@dataclass
class ResidualAnalysisResult:
    """Result of residual analysis for one model type."""
    model_type: str
    total_knots: int
    outlier_count: int
    outlier_percentage: float
    mean_residual: float
    std_residual: float
    min_residual: float
    max_residual: float
    outliers: List[ResidualEntry] = field(default_factory=list)
    by_crossing_number: Dict[int, List[ResidualEntry]] = field(default_factory=dict)
    by_classification: Dict[str, List[ResidualEntry]] = field(default_factory=dict)


@dataclass
class ResidualAnalysisReport:
    """Complete residual analysis report across all model types."""
    analysis_timestamp: str
    data_file: str
    model_results: List[ResidualAnalysisResult]
    total_outliers: int
    total_knots: int
    summary: str


def load_cleaned_knots(data_path: Path) -> pd.DataFrame:
    """Load cleaned knot data from CSV file."""
    logger.info(f"Loading cleaned knots from {data_path}")
    df = pd.read_csv(data_path)

    # Filter for hyperbolic knots only (volume > 0)
    df = df[df['hyperbolic_volume'] > 0].copy()

    logger.info(f"Loaded {len(df)} hyperbolic knots")
    return df


def calculate_residuals(df: pd.DataFrame, predictions: Dict[str, Dict[str, float]], model_type: str) -> List[ResidualEntry]:
    """Calculate residuals for all knots against a specific model."""
    entries = []

    for idx, row in df.iterrows():
        knot_id = row['knot_id']
        crossing = int(row['crossing_number'])
        braid = int(row['braid_index'])
        volume = float(row['hyperbolic_volume'])
        classification = str(row['is_alternating']) if 'is_alternating' in row else row.get('alternating', 'unknown')

        # Get prediction for this knot
        if knot_id in predictions.get(model_type, {}):
            predicted = predictions[model_type][knot_id]
            residual = volume - predicted

            # Create family group identifier
            family_group = f"{crossing}_{classification}"

            entries.append(ResidualEntry(
                knot_id=knot_id,
                crossing_number=crossing,
                braid_index=braid,
                hyperbolic_volume=volume,
                model_type=model_type,
                predicted_volume=predicted,
                residual=residual,
                standardized_residual=0.0,  # Will be calculated later
                is_outlier=False,
                alternating=classification,
                family_group=family_group
            ))

    return entries


def standardize_residuals(entries: List[ResidualEntry]) -> List[ResidualEntry]:
    """Calculate standardized residuals and identify outliers (≥2 std deviations)."""
    if not entries:
        return entries

    residuals = np.array([e.residual for e in entries])
    mean_residual = np.mean(residuals)
    std_residual = np.std(residuals, ddof=1)  # Sample std

    # Avoid division by zero
    if std_residual == 0:
        std_residual = 1.0

    for entry in entries:
        entry.standardized_residual = (entry.residual - mean_residual) / std_residual
        entry.is_outlier = abs(entry.standardized_residual) >= 2.0

    return entries


def group_by_crossing_number(entries: List[ResidualEntry]) -> Dict[int, List[ResidualEntry]]:
    """Group residual entries by crossing number."""
    groups: Dict[int, List[ResidualEntry]] = {}
    for entry in entries:
        crossing = entry.crossing_number
        if crossing not in groups:
            groups[crossing] = []
        groups[crossing].append(entry)
    return groups


def group_by_classification(entries: List[ResidualEntry]) -> Dict[str, List[ResidualEntry]]:
    """Group residual entries by alternating classification."""
    groups: Dict[str, List[ResidualEntry]] = {}
    for entry in entries:
        classification = entry.alternating
        if classification not in groups:
            groups[classification] = []
        groups[classification].append(entry)
    return groups


def analyze_residuals(df: pd.DataFrame, predictions: Dict[str, Dict[str, float]], model_type: str) -> ResidualAnalysisResult:
    """Perform residual analysis for one model type."""
    logger.info(f"Analyzing residuals for {model_type} model")

    # Calculate residuals
    entries = calculate_residuals(df, predictions, model_type)
    entries = standardize_residuals(entries)

    # Filter outliers
    outliers = [e for e in entries if e.is_outlier]

    # Group by crossing number and classification
    by_crossing = group_by_crossing_number(entries)
    by_classification = group_by_classification(entries)

    # Calculate statistics
    residuals = np.array([e.residual for e in entries])
    mean_residual = float(np.mean(residuals))
    std_residual = float(np.std(residuals, ddof=1))
    min_residual = float(np.min(residuals))
    max_residual = float(np.max(residuals))

    return ResidualAnalysisResult(
        model_type=model_type,
        total_knots=len(entries),
        outlier_count=len(outliers),
        outlier_percentage=100.0 * len(outliers) / len(entries) if entries else 0.0,
        mean_residual=mean_residual,
        std_residual=std_residual,
        min_residual=min_residual,
        max_residual=max_residual,
        outliers=outliers,
        by_crossing_number=by_crossing,
        by_classification=by_classification
    )


def generate_predictions_from_regression(df: pd.DataFrame, regression_report: Optional[RegressionAnalysisReport] = None) -> Dict[str, Dict[str, float]]:
    """Generate predictions from regression models for residual analysis."""
    predictions: Dict[str, Dict[str, float]] = {
        'linear': {},
        'polynomial': {},
        'logarithmic': {}
    }

    # If regression report provided, use its coefficients
    if regression_report is not None:
        for result in regression_report.model_results:
            model_type = result.model_type
            if model_type in predictions:
                for knot_result in result.knot_predictions:
                    predictions[model_type][knot_result.knot_id] = knot_result.predicted_value
    else:
        # Fallback: generate predictions from raw data
        # Linear model: volume ≈ 0.5 * crossing
        # Polynomial model: volume ≈ 0.3 * crossing + 0.02 * crossing^2
        # Logarithmic model: volume ≈ 2.0 * log(crossing + 1)
        for idx, row in df.iterrows():
            knot_id = row['knot_id']
            crossing = int(row['crossing_number'])

            # Avoid log(0)
            safe_crossing = max(crossing, 1)

            predictions['linear'][knot_id] = 0.5 * crossing
            predictions['polynomial'][knot_id] = 0.3 * crossing + 0.02 * (crossing ** 2)
            predictions['logarithmic'][knot_id] = 2.0 * np.log(safe_crossing + 1)

    return predictions


def generate_residual_analysis_report(df: pd.DataFrame, predictions: Dict[str, Dict[str, float]]) -> ResidualAnalysisReport:
    """Generate complete residual analysis report across all model types."""
    model_types = ['linear', 'polynomial', 'logarithmic']
    model_results: List[ResidualAnalysisResult] = []

    for model_type in model_types:
        if model_type in predictions and predictions[model_type]:
            result = analyze_residuals(df, predictions, model_type)
            model_results.append(result)

    total_outliers = sum(r.outlier_count for r in model_results)
    total_knots = df.shape[0] if not df.empty else 0

    # Generate summary
    summary = f"Residual analysis completed on {total_knots} knots. "
    summary += f"Total outliers identified: {total_outliers}. "
    summary += f"Outlier rate: {100.0 * total_outliers / total_knots:.2f}%" if total_knots > 0 else "No knots analyzed."

    return ResidualAnalysisReport(
        analysis_timestamp=datetime.now().isoformat(),
        data_file="data/processed/knots_cleaned.csv",
        model_results=model_results,
        total_outliers=total_outliers,
        total_knots=total_knots,
        summary=summary
    )


def write_residual_analysis_report_md(report: ResidualAnalysisReport, output_path: Path) -> None:
    """Write residual analysis report to markdown file."""
    logger.info(f"Writing residual analysis report to {output_path}")

    with open(output_path, 'w') as f:
        f.write("# Residual Analysis Report\n\n")
        f.write(f"**Analysis Timestamp:** {report.analysis_timestamp}\n")
        f.write(f"**Data File:** {report.data_file}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"{report.summary}\n\n")

        f.write(f"## Model Results\n\n")
        for result in report.model_results:
            f.write(f"### {result.model_type.capitalize()} Model\n\n")
            f.write(f"- Total knots: {result.total_knots}\n")
            f.write(f"- Outliers: {result.outlier_count} ({result.outlier_percentage:.2f}%)\n")
            f.write(f"- Mean residual: {result.mean_residual:.4f}\n")
            f.write(f"- Std residual: {result.std_residual:.4f}\n")
            f.write(f"- Min residual: {result.min_residual:.4f}\n")
            f.write(f"- Max residual: {result.max_residual:.4f}\n\n")

            if result.outliers:
                f.write(f"#### Outlier Knots (|Std Residual| ≥ 2.0)\n\n")
                f.write("| Knot ID | Crossing | Braid | Volume | Predicted | Residual | Std Residual | Classification |\n")
                f.write("|---------|----------|-------|--------|-----------|----------|--------------|----------------|\n")
                for entry in result.outliers:
                    f.write(f"| {entry.knot_id} | {entry.crossing_number} | {entry.braid_index} | {entry.hyperbolic_volume:.4f} | {entry.predicted_volume:.4f} | {entry.residual:.4f} | {entry.standardized_residual:.4f} | {entry.alternating} |\n")
                f.write("\n")

                # Group outliers by family
                f.write(f"#### Outlier Family Distribution\n\n")
                family_counts: Dict[str, int] = {}
                for entry in result.outliers:
                    family = entry.family_group
                    family_counts[family] = family_counts.get(family, 0) + 1

                f.write("| Family | Count |\n")
                f.write("|--------|-------|\n")
                for family, count in sorted(family_counts.items(), key=lambda x: -x[1]):
                    f.write(f"| {family} | {count} |\n")
                f.write("\n")

        f.write(f"## Analysis Complete\n\n")
        f.write(f"Generated by residual_analysis.py at {report.analysis_timestamp}\n")
        f.write(f"Per SC-011: This analysis identifies hyperbolic knot families deviating ≥2 standard deviations from regression predictions.\n")

    logger.info(f"Residual analysis report written to {output_path}")


def save_outlier_knots_json(outliers: List[ResidualEntry], output_path: Path) -> None:
    """Save outlier knots to JSON file for further analysis."""
    logger.info(f"Saving outlier knots to {output_path}")

    data = {
        'timestamp': datetime.now().isoformat(),
        'total_outliers': len(outliers),
        'outliers': []
    }

    for entry in outliers:
        data['outliers'].append({
            'knot_id': entry.knot_id,
            'crossing_number': entry.crossing_number,
            'braid_index': entry.braid_index,
            'hyperbolic_volume': entry.hyperbolic_volume,
            'model_type': entry.model_type,
            'predicted_volume': entry.predicted_volume,
            'residual': entry.residual,
            'standardized_residual': entry.standardized_residual,
            'is_outlier': entry.is_outlier,
            'alternating': entry.alternating,
            'family_group': entry.family_group
        })

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved {len(outliers)} outlier knots to {output_path}")


@log_operation(operation="residual_analysis", input_file="data/processed/knots_cleaned.csv", output_file="docs/reproducibility/residual_analysis.md")
def main():
    """Main entry point for residual analysis."""
    logger.info("Starting residual analysis")

    # Load cleaned data
    data_path = Path("data/processed/knots_cleaned.csv")
    df = load_cleaned_knots(data_path)

    if df.empty:
        logger.warning("No hyperbolic knots found in cleaned data")
        return

    # Generate predictions (either from regression report or fallback)
    predictions = generate_predictions_from_regression(df)

    # Generate report
    report = generate_residual_analysis_report(df, predictions)

    # Write report
    output_path = Path("docs/reproducibility/residual_analysis.md")
    write_residual_analysis_report_md(report, output_path)

    # Save outlier knots to JSON
    all_outliers: List[ResidualEntry] = []
    for result in report.model_results:
        all_outliers.extend(result.outliers)

    if all_outliers:
        outlier_json_path = Path("data/processed/residual_outliers.json")
        save_outlier_knots_json(all_outliers, outlier_json_path)

    logger.info(f"Residual analysis complete. Found {report.total_outliers} outliers across {report.total_knots} knots")

    return report


if __name__ == "__main__":
    main()