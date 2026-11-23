import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from utils.config import get_data_dir

logger = get_logger(__name__)

def load_processed_data_stats() -> Dict[str, Any]:
    """
    Load the processed dataset with 3D conformers and SASA values.
    This function reads the output from T015 (processes_with_3d.parquet).
    
    Returns:
        Dict containing 'sasa_values' (list of floats) and 'count' (int).
    """
    data_dir = get_data_dir()
    processed_file = data_dir / "processed" / "graphs_with_3d.parquet"
    
    if not processed_file.exists():
        raise FileNotFoundError(
            f"Processed data file not found: {processed_file}. "
            "Ensure T015 has completed successfully."
        )
    
    try:
        import pandas as pd
        df = pd.read_parquet(processed_file)
        
        if 'sasa' not in df.columns:
            raise ValueError(
                f"Column 'sasa' not found in {processed_file}. "
                "Available columns: {list(df.columns)}"
            )
        
        sasa_values = df['sasa'].dropna().tolist()
        
        if not sasa_values:
            raise ValueError("No valid SASA values found in the dataset.")
        
        return {
            'sasa_values': sasa_values,
            'count': len(sasa_values)
        }
    except ImportError:
        logger.error("pandas and pyarrow are required to read parquet files.")
        raise
    except Exception as e:
        logger.error(f"Error loading processed data: {e}")
        raise

def analyze_sasa_scale(stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate the mean SASA and generate a justification for the scale.
    
    Args:
        stats: Dictionary containing 'sasa_values' and 'count'.
        
    Returns:
        Dictionary with 'mean_sasa', 'min_sasa', 'max_sasa', 'std_sasa',
        'count', and 'justification_source'.
    """
    import numpy as np
    
    sasa_values = np.array(stats['sasa_values'])
    
    mean_sasa = float(np.mean(sasa_values))
    min_sasa = float(np.min(sasa_values))
    max_sasa = float(np.max(sasa_values))
    std_sasa = float(np.std(sasa_values))
    
    # Justification based on typical experimental error for SASA measurements
    # SASA (Solvent Accessible Surface Area) is typically measured in Angstroms squared (Å²)
    # Experimental error is generally small relative to the total surface area of molecules.
    justification_source = "Typical experimental error for SASA calculations is small (< 1 Å²) relative to molecular surface areas which typically range from 50 to 500 Å² for drug-like molecules."
    
    return {
        'mean_sasa': mean_sasa,
        'min_sasa': min_sasa,
        'max_sasa': max_sasa,
        'std_sasa': std_sasa,
        'count': stats['count'],
        'justification_source': justification_source
    }

def main():
    """
    Main entry point for T040: Calculate mean SASA and document scale.
    
    Outputs:
        - results/reports/scale_analysis.json: JSON with mean_sasa and justification.
        - results/reports/scale_analysis.md: Markdown report with analysis details.
    """
    logger.info("Starting T040: Scale Analysis of SASA")
    
    try:
        # Load processed data
        logger.info("Loading processed data with 3D conformers...")
        stats = load_processed_data_stats()
        logger.info(f"Loaded {stats['count']} molecules with SASA values.")
        
        # Analyze scale
        logger.info("Calculating SASA statistics...")
        analysis = analyze_sasa_scale(stats)
        
        # Prepare output directories
        results_dir = project_root / "results" / "reports"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Write JSON output
        json_output_path = results_dir / "scale_analysis.json"
        with open(json_output_path, 'w') as f:
            json.dump(analysis, f, indent=2)
        logger.info(f"Written JSON report to {json_output_path}")
        
        # Write Markdown report
        md_output_path = results_dir / "scale_analysis.md"
        with open(md_output_path, 'w') as f:
            f.write("# SASA Scale Analysis\n\n")
            f.write("## Summary\n\n")
            f.write(f"This report documents the scale of the target variable (SASA) "
                    f"calculated from the processed dataset.\n\n")
            
            f.write("## Statistics\n\n")
            f.write(f"- **Mean SASA**: {analysis['mean_sasa']:.2f} Å²\n")
            f.write(f"- **Min SASA**: {analysis['min_sasa']:.2f} Å²\n")
            f.write(f"- **Max SASA**: {analysis['max_sasa']:.2f} Å²\n")
            f.write(f"- **Std Dev**: {analysis['std_sasa']:.2f} Å²\n")
            f.write(f"- **Sample Size**: {analysis['count']}\n\n")
            
            f.write("## Justification\n\n")
            f.write(f"{analysis['justification_source']}\n\n")
            f.write("The mean SASA value calculated here will be used to contextualize "
                    "model performance metrics (MAE, RMSE) in subsequent tasks.\n")
        
        logger.info(f"Written Markdown report to {md_output_path}")
        logger.info("T040 completed successfully.")
        
        return analysis
        
    except Exception as e:
        logger.error(f"T040 failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
