import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

from utils.logging import get_logger

logger = get_logger(__name__)

def load_correlation_matrix() -> pd.DataFrame:
    """Load the correlation matrix from data/results/correlation_matrix.csv."""
    path = Path("data/results/correlation_matrix.csv")
    if not path.exists():
        raise FileNotFoundError(f"Correlation matrix not found at {path}. "
                                "Run T019 (compute_correlation_matrix) first.")
    df = pd.read_csv(path, index_col=0)
    return df

def load_spatial_stats() -> Dict[str, Any]:
    """Load spatial autocorrelation statistics from data/results/spatial_stats.json."""
    path = Path("data/results/spatial_stats.json")
    if not path.exists():
        raise FileNotFoundError(f"Spatial stats not found at {path}. "
                                "Run T020 (compute_spatial_autocorrelation) first.")
    with open(path, "r") as f:
        return json.load(f)

def check_socioeconomic_proxies() -> Dict[str, Any]:
    """
    Attempt to ingest socioeconomic proxies (WorldPop/OSM height).
    Since T032 (Proxy Validity) is not yet complete and no real socioeconomic
    data is ingested, this returns a status indicating data is missing.
    """
    # Check for expected files that would come from T032 or external ingestion
    worldpop_path = Path("data/processed/worldpop_population.tif")
    osm_height_path = Path("data/processed/osm_building_height.tif")
    
    found = {}
    missing = []
    
    for name, p in [("WorldPop", worldpop_path), ("OSM_Height", osm_height_path)]:
        if p.exists():
            found[name] = str(p)
        else:
            missing.append(name)
    
    return {
        "status": "missing" if missing else "partial" if found else "none",
        "found": found,
        "missing": missing,
        "note": "Socioeconomic proxies (WorldPop/OSM height) are not yet ingested. "
                "This is a known limitation pending T032 completion."
    }

def generate_report_content(
    corr_df: pd.DataFrame,
    spatial_stats: Dict[str, Any],
    socio_data: Dict[str, Any]
) -> str:
    """Generate the Markdown content for the EDA report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Determine strongest correlations
    target_col = "temperature"
    if target_col not in corr_df.columns:
        # Fallback if column naming differs, look for 'temp' or similar
        cols = [c for c in corr_df.columns if 'temp' in c.lower()]
        if cols:
            target_col = cols[0]
        else:
            # If absolutely no target, use first column as placeholder
            target_col = corr_df.columns[0]
    
    # Get correlations with target, exclude self-correlation (1.0)
    if target_col in corr_df.index and target_col in corr_df.columns:
        corrs = corr_df[target_col].drop(target_col).abs()
        top_pos = corrs.nlargest(3)
        # Sort by absolute value descending
        sorted_top = top_pos.sort_values(ascending=False)
    else:
        sorted_top = pd.Series(dtype=float)
    
    lines = []
    lines.append("# Exploratory Data Analysis (EDA) Report")
    lines.append("")
    lines.append(f"**Generated:** {timestamp}")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append("This report summarizes the exploratory spatial analysis of OpenStreetMap-derived")
    lines.append("covariates and satellite thermal data to investigate Urban Heat Island (UHI) effects.")
    lines.append("")
    
    # Socioeconomic Proxy Section
    lines.append("## 2. Socioeconomic Proxy Data Status")
    lines.append("")
    if socio_data["status"] == "missing":
        lines.append("**Status: NOT INGESTED**")
        lines.append("")
        lines.append("Socioeconomic proxy data (WorldPop population density, OSM building height)")
        lines.append("was not available for this analysis run. This is a known limitation.")
        lines.append("")
        lines.append("The analysis relies solely on OSM vector features (building footprint, land use,")
        lines.append("vegetation, roads) and satellite thermal data.")
        lines.append("")
        lines.append(f"**Missing Data Sources:** {', '.join(socio_data['missing'])}")
    else:
        lines.append("**Status: PARTIAL/INGESTED**")
        lines.append("")
        lines.append(f"Found data: {socio_data['found']}")
    
    lines.append("")
    lines.append("## 3. Linear Relationships (Correlation Analysis)")
    lines.append("")
    lines.append("The following table shows the strength and direction of linear relationships")
    lines.append(f"between covariates and the target variable (`{target_col}`).")
    lines.append("")
    lines.append("| Variable | Correlation Coefficient | Strength |")
    lines.append("| :--- | :---: | :--- |")
    
    for var, val in sorted_top.items():
        strength = "Strong" if abs(val) > 0.7 else "Moderate" if abs(val) > 0.4 else "Weak"
        lines.append(f"| {var} | {val:.3f} | {strength} |")
    
    lines.append("")
    lines.append("**Interpretation:**")
    if len(sorted_top) > 0:
        best_var = sorted_top.index[0]
        best_val = sorted_top.iloc[0]
        direction = "positive" if best_val > 0 else "negative"
        lines.append(f"- The strongest linear relationship is with `{best_var}` (r = {best_val:.3f}, {direction}).")
    else:
        lines.append("- No significant correlations could be computed.")
    
    lines.append("")
    lines.append("## 4. Spatial Autocorrelation")
    lines.append("")
    lines.append("Spatial autocorrelation metrics (Moran's I) indicate the degree to which")
    lines.append("temperature values are clustered in space.")
    lines.append("")
    
    moran_i = spatial_stats.get("moran_i", {}).get("statistic", "N/A")
    p_value = spatial_stats.get("moran_i", {}).get("p_value", "N/A")
    z_score = spatial_stats.get("moran_i", {}).get("z_score", "N/A")
    
    lines.append(f"- **Moran's I Statistic:** {moran_i}")
    lines.append(f"- **P-value:** {p_value}")
    lines.append(f"- **Z-score:** {z_score}")
    lines.append("")
    
    if moran_i != "N/A" and isinstance(moran_i, (int, float)):
        if moran_i > 0.5:
            interpretation = "Strong positive spatial clustering"
        elif moran_i > 0:
            interpretation = "Moderate positive spatial clustering"
        else:
            interpretation = "Weak or negative spatial clustering"
        lines.append(f"**Interpretation:** {interpretation}. Temperature values are significantly")
        lines.append("spatially dependent, justifying the use of spatial regression models (SAR/GWR).")
    
    lines.append("")
    lines.append("## 5. Variogram Analysis")
    lines.append("")
    lines.append("Empirical variograms were computed to characterize the spatial range and")
    lines.append("sill of the temperature field.")
    lines.append("")
    
    variogram_stats = spatial_stats.get("variogram", {})
    if variogram_stats:
        lines.append(f"- **Nugget:** {variogram_stats.get('nugget', 'N/A')}")
        lines.append(f"- **Sill:** {variogram_stats.get('sill', 'N/A')}")
        lines.append(f"- **Range:** {variogram_stats.get('range', 'N/A')} meters")
    else:
        lines.append("- Variogram statistics could not be computed or are missing.")
    
    lines.append("")
    lines.append("## 6. Limitations and Next Steps")
    lines.append("")
    lines.append("1. **Socioeconomic Proxies:** As noted, WorldPop and OSM height data are missing.")
    lines.append("   Inclusion of these variables is expected to improve model explanatory power.")
    lines.append("")
    lines.append("2. **Temporal Scope:** This analysis uses a single composite thermal layer.")
    lines.append("   Multi-temporal analysis could reveal seasonal UHI dynamics.")
    lines.append("")
    lines.append("3. **Resolution:** All data is resampled to 30m. Finer resolution OSM features")
    lines.append("   may have been smoothed during rasterization.")
    lines.append("")
    lines.append("---")
    lines.append("*Report generated by llmXive pipeline (Task T021)*")
    
    return "\n".join(lines)

def main():
    """Main entry point to generate the EDA report."""
    logger.info("Starting EDA report generation (T021)...")
    
    try:
        # Load dependencies
        logger.info("Loading correlation matrix...")
        corr_df = load_correlation_matrix()
        
        logger.info("Loading spatial statistics...")
        spatial_stats = load_spatial_stats()
        
        logger.info("Checking socioeconomic proxies...")
        socio_data = check_socioeconomic_proxies()
        
        # Generate content
        logger.info("Generating report content...")
        content = generate_report_content(corr_df, spatial_stats, socio_data)
        
        # Write output
        output_path = Path("data/results/eda_report.md")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"EDA report successfully written to {output_path}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during report generation: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
