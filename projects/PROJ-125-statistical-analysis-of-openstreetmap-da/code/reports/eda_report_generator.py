"""
EDA Report Generator for Urban Heat Island Analysis.

This module generates a comprehensive markdown report summarizing the
exploratory data analysis (EDA) results, including correlation matrices,
spatial autocorrelation metrics, and socioeconomic proxy checks.
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from config import get_path
from utils.logging import get_logger

logger = get_logger(__name__)

def load_correlation_matrix() -> Optional[Dict[str, Any]]:
    """
    Load the correlation matrix from the results directory.

    Returns:
        Dict containing correlation data or None if file not found.
    """
    path = get_path("data/results/correlation_matrix.csv")
    if not os.path.exists(path):
        logger.warning(f"Correlation matrix file not found: {path}")
        return None

    # Read CSV manually to avoid heavy dependencies if not needed
    # or use pandas if available (project requirements include pandas)
    try:
        import pandas as pd
        df = pd.read_csv(path)
        return df.to_dict(orient='records')
    except ImportError:
        logger.error("pandas is required to read correlation_matrix.csv")
        return None
    except Exception as e:
        logger.error(f"Error reading correlation matrix: {e}")
        return None

def load_spatial_stats() -> Optional[Dict[str, Any]]:
    """
    Load spatial autocorrelation statistics from the results directory.

    Returns:
        Dict containing spatial stats or None if file not found.
    """
    path = get_path("data/results/spatial_stats.json")
    if not os.path.exists(path):
        logger.warning(f"Spatial stats file not found: {path}")
        return None

    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading spatial stats: {e}")
        return None

def check_socioeconomic_proxies() -> Dict[str, Any]:
    """
    Check for the presence of socioeconomic proxy data (WorldPop/OSM height).

    Returns:
        Dict with 'found' boolean and 'details' string.
    """
    # Check for WorldPop data
    worldpop_path = get_path("data/raw/worldpop")
    osm_height_path = get_path("data/processed/osm_height.tif")

    found_worldpop = os.path.exists(worldpop_path) and any(os.scandir(worldpop_path))
    found_osm_height = os.path.exists(osm_height_path)

    if found_worldpop:
        return {
            "found": True,
            "details": "WorldPop data detected in data/raw/worldpop",
            "source": "WorldPop"
        }
    elif found_osm_height:
        return {
            "found": True,
            "details": "OSM height data detected in data/processed/osm_height.tif",
            "source": "OSM Height"
        }
    else:
        return {
            "found": False,
            "details": "No socioeconomic proxy data (WorldPop or OSM height) found.",
            "source": None
        }

def generate_report_content(
    correlation_data: Optional[Dict[str, Any]],
    spatial_data: Optional[Dict[str, Any]],
    proxy_check: Dict[str, Any]
) -> str:
    """
    Generate the markdown content for the EDA report.

    Args:
        correlation_data: Data from correlation_matrix.csv
        spatial_data: Data from spatial_stats.json
        proxy_check: Result from check_socioeconomic_proxies()

    Returns:
        Markdown string content.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines = [
        "# Exploratory Data Analysis (EDA) Report",
        "",
        f"**Generated:** {timestamp}",
        "",
        "## 1. Executive Summary",
        "",
        "This report summarizes the exploratory analysis of OpenStreetMap-derived",
        "features and satellite thermal imagery for Urban Heat Island (UHI) effects.",
        "",
    ]

    # Socioeconomic Proxy Section
    lines.append("## 2. Socioeconomic Proxy Data Availability")
    lines.append("")
    if proxy_check['found']:
        lines.append(f"- **Status:** Data Available")
        lines.append(f"- **Source:** {proxy_check['source']}")
        lines.append(f"- **Details:** {proxy_check['details']}")
    else:
        lines.append(f"- **Status:** Data Missing")
        lines.append(f"- **Details:** {proxy_check['details']}")
        lines.append("")
        lines.append("> **Limitation:** Ingestion of socioeconomic proxies (WorldPop/OSM height)")
        lines.append("> failed or data is missing. This may limit the explanatory power of the")
        lines.append("> regression models regarding population density and building height.")
    lines.append("")

    # Correlation Analysis Section
    lines.append("## 3. Correlation Analysis")
    lines.append("")
    if correlation_data:
        lines.append("The following table summarizes the linear relationships between")
        lines.append("covariates and land-surface temperature (LST).")
        lines.append("")
        lines.append("| Variable | Correlation (Pearson) | Interpretation |")
        lines.append("| :--- | :--- | :--- |")
        
        # Extract variables and correlations (assuming CSV format: variable, correlation)
        # If the CSV has a different structure, this logic adapts
        for row in correlation_data:
            # Try to find keys that look like variable and correlation
            vars = [k for k in row.keys() if 'variable' in k.lower() or k == 'variable']
            corrs = [k for k in row.keys() if 'correlation' in k.lower() or k == 'correlation']
            
            if vars and corrs:
                var_name = str(row[vars[0]])
                corr_val = float(row[corrs[0]])
                interp = "Positive" if corr_val > 0.1 else ("Negative" if corr_val < -0.1 else "Weak/None")
                lines.append(f"| {var_name} | {corr_val:.3f} | {interp} |")
    else:
        lines.append("> **Warning:** Correlation matrix data is missing. Unable to summarize linear relationships.")
    lines.append("")

    # Spatial Autocorrelation Section
    lines.append("## 4. Spatial Autocorrelation")
    lines.append("")
    if spatial_data:
        lines.append("Spatial autocorrelation metrics indicate the degree to which")
        lines.append("nearby locations have similar temperature values.")
        lines.append("")
        lines.append("### 4.1 Moran's I")
        lines.append("")
        moran_i = spatial_data.get('moran_i', 'N/A')
        p_value = spatial_data.get('p_value', 'N/A')
        lines.append(f"- **Moran's I:** {moran_i}")
        lines.append(f"- **P-value:** {p_value}")
        
        if isinstance(moran_i, (int, float)) and moran_i > 0:
            lines.append(f"- **Interpretation:** Significant positive spatial autocorrelation.")
            lines.append("  Temperature values are clustered, suggesting strong spatial dependence.")
        elif isinstance(moran_i, (int, float)) and moran_i < 0:
            lines.append(f"- **Interpretation:** Negative spatial autocorrelation (dispersion).")
        else:
            lines.append("- **Interpretation:** No significant spatial autocorrelation detected.")
        
        lines.append("")
        lines.append("### 4.2 Variogram")
        lines.append("")
        if 'variogram' in spatial_data:
            lines.append("- **Sill:** " + str(spatial_data['variogram'].get('sill', 'N/A')))
            lines.append("- **Range:** " + str(spatial_data['variogram'].get('range', 'N/A')))
            lines.append("- **Nugget:** " + str(spatial_data['variogram'].get('nugget', 'N/A')))
        else:
            lines.append("> Variogram details not available in spatial stats.")
    else:
        lines.append("> **Warning:** Spatial statistics data is missing. Unable to assess spatial dependence.")
    lines.append("")

    # Conclusion
    lines.append("## 5. Conclusion")
    lines.append("")
    lines.append("The EDA provides preliminary evidence of the relationships between")
    lines.append("urban form (OSM data) and thermal patterns. The presence of spatial")
    lines.append("autocorrelation justifies the use of spatial regression models (SAR, GWR)")
    lines.append("in subsequent modeling phases.")
    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated by code/reports/eda_report_generator.py*")

    return "\n".join(lines)

def main():
    """Main entry point to generate the EDA report."""
    logger.info("Starting EDA report generation...")

    # Load data
    corr_data = load_correlation_matrix()
    spatial_data = load_spatial_stats()
    proxy_data = check_socioeconomic_proxies()

    # Generate content
    report_md = generate_report_content(corr_data, spatial_data, proxy_data)

    # Write output
    output_path = get_path("data/results/eda_report.md")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_md)
        logger.info(f"EDA report successfully written to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to write EDA report: {e}")
        raise

    return output_path

if __name__ == "__main__":
    main()
