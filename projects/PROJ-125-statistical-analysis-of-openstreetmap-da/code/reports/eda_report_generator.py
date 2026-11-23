"""
EDA Report Generator for User Story 2.

Generates a markdown summary report based on correlation matrices,
spatial autocorrelation statistics, and socioeconomic proxy availability.
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from config import get_path
from utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)


def load_correlation_matrix() -> Optional[Dict[str, Any]]:
    """
    Load the correlation matrix from the results directory.
    
    Returns:
        Dictionary containing correlation data or None if file missing.
    """
    path = get_path("data/results/correlation_matrix.csv")
    if not os.path.exists(path):
        logger.warning(f"Correlation matrix not found at {path}. Skipping correlation section.")
        return None
    
    try:
        import pandas as pd
        df = pd.read_csv(path)
        
        # Convert to a JSON-serializable dict structure for the report
        # Assuming first column is variable names, rest are correlations
        if df.empty:
            logger.warning("Correlation matrix is empty.")
            return None
        
        variables = df.iloc[:, 0].tolist()
        correlations = {}
        
        for i, var in enumerate(variables):
            correlations[var] = {}
            for j, other_var in enumerate(variables):
                # Handle potential float conversion issues
                val = df.iloc[i, j]
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    val = str(val)
                correlations[var][other_var] = val
        
        return {
            "variables": variables,
            "matrix": correlations,
            "source_path": str(path)
        }
    except Exception as e:
        logger.error(f"Failed to parse correlation matrix: {e}")
        return None


def load_spatial_stats() -> Optional[Dict[str, Any]]:
    """
    Load spatial autocorrelation statistics from the results directory.
    
    Returns:
        Dictionary containing spatial stats or None if file missing.
    """
    path = get_path("data/results/spatial_stats.json")
    if not os.path.exists(path):
        logger.warning(f"Spatial stats not found at {path}. Skipping spatial stats section.")
        return None
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Failed to parse spatial stats: {e}")
        return None


def check_socioeconomic_proxies() -> Dict[str, Any]:
    """
    Check if socioeconomic proxies were successfully ingested.
    
    Returns:
        Dictionary with availability status and path.
    """
    path = get_path("data/processed/socioeconomic_proxies.tif")
    exists = os.path.exists(path)
    
    return {
        "available": exists,
        "path": str(path) if exists else None,
        "message": "Socioeconomic proxies (WorldPop/OSM height) included." if exists else "Socioeconomic proxies unavailable (T021a warning logged during ingestion)."
    }


def interpret_morans_i(moran_i: float, p_value: Optional[float] = None) -> str:
    """
    Generate a textual interpretation of Moran's I statistic.
    """
    if moran_i > 0.5:
        strength = "strong"
    elif moran_i > 0.2:
        strength = "moderate"
    elif moran_i > 0:
        strength = "weak"
    else:
        strength = "negligible or negative"
    
    direction = "positive spatial autocorrelation" if moran_i > 0 else "negative spatial autocorrelation"
    
    significance = ""
    if p_value is not None:
        if p_value < 0.05:
            significance = " (statistically significant)"
        else:
            significance = " (not statistically significant)"
    
    return f"The temperature data exhibits {strength} {direction}{significance} (I={moran_i:.4f}{significance})."


def interpret_correlations(correlations: Dict[str, Dict[str, float]], target_var: str = "temperature") -> str:
    """
    Generate a summary of linear relationships.
    """
    if not correlations:
        return "No correlation data available."
    
    if target_var not in correlations:
        # Try to find a key that looks like temperature
        keys = [k for k in correlations.keys() if "temp" in k.lower()]
        if keys:
            target_var = keys[0]
        else:
            return f"Target variable '{target_var}' not found in correlation matrix keys: {list(correlations.keys())}."
    
    summary = []
    # Get correlations for the target variable
    target_corrs = correlations[target_var]
    
    # Sort by absolute value
    sorted_vars = sorted(target_corrs.items(), key=lambda x: abs(x[1]) if isinstance(x[1], float) else 0, reverse=True)
    
    for var, val in sorted_vars:
        if var == target_var:
            continue
        if not isinstance(val, float):
            continue
        
        direction = "positive" if val > 0 else "negative"
        strength = "strong" if abs(val) > 0.7 else "moderate" if abs(val) > 0.4 else "weak"
        summary.append(f"{strength} {direction} relationship with {var} (r={val:.3f})")
    
    if not summary:
        return "No significant linear relationships identified."
        
    return "; ".join(summary)


def generate_report_content(
    correlation_data: Optional[Dict[str, Any]],
    spatial_data: Optional[Dict[str, Any]],
    proxy_info: Dict[str, Any]
) -> str:
    """
    Assemble the markdown report content.
    """
    lines = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines.append("# Exploratory Data Analysis (EDA) Report")
    lines.append(f"**Generated:** {timestamp}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Section 1: Spatial Autocorrelation
    lines.append("## 1. Spatial Autocorrelation Analysis")
    lines.append("")
    
    if spatial_data:
        moran_i = spatial_data.get("temperature", {}).get("moran_i")
        p_value = spatial_data.get("temperature", {}).get("p_value")
        
        if moran_i is not None:
            lines.append(interpret_morans_i(moran_i, p_value))
            lines.append("")
            
            # Include variogram info if available
            if "variogram" in spatial_data:
                lines.append("**Variogram Analysis:**")
                lines.append(f"- Range: {spatial_data['variogram'].get('range', 'N/A')}")
                lines.append(f"- Nugget: {spatial_data['variogram'].get('nugget', 'N/A')}")
                lines.append(f"- Sill: {spatial_data['variogram'].get('sill', 'N/A')}")
                lines.append("")
        else:
            lines.append("Moran's I statistic could not be computed or retrieved.")
            lines.append("")
    else:
        lines.append("Spatial statistics file not found. Autocorrelation analysis could not be performed.")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Section 2: Correlation Analysis
    lines.append("## 2. Correlation Analysis")
    lines.append("")
    
    if correlation_data:
        lines.append("### Linear Relationships with Temperature")
        lines.append("")
        summary = interpret_correlations(correlation_data.get("matrix", {}))
        lines.append(summary)
        lines.append("")
        
        lines.append("### Full Correlation Matrix")
        lines.append("")
        lines.append("| Variable | ")
        header_row = correlation_data.get("variables", [])
        lines.append(" | ".join([f"{v[:15]}..." if len(v) > 15 else v for v in header_row]))
        lines.append("|")
        lines.append("|" + "---|" * len(header_row))
        
        matrix = correlation_data.get("matrix", {})
        for var in header_row:
            row_vals = matrix.get(var, {})
            row_strs = []
            for other_var in header_row:
                val = row_vals.get(other_var, "N/A")
                if isinstance(val, float):
                    row_strs.append(f"{val:.3f}")
                else:
                    row_strs.append(str(val))
            lines.append(f"| {var[:15]}... | " + " | ".join(row_strs))
        lines.append("")
    else:
        lines.append("Correlation matrix not found. Linear relationships could not be analyzed.")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Section 3: Socioeconomic Proxies
    lines.append("## 3. Socioeconomic Proxies")
    lines.append("")
    lines.append(proxy_info["message"])
    lines.append("")
    if proxy_info["available"]:
        lines.append(f"**Source File:** `{proxy_info['path']}`")
        lines.append("")
        lines.append("These proxies (WorldPop population density and/or OSM building heights) were successfully ingested and aligned with the thermal raster stack.")
    else:
        lines.append("Note: The ingestion of socioeconomic proxies (T021a) encountered issues or the data source was unavailable. The analysis proceeded without this layer.")
    lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("*End of Report*")
    
    return "\n".join(lines)


def main():
    """
    Main entry point to generate the EDA report.
    """
    logger.info("Starting EDA Report Generation (T021)...")
    
    # Load dependencies
    correlation_data = load_correlation_matrix()
    spatial_data = load_spatial_stats()
    proxy_info = check_socioeconomic_proxies()
    
    # Generate content
    report_content = generate_report_content(correlation_data, spatial_data, proxy_info)
    
    # Write output
    output_path = get_path("data/results/eda_report.md")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        logger.info(f"EDA report successfully written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write report to {output_path}: {e}")
        raise


if __name__ == "__main__":
    main()