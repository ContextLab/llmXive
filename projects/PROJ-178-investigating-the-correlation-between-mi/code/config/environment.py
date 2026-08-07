import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_local_paths():
    """Return local file paths for the project."""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'data'
    processed_dir = data_dir / 'processed'
    logs_dir = base_dir / 'logs'
    figures_dir = base_dir / 'figures'
    
    # Ensure directories exist
    ensure_directories([processed_dir, logs_dir, figures_dir])
    
    return {
        'raw_data': data_dir / 'raw',
        'processed_dataset': processed_dir / 'mito_aging_dataset.csv',
        'spearman_results': processed_dir / 'spearman_results.csv',
        'rank_ols_results': processed_dir / 'rank_ols_results.csv',
        'model_comparison_log': logs_dir / 'model_comparison.log',
        'exclusion_report': logs_dir / 'exclusion_report.txt',
        'haplogroup_success_rate': logs_dir / 'haplogroup_success_rate.txt',
        'sensitivity_results': processed_dir / 'sensitivity_results.csv',
        'subgroup_results': processed_dir / 'subgroup_results.csv',
        'threshold_variation': processed_dir / 'threshold_variation.json',
        'subgroup_variation': processed_dir / 'subgroup_variation.json',
        'sensitivity_analysis': processed_dir / 'sensitivity_analysis.csv',
        'figures': figures_dir,
        'validation_log': logs_dir / 'validation.log'
    }

def get_ftp_urls():
    """Return FTP URLs for 1000 Genomes data."""
    return {
        'vcf': 'ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/20130502_release/',
        'metadata': 'ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/20130502_release/'
    }

def ensure_directories(dir_paths):
    """Ensure that the given directories exist."""
    for dir_path in dir_paths:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {dir_path}")
