"""
metrics.py - Severity Mapping and Metrics Calculation

Implements the conversion of raw scanner labels to NIST-based ordinal ranks
and calculates vulnerability density metrics.
"""
import os
import yaml
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import project configuration
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_severity_map(map_path: str) -> Dict[str, Any]:
    """
    Load the NIST severity mapping configuration from YAML.

    Args:
        map_path: Path to the nist_severity_map.yaml file

    Returns:
        Dictionary containing severity mappings

    Raises:
        FileNotFoundError: If the map file does not exist
        yaml.YAMLError: If the file is not valid YAML
    """
    path = Path(map_path)
    if not path.exists():
        raise FileNotFoundError(f"Severity map file not found: {map_path}")

    with open(path, 'r') as f:
        return yaml.safe_load(f)

def map_severity_to_ordinal(raw_severity: str, scanner: str, severity_map: Dict[str, Any]) -> int:
    """
    Convert a raw scanner severity label to an NIST-based ordinal rank.

    Args:
        raw_severity: The raw severity string from the scanner (e.g., "HIGH", "MEDIUM")
        scanner: The name of the scanner (e.g., "bandit", "semgrep")
        severity_map: The loaded NIST severity mapping configuration

    Returns:
        Integer ordinal rank (1-4) based on NIST guidelines

    Raises:
        ValueError: If the raw severity is not found in the mapping
    """
    # Normalize inputs
    raw_severity = raw_severity.strip().upper()
    scanner = scanner.lower()

    # Get scanner-specific mapping if available, otherwise use default
    scanner_mapping = severity_map.get('scanners', {}).get(scanner, severity_map.get('default', {}))

    # Try to find the mapping
    if raw_severity in scanner_mapping:
        return scanner_mapping[raw_severity]

    # Check for case-insensitive match in keys
    for key, value in scanner_mapping.items():
        if key.upper() == raw_severity:
            return value

    # If not found, raise an error - do not fallback to synthetic/default
    raise ValueError(f"Severity '{raw_severity}' from scanner '{scanner}' not found in NIST mapping. "
                    f"Available keys: {list(scanner_mapping.keys())}")

def process_findings_csv(input_path: str, output_path: str, map_path: str) -> pd.DataFrame:
    """
    Read raw findings CSV, apply severity mapping, and write updated CSV.

    Args:
        input_path: Path to raw_findings.csv
        output_path: Path to write the updated findings CSV
        map_path: Path to nist_severity_map.yaml

    Returns:
        DataFrame containing the processed findings
    """
    # Validate input file exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input findings file not found: {input_path}")

    # Load severity map
    logger.info(f"Loading severity map from {map_path}")
    severity_map = load_severity_map(map_path)

    # Read findings
    logger.info(f"Reading findings from {input_path}")
    df = pd.read_csv(input_path)

    # Verify required columns
    required_cols = ['finding_id', 'snippet_id', 'scanner', 'raw_severity']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in findings CSV: {missing_cols}")

    # Apply mapping
    logger.info("Mapping raw severities to NIST ordinal ranks")
    try:
        df['mapped_ordinal_rank'] = df.apply(
            lambda row: map_severity_to_ordinal(row['raw_severity'], row['scanner'], severity_map),
            axis=1
        )
    except ValueError as e:
        logger.error(f"Severity mapping failed: {e}")
        raise

    # Save output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(df)} findings to {output_path}")

    return df

def calculate_vuln_density(snippet_df: pd.DataFrame, findings_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate vulnerability density (V/100LOC) for each snippet.

    Args:
        snippet_df: DataFrame containing snippet metadata (snippet_id, line_count)
        findings_df: DataFrame containing findings with snippet_id and mapped_ordinal_rank

    Returns:
        DataFrame with snippet_id, line_count, vuln_count, vuln_density, and severity breakdowns
    """
    if snippet_df is None or findings_df is None:
        raise ValueError("Both snippet_df and findings_df must be provided")

    # Ensure required columns exist
    if 'snippet_id' not in snippet_df.columns or 'line_count' not in snippet_df.columns:
        raise ValueError("snippet_df must contain 'snippet_id' and 'line_count' columns")
    if 'snippet_id' not in findings_df.columns:
        raise ValueError("findings_df must contain 'snippet_id' column")

    # Count findings per snippet
    findings_counts = findings_df.groupby('snippet_id').agg(
        vuln_count=('finding_id', 'count'),
        high_severity_count=('mapped_ordinal_rank', lambda x: (x >= 4).sum()),
        medium_severity_count=('mapped_ordinal_rank', lambda x: ((x >= 2) & (x < 4)).sum()),
        low_severity_count=('mapped_ordinal_rank', lambda x: (x == 1).sum())
    ).reset_index()

    # Merge with snippet data
    result = snippet_df.merge(findings_counts, on='snippet_id', how='left')

    # Fill NaN for snippets with no findings
    result['vuln_count'] = result['vuln_count'].fillna(0).astype(int)
    result['high_severity_count'] = result['high_severity_count'].fillna(0).astype(int)
    result['medium_severity_count'] = result['medium_severity_count'].fillna(0).astype(int)
    result['low_severity_count'] = result['low_severity_count'].fillna(0).astype(int)

    # Calculate vulnerability density (V/100LOC)
    # Avoid division by zero
    result['vuln_density'] = (result['vuln_count'] / result['line_count'].replace(0, 1)) * 100

    return result

def main():
    """
    Main entry point for severity mapping and metrics calculation.
    """
    # Define paths based on project structure
    base_dir = Path(__file__).resolve().parent.parent
    input_findings = base_dir / "data" / "findings" / "raw_findings.csv"
    output_findings = base_dir / "data" / "findings" / "findings_with_severity.csv"
    severity_map_path = base_dir / "data" / "mappings" / "nist_severity_map.yaml"

    # Check if input file exists
    if not input_findings.exists():
        logger.error(f"Input file not found: {input_findings}")
        logger.error("Ensure T019 (raw_findings.csv generation) has completed successfully.")
        return 1

    # Check if severity map exists
    if not severity_map_path.exists():
        logger.error(f"Severity map not found: {severity_map_path}")
        logger.error("Ensure T007 (nist_severity_map.yaml generation) has completed successfully.")
        return 1

    try:
        # Process findings and apply mapping
        processed_df = process_findings_csv(
            str(input_findings),
            str(output_findings),
            str(severity_map_path)
        )

        # Load snippets if available for density calculation
        snippets_path = base_dir / "data" / "generated" / "snippets.csv"
        if snippets_path.exists():
            logger.info("Calculating vulnerability density metrics...")
            snippets_df = pd.read_csv(snippets_path)
            density_df = calculate_vuln_density(snippets_df, processed_df)
            
            density_output = base_dir / "data" / "results" / "vulnerability_density.csv"
            density_df.to_csv(density_output, index=False)
            logger.info(f"Wrote vulnerability density metrics to {density_output}")
        else:
            logger.warning(f"Snippets file not found: {snippets_path}. Skipping density calculation.")

        logger.info("Severity mapping completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error during severity mapping: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
