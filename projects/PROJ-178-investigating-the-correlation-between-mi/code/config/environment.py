import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def get_local_paths():
    """
    Return a dictionary of all local file paths used by the analysis.
    
    All paths are relative to the project root (code/ directory).
    """
    # Project root is assumed to be the parent of 'code'
    # When run from code/, we need to go up one level
    try:
        # Try to find project root by looking for 'tasks.md'
        current = Path(__file__).resolve()
        while current.parent != current:  # Stop at root
            if (current / 'tasks.md').exists():
                project_root = current
                break
            current = current.parent
        else:
            # Fallback: assume project root is parent of code/
            project_root = Path(__file__).resolve().parent.parent
    except Exception:
        project_root = Path(__file__).resolve().parent.parent
    
    # Define all paths relative to project root
    paths = {
        # Raw data
        'raw_vcf_dir': project_root / 'code' / 'data' / 'raw' / 'vcf',
        'raw_metadata': project_root / 'code' / 'data' / 'raw' / 'metadata_panel.tsv',
        
        # Processed data
        'processed_dataset': project_root / 'code' / 'data' / 'processed' / 'mito_aging_dataset.csv',
        'spearman_results': project_root / 'code' / 'data' / 'processed' / 'spearman_results.csv',
        'rank_ols_results': project_root / 'code' / 'data' / 'processed' / 'rank_ols_results.csv',
        'secondary_ols_results': project_root / 'code' / 'data' / 'processed' / 'secondary_ols_results.csv',
        'sensitivity_results': project_root / 'code' / 'data' / 'processed' / 'sensitivity_results.csv',
        'subgroup_results': project_root / 'code' / 'data' / 'processed' / 'subgroup_results.csv',
        'threshold_variation': project_root / 'code' / 'data' / 'processed' / 'threshold_variation.json',
        'subgroup_variation': project_root / 'code' / 'data' / 'processed' / 'subgroup_variation.json',
        'sensitivity_analysis': project_root / 'code' / 'data' / 'processed' / 'sensitivity_analysis.csv',
        
        # Logs
        'log_dir': project_root / 'code' / 'logs',
        'exclusion_report': project_root / 'code' / 'logs' / 'exclusion_report.txt',
        'haplogroup_success_rate': project_root / 'code' / 'logs' / 'haplogroup_success_rate.txt',
        'model_comparison': project_root / 'code' / 'logs' / 'model_comparison.log',
        'memory_profile': project_root / 'code' / 'logs' / 'memory_profile.log',
        'runtime_validation': project_root / 'code' / 'logs' / 'runtime_validation.log',
        'age_column_validation': project_root / 'code' / 'logs' / 'log_age_column.json',
        'source_verification': project_root / 'code' / 'logs' / 'source_verification.log',
        
        # Figures
        'figures_dir': project_root / 'paper' / 'figures',
        
        # Contracts
        'dataset_schema': project_root / 'code' / 'contracts' / 'dataset.schema.yaml',
        'output_schema': project_root / 'code' / 'contracts' / 'output.schema.yaml',
    }
    
    return paths

def get_ftp_urls():
    """Return FTP URLs for 1000 Genomes data."""
    return {
        'vcf_base': 'ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/',
        'metadata': 'ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/20130602_sample_metadata/20130602_sample_metadata.tsv'
    }

def ensure_directories():
    """Create all required directories if they don't exist."""
    paths = get_local_paths()
    
    for path_name, path_obj in paths.items():
        if isinstance(path_obj, Path):
            if path_obj.suffix == '':  # It's a directory
                path_obj.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured directory: {path_obj}")
    
    logger.info("All required directories created/verified")
    return True

if __name__ == "__main__":
    ensure_directories()
    print("Directories ready")