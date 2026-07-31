import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def get_local_paths() -> dict:
    """
    Returns a dictionary of local paths used by the analysis scripts.
    These paths are relative to the project root (code/).
    """
    project_root = Path(__file__).resolve().parent.parent
    
    return {
        'raw_data_dir': project_root / 'data' / 'raw',
        'processed_data_dir': project_root / 'data' / 'processed',
        'logs_dir': project_root / 'logs',
        'figures_dir': project_root / 'paper' / 'figures',
        
        # Specific file paths
        'raw_vcf_dir': project_root / 'data' / 'raw' / 'vcf',
        'processed_dataset': project_root / 'data' / 'processed' / 'mito_aging_dataset.csv',
        'model_results': project_root / 'data' / 'processed' / 'model_results.csv',
        'model_comparison_log': project_root / 'logs' / 'model_comparison.log',
        'sensitivity_results': project_root / 'data' / 'processed' / 'sensitivity_analysis.csv',
        'summary_results': project_root / 'data' / 'processed' / 'analysis_results.csv',
    }

def get_ftp_urls() -> dict:
    """
    Returns the FTP URLs for the 1000 Genomes Project data.
    """
    return {
        'mt_vcf_base': 'ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/working/20201028_3202_phased/',
        'metadata_panel': 'ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/20130523_integrated_call_samples_v3.20130502.genotypes.txt',
        # Note: The exact path for metadata might need adjustment based on actual FTP structure
        # This is a placeholder for the metadata panel containing age, sex, population, PCs.
        'metadata_panel_real': 'ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/20130523_integrated_call_samples_v3.20130502.genotypes.txt' 
    }

def ensure_directories():
    """
    Creates necessary directories if they do not exist.
    """
    paths = get_local_paths()
    dirs_to_create = [
        paths['raw_data_dir'],
        paths['processed_data_dir'],
        paths['logs_dir'],
        paths['figures_dir'],
        paths['raw_vcf_dir'],
    ]
    
    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {d}")