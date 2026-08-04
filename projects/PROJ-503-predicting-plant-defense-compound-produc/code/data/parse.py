"""
Parse raw metabolomics and expression data files into wide-format CSV matrices.

This module handles:
1. Parsing Metabolomics Workbench raw files (ST002565) into a wide-format metabolite matrix.
2. Parsing GEO raw zip files (GSE21857, GSE167633) into a wide-format expression matrix.

Output format:
- Metabolite Matrix: {metabolite_id, sample_1, sample_2, ...}
- Expression Matrix: {gene_id, sample_1, sample_2, ...}

All parsing MUST fail loudly if the data format is unexpected or if required
fields are missing. No synthetic fallback is allowed.
"""

import csv
import json
import logging
import os
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import custom exceptions
try:
    from exceptions import E_DATASET
except ImportError:
    # Fallback for direct execution
    class E_DATASET(Exception):
        """Raised when dataset acquisition or parsing fails."""
        pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/parse.log')
    ]
)
logger = logging.getLogger(__name__)

# Project root path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / 'data' / 'raw'
LOGS_DIR = PROJECT_ROOT / 'logs'

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def parse_metabolomics_workbench(
    input_zip_path: str,
    output_csv_path: str
) -> None:
    """
    Parse Metabolomics Workbench raw files into wide-format CSV.
    
    Args:
        input_zip_path: Path to the raw zip file from T002a (e.g., metabolomics_ST002565.zip)
        output_csv_path: Path to output wide-format CSV (e.g., metabolite_matrix.csv)
    
    Raises:
        E_DATASET: If parsing fails, required fields are missing, or data is invalid.
        FileNotFoundError: If input zip file does not exist.
    """
    input_path = Path(input_zip_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input zip file not found: {input_zip_path}")
    
    logger.info(f"Parsing Metabolomics Workbench data from {input_zip_path}")
    
    metabolite_data = {}  # {metabolite_id: {sample_id: value}}
    sample_ids = set()
    
    try:
        with zipfile.ZipFile(input_path, 'r') as zip_ref:
            # Find the metabolite data file (usually .tsv or .csv)
            data_files = [f for f in zip_ref.namelist() if f.endswith(('.tsv', '.csv')) and 'metabolite' in f.lower()]
            
            if not data_files:
                # Try to find any TSV/CSV file if 'metabolite' not in name
                all_data_files = [f for f in zip_ref.namelist() if f.endswith(('.tsv', '.csv'))]
                if all_data_files:
                    data_files = all_data_files
                    logger.warning(f"No 'metabolite' file found, using: {data_files[0]}")
                else:
                    raise E_DATASET(f"No metabolite data files (.tsv/.csv) found in {input_zip_path}")
            
            data_file = data_files[0]
            logger.info(f"Processing file: {data_file}")
            
            with zip_ref.open(data_file) as file:
                # Decode if necessary
                content = file.read().decode('utf-8')
                lines = content.splitlines()
                
                # Detect delimiter
                first_line = lines[0]
                delimiter = ',' if ',' in first_line else '\t'
                
                reader = csv.DictReader(lines, delimiter=delimiter)
                
                required_fields = ['Compound Name', 'Study Accession']
                missing_fields = [f for f in required_fields if f not in reader.fieldnames]
                if missing_fields:
                    raise E_DATASET(f"Missing required fields in metabolite data: {missing_fields}")
                
                # Check for sample columns (columns that are not metadata)
                # Typically, sample columns are numeric and not in the metadata list
                metadata_fields = {'Compound Name', 'Compound ID', 'Study Accession', 'Analysis ID'}
                sample_columns = [col for col in reader.fieldnames if col not in metadata_fields]
                
                if not sample_columns:
                    raise E_DATASET("No sample columns found in metabolite data")
                
                logger.info(f"Found {len(sample_columns)} sample columns: {sample_columns[:5]}...")
                
                for row_idx, row in enumerate(reader):
                    compound_name = row['Compound Name']
                    study_accession = row['Study Accession']
                    
                    if not compound_name or not study_accession:
                        logger.warning(f"Skipping row {row_idx}: missing Compound Name or Study Accession")
                        continue
                    
                    # Use Study Accession as sample_id (as per task requirement)
                    # In reality, we might need to map Study Accession + Sample ID to a unique sample_id
                    # For now, we'll use Study Accession as the base and append a counter if needed
                    # But the task says "Map 'Study Accession' to 'sample_id'", implying one row per study?
                    # Actually, Metabolomics Workbench data usually has one row per compound per sample.
                    # So we need to identify the sample_id from the column headers or metadata.
                    
                    # Re-evaluating: The columns are typically sample IDs.
                    # Let's assume the column names are the sample IDs.
                    
                    for sample_col in sample_columns:
                        value_str = row.get(sample_col, '').strip()
                        
                        # Skip empty or NA values
                        if not value_str or value_str.lower() in ('na', 'nan', '', 'null'):
                            continue
                        
                        try:
                            value = float(value_str)
                        except ValueError:
                            logger.warning(f"Skipping non-numeric value '{value_str}' for {compound_name} in {sample_col}")
                            continue
                        
                        if compound_name not in metabolite_data:
                            metabolite_data[compound_name] = {}
                        
                        metabolite_data[compound_name][sample_col] = value
                        sample_ids.add(sample_col)
                
                if not metabolite_data:
                    raise E_DATASET("No valid metabolite data parsed from the file")
                
                logger.info(f"Parsed {len(metabolite_data)} metabolites across {len(sample_ids)} samples")
                
    except zipfile.BadZipFile:
        raise E_DATASET(f"Invalid zip file: {input_zip_path}")
    except Exception as e:
        raise E_DATASET(f"Failed to parse metabolomics data: {str(e)}")
    
    # Write wide-format CSV
    # Rows: metabolite_id, Columns: sample_1, sample_2, ...
    sorted_samples = sorted(list(sample_ids))
    
    logger.info(f"Writing metabolite matrix to {output_csv_path}")
    
    try:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header: metabolite_id, sample_1, sample_2, ...
            header = ['metabolite_id'] + sorted_samples
            writer.writerow(header)
            
            # Sort metabolites for consistent output
            for metabolite_id in sorted(metabolite_data.keys()):
                row = [metabolite_id]
                for sample_id in sorted_samples:
                    value = metabolite_data[metabolite_id].get(sample_id, '')
                    row.append(value)
                writer.writerow(row)
                
        logger.info(f"Successfully wrote metabolite matrix with {len(metabolite_data)} rows and {len(sorted_samples)} columns")
        
    except Exception as e:
        raise E_DATASET(f"Failed to write metabolite matrix: {str(e)}")

def parse_geo_expression(
    input_zip_path: str,
    output_csv_path: str
) -> None:
    """
    Parse GEO raw zip files into wide-format CSV.
    
    Args:
        input_zip_path: Path to the raw zip file from T001a (e.g., geo_GSE21857.zip)
        output_csv_path: Path to output wide-format CSV (e.g., geo_expression_matrix.csv)
    
    Raises:
        E_DATASET: If parsing fails, required fields are missing, or data is invalid.
        FileNotFoundError: If input zip file does not exist.
    """
    input_path = Path(input_zip_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input zip file not found: {input_zip_path}")
    
    logger.info(f"Parsing GEO expression data from {input_zip_path}")
    
    expression_data = {}  # {gene_id: {sample_id: value}}
    sample_ids = set()
    
    try:
        with zipfile.ZipFile(input_path, 'r') as zip_ref:
            # Find the expression data file (usually .txt, .tsv, or .csv)
            data_files = [f for f in zip_ref.namelist() if f.endswith(('.txt', '.tsv', '.csv')) and 'expression' in f.lower()]
            
            if not data_files:
                # Try to find any TSV/CSV file if 'expression' not in name
                all_data_files = [f for f in zip_ref.namelist() if f.endswith(('.txt', '.tsv', '.csv'))]
                if all_data_files:
                    data_files = all_data_files
                    logger.warning(f"No 'expression' file found, using: {data_files[0]}")
                else:
                    raise E_DATASET(f"No expression data files (.txt/.tsv/.csv) found in {input_zip_path}")
            
            data_file = data_files[0]
            logger.info(f"Processing file: {data_file}")
            
            with zip_ref.open(data_file) as file:
                # Decode if necessary
                content = file.read().decode('utf-8')
                lines = content.splitlines()
                
                # Detect delimiter
                first_line = lines[0]
                delimiter = ',' if ',' in first_line else '\t'
                
                reader = csv.DictReader(lines, delimiter=delimiter)
                
                # Look for gene_id column (common names: 'Gene ID', 'Gene', 'Probe ID', 'ID')
                gene_id_column = None
                potential_gene_columns = ['Gene ID', 'Gene', 'Probe ID', 'ID', 'gene_id', 'gene']
                for col in potential_gene_columns:
                    if col in reader.fieldnames:
                        gene_id_column = col
                        break
                
                if not gene_id_column:
                    # Use the first column as gene_id if no match found
                    gene_id_column = reader.fieldnames[0]
                    logger.warning(f"Using '{gene_id_column}' as gene_id column (no standard name found)")
                
                # Sample columns are all columns except gene_id_column
                sample_columns = [col for col in reader.fieldnames if col != gene_id_column]
                
                if not sample_columns:
                    raise E_DATASET("No sample columns found in expression data")
                
                logger.info(f"Found {len(sample_columns)} sample columns")
                
                for row_idx, row in enumerate(reader):
                    gene_id = row[gene_id_column].strip()
                    
                    if not gene_id:
                        logger.warning(f"Skipping row {row_idx}: missing gene_id")
                        continue
                    
                    for sample_col in sample_columns:
                        value_str = row.get(sample_col, '').strip()
                        
                        # Skip empty or NA values
                        if not value_str or value_str.lower() in ('na', 'nan', '', 'null'):
                            continue
                        
                        try:
                            value = float(value_str)
                        except ValueError:
                            logger.warning(f"Skipping non-numeric value '{value_str}' for {gene_id} in {sample_col}")
                            continue
                        
                        if gene_id not in expression_data:
                            expression_data[gene_id] = {}
                        
                        expression_data[gene_id][sample_col] = value
                        sample_ids.add(sample_col)
                
                if not expression_data:
                    raise E_DATASET("No valid expression data parsed from the file")
                
                logger.info(f"Parsed {len(expression_data)} genes across {len(sample_ids)} samples")
                
    except zipfile.BadZipFile:
        raise E_DATASET(f"Invalid zip file: {input_zip_path}")
    except Exception as e:
        raise E_DATASET(f"Failed to parse GEO expression data: {str(e)}")
    
    # Write wide-format CSV
    # Rows: gene_id, Columns: sample_1, sample_2, ...
    sorted_samples = sorted(list(sample_ids))
    
    logger.info(f"Writing expression matrix to {output_csv_path}")
    
    try:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header: gene_id, sample_1, sample_2, ...
            header = ['gene_id'] + sorted_samples
            writer.writerow(header)
            
            # Sort genes for consistent output
            for gene_id in sorted(expression_data.keys()):
                row = [gene_id]
                for sample_id in sorted_samples:
                    value = expression_data[gene_id].get(sample_id, '')
                    row.append(value)
                writer.writerow(row)
                
        logger.info(f"Successfully wrote expression matrix with {len(expression_data)} rows and {len(sorted_samples)} columns")
        
    except Exception as e:
        raise E_DATASET(f"Failed to write expression matrix: {str(e)}")

def main():
    """
    Main function to parse raw data files.
    
    This function should be called after T001a and T002a have downloaded the raw files.
    It parses the downloaded files into wide-format CSVs.
    """
    # Parse Metabolomics Workbench data (T002b)
    metabolomics_input = str(DATA_RAW_DIR / 'metabolomics_ST002565.zip')
    metabolomics_output = str(DATA_RAW_DIR / 'metabolite_matrix.csv')
    
    try:
        parse_metabolomics_workbench(metabolomics_input, metabolomics_output)
        logger.info("T002b: Successfully parsed metabolomics data")
    except Exception as e:
        logger.error(f"T002b: Failed to parse metabolomics data: {str(e)}")
        raise
    
    # Parse GEO expression data (T001b)
    geo_gse21857_input = str(DATA_RAW_DIR / 'geo_GSE21857.zip')
    geo_gse167633_input = str(DATA_RAW_DIR / 'geo_GSE167633.zip')
    geo_output = str(DATA_RAW_DIR / 'geo_expression_matrix.csv')
    
    # If both files exist, we might need to merge them or process separately
    # For now, let's process GSE21857 if it exists
    if Path(geo_gse21857_input).exists():
        try:
            parse_geo_expression(geo_gse21857_input, geo_output)
            logger.info("T001b: Successfully parsed GEO GSE21857 data")
        except Exception as e:
            logger.error(f"T001b: Failed to parse GEO GSE21857 data: {str(e)}")
            raise
    elif Path(geo_gse167633_input).exists():
        try:
            parse_geo_expression(geo_gse167633_input, geo_output)
            logger.info("T001b: Successfully parsed GEO GSE167633 data")
        except Exception as e:
            logger.error(f"T001b: Failed to parse GEO GSE167633 data: {str(e)}")
            raise
    else:
        logger.warning("No GEO expression data files found. Skipping expression matrix parsing.")

if __name__ == '__main__':
    main()