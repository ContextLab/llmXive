"""
Data Acquisition Module for TCGA and GEO datasets.

This module handles the dynamic discovery and download of TCGA RNA-seq data
and clinical metadata for tumor types with sufficient sample sizes and response annotations.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

# Try to import TCGAbiolinks wrapper (via rpy2 or python wrapper)
# We use the 'TCGAbiolinks' R package via rpy2 as per project dependencies
try:
    import rpy2.robjects as ro
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.conversion import localconverter
    pandas2ri.activate()
    R_AVAILABLE = True
except ImportError:
    R_AVAILABLE = False
    logging.warning("rpy2 not available. TCGA download will be skipped.")

from .config import get_project_root, ensure_directories
from .utils import calculate_checksum, setup_logging

# Configure logging
logger = setup_logging(__name__)

# Constants
MIN_SAMPLES_PER_TYPE = 50  # Minimum samples required to consider a tumor type valid
MIN_RESPONSE_ANNOTATED = 10  # Minimum samples with response labels
TCGA_RAW_DIR = get_project_root() / "data" / "raw" / "tcga"
TCGA_PROCESSED_DIR = get_project_root() / "data" / "processed"
FEASIBILITY_GATE_FILE = get_project_root() / "data" / "feasibility_gate.json"

def ensure_r_packages_installed():
    """Ensure required R packages are installed."""
    if not R_AVAILABLE:
        return False
    
    required_packages = ['TCGAbiolinks', 'SummarizedExperiment', 'Biobase']
    r = ro.r
    
    for pkg in required_packages:
        try:
            # Check if package is installed
            r('library({})'.format(pkg))
        except Exception:
            logger.info(f"Installing R package {pkg}...")
            try:
                r('if (!requireNamespace("BiocManager", quietly = TRUE)) install.packages("BiocManager")')
                r(f'BiocManager::install("{pkg}", ask=FALSE, update=FALSE)')
                r('library({})'.format(pkg))
            except Exception as e:
                logger.error(f"Failed to install R package {pkg}: {e}")
                return False
    
    return True

def discover_available_tcga_tumor_types():
    """
    Dynamically discover available TCGA tumor types with sufficient sample size.
    
    Returns:
        List[str]: List of tumor type project IDs (e.g., 'TCGA-BRCA')
    """
    if not R_AVAILABLE or not ensure_r_packages_installed():
        logger.error("R environment not available. Cannot discover TCGA types.")
        return []
    
    r = ro.r
    logger.info("Discovering available TCGA tumor types...")
    
    # Use TCGAbiolinks to get available projects
    try:
        # Get all available projects from GDC
        r('''
        library(TCGAbiolinks)
        projects <- GDCquery(project = "all", data.category = "Transcriptome Profiling",
                             data.type = "Gene Expression Quantification", 
                             workflow.type = "HTSeq - Counts")
        ''')
        
        # Extract project IDs
        projects_df = r['projects']
        with localconverter(ro.default_converter + pandas2ri.converter):
            from rpy2.robjects import pandas2ri
            projects_py = pandas2ri.rpy2py(projects_df)
        
        project_ids = projects_py['project'].unique().tolist()
        logger.info(f"Found {len(project_ids)} total TCGA projects")
        
        valid_types = []
        
        # Filter for tumor types with sufficient sample size
        for project_id in project_ids:
            if not project_id.startswith('TCGA-'):
                continue
            
            try:
                # Query sample count for this project
                r(f'''
                query_count <- GDCquery(project = "{project_id}", 
                                        data.category = "Transcriptome Profiling",
                                        data.type = "Gene Expression Quantification",
                                        workflow.type = "HTSeq - Counts")
                sample_count <- nrow(query_count$results[[1]])
                ''')
                
                sample_count = int(r['sample_count'][0])
                
                if sample_count >= MIN_SAMPLES_PER_TYPE:
                    valid_types.append(project_id)
                    logger.info(f"Valid tumor type: {project_id} with {sample_count} samples")
                    
                    # Limit to first 3 valid types found
                    if len(valid_types) >= 3:
                        break
                        
            except Exception as e:
                logger.warning(f"Error checking {project_id}: {e}")
                continue
        
        logger.info(f"Found {len(valid_types)} valid tumor types with >= {MIN_SAMPLES_PER_TYPE} samples")
        return valid_types[:3]  # Return first 3 valid types
        
    except Exception as e:
        logger.error(f"Error discovering TCGA tumor types: {e}")
        return []

def check_response_annotations(project_id: str) -> bool:
    """
    Check if a TCGA project has clinical data with response annotations.
    
    Args:
        project_id: TCGA project ID (e.g., 'TCGA-BRCA')
        
    Returns:
        bool: True if response annotations are available
    """
    if not R_AVAILABLE:
        return False
    
    r = ro.r
    
    try:
        # Query clinical data
        r(f'''
        clinical_query <- GDCquery(project = "{project_id}",
                                   access = "open",
                                   data.category = "Clinical",
                                   data.type = "Clinical Supplement",
                                   data.format = "BCR XML")
        ''')
        
        # Check if clinical data exists
        has_clinical = r['length(clinical_query$results[[1]])'] > 0
        
        if not has_clinical:
            logger.warning(f"No clinical data found for {project_id}")
            return False
        
        # Try to load and check for response annotations
        r('''
        clinical_data <- GDCdownload(clinical_query)
        clinical_df <- GDCprepare(clinical_query)
        ''')
        
        # Check for common response annotation columns
        response_columns = ['response', 'recist', 'cr_pr', 'best_response', 
                          'overall_survival', 'disease_free_survival']
        
        has_response = False
        for col in response_columns:
            r(f'has_{col} <- "{col}" %in% colnames(clinical_df)')
            if r[f'has_{col}'][0]:
                has_response = True
                logger.info(f"Found response column '{col}' in {project_id}")
                break
        
        return has_response
        
    except Exception as e:
        logger.warning(f"Error checking response annotations for {project_id}: {e}")
        return False

def download_tcga_data(project_ids: List[str]):
    """
    Download TCGA RNA-seq data and clinical metadata for specified tumor types.
    
    Args:
        project_ids: List of TCGA project IDs to download
    """
    if not R_AVAILABLE or not ensure_r_packages_installed():
        logger.error("Cannot download TCGA data: R environment not available")
        return False
    
    ensure_directories(TCGA_RAW_DIR)
    
    r = ro.r
    downloaded_types = []
    
    for project_id in project_ids:
        logger.info(f"Downloading data for {project_id}...")
        
        try:
            # Query RNA-seq data
            r(f'''
            query <- GDCquery(project = "{project_id}",
                              data.category = "Transcriptome Profiling",
                              data.type = "Gene Expression Quantification",
                              workflow.type = "HTSeq - Counts")
            ''')
            
            # Download data
            r('GDCdownload(query)')
            
            # Prepare data
            r('''
            data <- GDCprepare(query)
            ''')
            
            # Extract counts and metadata
            r('''
            counts <- assay(data)
            col_data <- colData(data)
            ''')
            
            # Convert to pandas
            with localconverter(ro.default_converter + pandas2ri.converter):
                counts_py = pandas2ri.rpy2py(r['counts'])
                col_data_py = pandas2ri.rpy2py(r['col_data'])
            
            # Save raw counts
            counts_file = TCGA_RAW_DIR / f"{project_id}_counts.csv"
            counts_py.to_csv(counts_file)
            logger.info(f"Saved counts to {counts_file}")
            
            # Save clinical metadata
            clinical_file = TCGA_RAW_DIR / f"{project_id}_clinical.csv"
            col_data_py.to_csv(clinical_file)
            logger.info(f"Saved clinical data to {clinical_file}")
            
            # Generate checksums
            checksum_counts = calculate_checksum(counts_file)
            checksum_clinical = calculate_checksum(clinical_file)
            
            logger.info(f"Checksums: counts={checksum_counts}, clinical={checksum_clinical}")
            
            downloaded_types.append(project_id)
            
        except Exception as e:
            logger.error(f"Failed to download {project_id}: {e}")
            continue
    
    return len(downloaded_types) > 0

def check_tcga_feasibility() -> Dict[str, Any]:
    """
    Check if we have sufficient TCGA tumor types for analysis.
    
    Returns:
        Dict with feasibility status and details
    """
    logger.info("Checking TCGA feasibility...")
    
    # Discover available tumor types
    valid_types = discover_available_tcga_tumor_types()
    
    # Check response annotations for each type
    types_with_response = []
    for project_id in valid_types:
        if check_response_annotations(project_id):
            types_with_response.append(project_id)
    
    result = {
        "total_discovered": len(valid_types),
        "with_response_annotations": len(types_with_response),
        "valid_types": types_with_response,
        "meets_minimum": len(types_with_response) >= 3
    }
    
    logger.info(f"TCGA feasibility: {len(types_with_response)} valid types with response annotations")
    return result

def write_feasibility_gate_result(tcga_status: Dict[str, Any], geo_status: Optional[Dict[str, Any]] = None):
    """
    Write the feasibility gate result to the designated file.
    
    Args:
        tcga_status: TCGA feasibility status
        geo_status: GEO feasibility status (optional)
    """
    gate_result = {
        "status": "pending",
        "tcga": tcga_status,
        "geo": geo_status,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Determine overall status
    if tcga_status["meets_minimum"] and (geo_status is None or geo_status.get("meets_minimum", False)):
        gate_result["status"] = "ready"
    elif not tcga_status["meets_minimum"]:
        gate_result["status"] = "halted"
        gate_result["reason"] = "insufficient_tcga_types"
    elif geo_status and not geo_status.get("meets_minimum", False):
        gate_result["status"] = "halted"
        gate_result["reason"] = "insufficient_geo_datasets"
    
    # Ensure data directory exists
    FEASIBILITY_GATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Write result
    with open(FEASIBILITY_GATE_FILE, 'w') as f:
        json.dump(gate_result, f, indent=2)
    
    logger.info(f"Feasibility gate result written to {FEASIBILITY_GATE_FILE}")
    return gate_result

def run_feasibility_gate():
    """
    Run the complete feasibility gate check for TCGA and GEO data.
    
    Returns:
        bool: True if feasibility gate passed, False otherwise
    """
    logger.info("Running feasibility gate...")
    
    # Check TCGA feasibility
    tcga_status = check_tcga_feasibility()
    
    # For now, we'll assume GEO check is pending (will be implemented in T013)
    geo_status = None
    
    # Write gate result
    result = write_feasibility_gate_result(tcga_status, geo_status)
    
    # Return success if gate passed
    return result["status"] == "ready"

def main():
    """Main entry point for data acquisition."""
    logger.info("Starting TCGA data acquisition...")
    
    # Discover and download TCGA data
    if R_AVAILABLE and ensure_r_packages_installed():
        valid_types = discover_available_tcga_tumor_types()
        
        if len(valid_types) >= 3:
            logger.info(f"Found {len(valid_types)} valid tumor types, proceeding with download...")
            success = download_tcga_data(valid_types[:3])
            
            if success:
                logger.info("TCGA data download completed successfully")
            else:
                logger.error("TCGA data download failed")
        else:
            logger.error(f"Insufficient tumor types found: {len(valid_types)} < 3")
    else:
        logger.error("R environment not available for TCGA data acquisition")
    
    # Run feasibility gate
    run_feasibility_gate()

if __name__ == "__main__":
    main()