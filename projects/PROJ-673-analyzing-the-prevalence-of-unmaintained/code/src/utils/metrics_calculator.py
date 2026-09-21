import json
from pathlib import Path
from typing import List, Dict, Any

def calculate_missing_release_proportion(dependencies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate the proportion of dependencies with missing release metadata.
    
    This function mirrors the logic in src.cli.calculate_metrics to ensure
    consistency across the codebase.
    
    Args:
        dependencies: List of dependency dictionaries containing metadata.
    
    Returns:
        Dictionary with:
        - missing_release_metadata_ratio: float
        - total_dependencies: int
        - missing_count: int
    """
    if not dependencies:
        return {
            'missing_release_metadata_ratio': 0.0,
            'total_dependencies': 0,
            'missing_count': 0
        }
    
    missing_count = 0
    total_count = len(dependencies)
    
    for dep in dependencies:
        if not isinstance(dep, dict):
            continue
        
        release_date = dep.get('last_release_date')
        
        # Check for missing or null release dates
        if release_date is None or release_date == '' or str(release_date).lower() == 'null':
            missing_count += 1
    
    ratio = missing_count / total_count if total_count > 0 else 0.0
    
    return {
        'missing_release_metadata_ratio': ratio,
        'total_dependencies': total_count,
        'missing_count': missing_count
    }

def write_metrics_to_file(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Write metrics to a JSON file.
    
    Args:
        metrics: Dictionary of metrics to write.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    output_dir = path.parent
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)