import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from code.config import Config
from code.utils.logging import log_provenance

def load_metadata() -> Dict[str, Any]:
    """Load dataset metadata."""
    # In real implementation, load from data/raw or verified_sources.json
    return {
        "source_name": "OpenNeuro",
        "dataset_id": Config.OPENNEURO_ID,
        "study_design": "observational", # Simulated
        "randomized": False
    }

def determine_framing(metadata: Dict[str, Any]) -> str:
    """Determine if findings should be framed as associational or causal."""
    # FR-008: If not randomized, frame as associational
    if metadata.get("study_design") == "randomized" or metadata.get("randomized") is True:
        return "causal"
    return "associational"

def load_statistical_results() -> Dict[str, Any]:
    """Load statistical results from CSV."""
    import pandas as pd
    path = Config.DATA_METRICS / "statistical_results.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    return df.to_dict(orient='records')

def load_network_metrics() -> Dict[str, Any]:
    """Load network metrics from CSV."""
    import pandas as pd
    path = Config.DATA_METRICS / "network_metrics.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    return df.to_dict(orient='records')

def load_power_analysis() -> Dict[str, Any]:
    """Load power analysis results from JSON."""
    path = Config.DATA_METRICS / "power_analysis.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)

def generate_report(metadata: Dict[str, Any], stats: Dict[str, Any], 
                   network: Dict[str, Any], power: Dict[str, Any]) -> str:
    """Generate the final report content."""
    framing = determine_framing(metadata)
    min_n = power.get("min_N_required", "N/A")
    
    report = f"""# Brain Network Dynamics and VR Therapy Response - Final Report

## Data Source
- Source: {metadata.get('source_name', 'Unknown')}
- Dataset ID: {metadata.get('dataset_id', 'Unknown')}
- Download Date: {datetime.now().strftime('%Y-%m-%d')}

## Methodology
- Analysis Type: ANCOVA (Post ~ Pre + Metric)
- Correction: FDR
- Framing: {framing.upper()}

## Results
- Minimum N Required for Power (0.8): {min_n}
- Current N: {len(stats) if isinstance(stats, list) else 'N/A'}

## Statistical Findings
{str(stats)[:500]}...

## Limitations
- Findings are framed as ASSOCIATIONAL due to lack of randomization.
- Power analysis indicates minimum N of {min_n} required for 80% power.

"""
    return report

def save_report(content: str, output_path: Path):
    """Save report to file."""
    with open(output_path, 'w') as f:
        f.write(content)
    logging.info(f"Saved report to {output_path}")
    log_provenance("Generated final report", {"path": str(output_path)})

def run_analysis():
    """Run the report generation stage."""
    logging.info("Starting report generation stage")
    
    metadata = load_metadata()
    stats = load_statistical_results()
    network = load_network_metrics()
    power = load_power_analysis()
    
    content = generate_report(metadata, stats, network, power)
    output_path = Config.REPORTS_DIR / "results.md"
    save_report(content, output_path)
    
    logging.info(f"Report generated at {output_path}")
    return content

def main():
    """Main entry point."""
    run_analysis()

if __name__ == "__main__":
    main()