"""
Configuration module for project settings, paths, and seeds.
"""
import os
from pathlib import Path
from typing import List, Dict, Any

def get_config_summary() -> Dict[str, Any]:
    """
    Return a dictionary of project configuration settings.
    
    Returns:
        Dictionary containing paths, seeds, and test URLs.
    """
    project_root = Path(__file__).parent.parent
    
    return {
        'project_root': str(project_root),
        'data_raw': str(project_root / 'data' / 'raw'),
        'data_processed': str(project_root / 'data' / 'processed'),
        'results': str(project_root / 'results'),
        'random_seed': 42,
        'test_data_url': 'https://raw.githubusercontent.com/materialsproject/pmg/master/pmg/test_data.json',
        'valid_source_whitelist': [
            'https://materialsproject.org',
            'https://oqmd.org',
            'https://raw.githubusercontent.com'
        ]
    }
