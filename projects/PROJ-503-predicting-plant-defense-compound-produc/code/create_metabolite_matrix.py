"""
Create metabolite CSV with log-transformed concentrations aligned by experimental sample identifier.

This module implements Task T025: Create metabolite CSV with log-transformed concentrations
aligned by experimental sample identifier (US-1 acceptance scenario 2).

Prerequisites:
- T027 must pass (pairing validation) before this script runs.
- Raw metabolite data must be available in data/raw/ from T022.

Output:
- data/processed/metabolite_matrix.csv: Log-transformed metabolite concentrations
- data/paired/metabolite_matrix.csv: Aligned metabolite matrix for paired samples
"""
import csv
import json
import logging
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from exceptions import E_PAIRING
from logging_utils import log_data_pairing_mismatch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'create_metabolite_matrix.log')
    ]
)
logger = logging.getLogger(__name__)

def load_pairing_report(pairing_report_path: Path) -> Dict[str, Any]:
    """Load the pairing report to get validated sample pairs."""
    if not pairing_report_path.exists():
        raise FileNotFoundError(f"Pairing report not found: {pairing_report_path}")
    
    with open(pairing_report_path, 'r') as f:
        return json.load(f)

def load_raw_metabolite_data(raw_data_dir: Path) -> Dict[str, Dict[str, float]]:
    """
    Load raw metabolite data from the data/raw directory.
    
    Expected format: CSV files with columns:
    - sample_id: Biological sample identifier
    - metabolite_id: Metabolite identifier
    - concentration: Raw concentration value
    - unit: Unit of measurement
    
    Returns:
        Dict mapping sample_id -> {metabolite_id: concentration}
    """
    metabolite_data: Dict[str, Dict[str, float]] = {}
    
    if not raw_data_dir.exists():
        raise FileNotFoundError(f"Raw metabolite data directory not found: {raw_data_dir}")
    
    csv_files = list(raw_data_dir.glob("*metabolite*.csv")) + list(raw_data_dir.glob("*MW*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(f"No metabolite CSV files found in {raw_data_dir}")
    
    logger.info(f"Found {len(csv_files)} metabolite data files")
    
    for csv_file in csv_files:
        logger.info(f"Processing metabolite file: {csv_file.name}")
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    sample_id = row.get('sample_id') or row.get('biosample_id') or row.get('Sample_ID')
                    metabolite_id = row.get('metabolite_id') or row.get('compound_id') or row.get('Metabolite_ID')
                    concentration_str = row.get('concentration') or row.get('concentration_value') or row.get('Concentration')
                    unit = row.get('unit') or row.get('Unit')
                    
                    if not sample_id or not metabolite_id or not concentration_str:
                        continue
                    
                    # Parse concentration, handling various formats
                    concentration_str = concentration_str.replace(',', '').replace(' ', '')
                    if 'nd' in concentration_str.lower() or 'not detected' in concentration_str.lower():
                        concentration = 0.0
                    else:
                        concentration = float(concentration_str)
                    
                    if sample_id not in metabolite_data:
                        metabolite_data[sample_id] = {}
                    
                    metabolite_data[sample_id][metabolite_id] = {
                        'value': concentration,
                        'unit': unit
                    }
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping malformed row in {csv_file.name}: {e}")
                    continue
    
    logger.info(f"Loaded metabolite data for {len(metabolite_data)} samples")
    return metabolite_data

def calculate_log_transformation(value: float, epsilon: float = 1e-10) -> float:
    """
    Calculate log transformation of a concentration value.
    
    Uses log1p(x) = log(1 + x) for small values to avoid -inf.
    For zero or negative values, uses log(epsilon + value).
    
    Args:
        value: Raw concentration value
        epsilon: Small constant to avoid log(0)
    
    Returns:
        Log-transformed value
    """
    if value <= 0:
        # Use log1p for small positive values, log(epsilon) for zero/negative
        return math.log1p(epsilon)
    return math.log1p(value)

def filter_metabolite_data_by_pairing(
    metabolite_data: Dict[str, Dict[str, float]],
    pairing_report: Dict[str, Any]
) -> Dict[str, Dict[str, float]]:
    """
    Filter metabolite data to only include samples that are in the pairing report.
    
    Args:
        metabolite_data: Raw metabolite data
        pairing_report: Pairing report with validated sample pairs
    
    Returns:
        Filtered metabolite data with only paired samples
    """
    # Get all valid sample IDs from pairing report
    valid_sample_ids: Set[str] = set()
    
    if 'paired_samples' in pairing_report:
        for pair in pairing_report['paired_samples']:
            valid_sample_ids.add(pair.get('sample_id'))
            valid_sample_ids.add(pair.get('expression_sample_id'))
            valid_sample_ids.add(pair.get('metabolite_sample_id'))
    
    # Filter metabolite data
    filtered_data = {
        sample_id: data
        for sample_id, data in metabolite_data.items()
        if sample_id in valid_sample_ids
    }
    
    logger.info(f"Filtered metabolite data: {len(filtered_data)} samples after pairing filter")
    return filtered_data

def write_metabolite_matrix(
    metabolite_data: Dict[str, Dict[str, float]],
    output_path: Path,
    log_transform: bool = True
) -> None:
    """
    Write metabolite matrix to CSV file.
    
    Format: Rows = samples, Columns = metabolites
    Values: Log-transformed concentrations (if log_transform=True)
    
    Args:
        metabolite_data: Filtered metabolite data
        output_path: Output file path
        log_transform: Whether to apply log transformation
    """
    # Collect all unique metabolite IDs
    all_metabolites: Set[str] = set()
    for sample_data in metabolite_data.values():
        all_metabolites.update(sample_data.keys())
    
    all_metabolites = sorted(list(all_metabolites))
    
    if not all_metabolites:
        raise ValueError("No metabolites found in filtered data")
    
    logger.info(f"Writing metabolite matrix with {len(metabolite_data)} samples and {len(all_metabolites)} metabolites")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        header = ['sample_id'] + all_metabolites
        writer.writerow(header)
        
        # Write data rows
        for sample_id in sorted(metabolite_data.keys()):
            row = [sample_id]
            sample_data = metabolite_data[sample_id]
            
            for metabolite_id in all_metabolites:
                if metabolite_id in sample_data:
                    value = sample_data[metabolite_id]['value']
                    if log_transform:
                        value = calculate_log_transformation(value)
                    row.append(f"{value:.6f}")
                else:
                    row.append("")  # Missing value
            
            writer.writerow(row)
    
    logger.info(f"Metabolite matrix written to {output_path}")

def create_metabolite_matrix(
    raw_data_dir: Path,
    pairing_report_path: Path,
    output_dir: Path,
    log_transform: bool = True
) -> Path:
    """
    Main function to create the metabolite matrix.
    
    Steps:
    1. Load pairing report (requires T027 to have passed)
    2. Load raw metabolite data
    3. Filter by paired samples
    4. Apply log transformation
    5. Write to CSV
    
    Args:
        raw_data_dir: Directory containing raw metabolite data
        pairing_report_path: Path to pairing report JSON
        output_dir: Directory for output files
        log_transform: Whether to apply log transformation
    
    Returns:
        Path to the created metabolite matrix file
    """
    # Validate prerequisites
    if not pairing_report_path.exists():
        raise FileNotFoundError(f"Pairing report not found: {pairing_report_path}. "
                              "Ensure T027 (pairing validation) has completed successfully.")
    
    # Load pairing report
    logger.info("Loading pairing report")
    pairing_report = load_pairing_report(pairing_report_path)
    
    # Check pairing rate
    pairing_rate = pairing_report.get('pairing_rate', 0)
    if pairing_rate < 0.95:
        logger.error(f"Pairing rate {pairing_rate:.2%} is below 95% threshold. "
                    "This should have been caught by T027 validation.")
        raise E_PAIRING(f"Pairing rate {pairing_rate:.2%} below 95% threshold")
    
    # Load raw metabolite data
    logger.info("Loading raw metabolite data")
    metabolite_data = load_raw_metabolite_data(raw_data_dir)
    
    if not metabolite_data:
        raise ValueError("No metabolite data found in raw data directory")
    
    # Filter by paired samples
    logger.info("Filtering metabolite data by paired samples")
    filtered_data = filter_metabolite_data_by_pairing(metabolite_data, pairing_report)
    
    if not filtered_data:
        raise ValueError("No metabolite samples remain after pairing filter")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write processed metabolite matrix
    processed_output = output_dir / 'metabolite_matrix.csv'
    logger.info(f"Writing processed metabolite matrix to {processed_output}")
    write_metabolite_matrix(filtered_data, processed_output, log_transform=log_transform)
    
    # Write paired metabolite matrix (same as processed for now, but separate file for clarity)
    paired_output = output_dir.parent / 'paired' / 'metabolite_matrix.csv'
    paired_output.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing paired metabolite matrix to {paired_output}")
    write_metabolite_matrix(filtered_data, paired_output, log_transform=log_transform)
    
    logger.info("Metabolite matrix creation completed successfully")
    return processed_output

def main():
    """Main entry point for the script."""
    project_root = Path(__file__).parent.parent
    
    # Define paths
    raw_data_dir = project_root / 'data' / 'raw'
    pairing_report_path = project_root / 'logs' / 'pairing_report.json'
    output_dir = project_root / 'data' / 'processed'
    
    logger.info(f"Starting metabolite matrix creation")
    logger.info(f"Raw data directory: {raw_data_dir}")
    logger.info(f"Pairing report: {pairing_report_path}")
    logger.info(f"Output directory: {output_dir}")
    
    try:
        output_path = create_metabolite_matrix(
            raw_data_dir=raw_data_dir,
            pairing_report_path=pairing_report_path,
            output_dir=output_dir,
            log_transform=True
        )
        logger.info(f"Successfully created metabolite matrix: {output_path}")
        print(f"Metabolite matrix created: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)
    except E_PAIRING as e:
        logger.error(f"Pairing error: {e}")
        print(f"ERROR: Pairing validation failed - {e}")
        sys.exit(2)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        print(f"ERROR: {e}")
        sys.exit(3)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"ERROR: Unexpected error - {e}")
        sys.exit(4)

if __name__ == '__main__':
    main()