import os
from pathlib import Path
from typing import Dict, Any

def load_paths() -> Dict[str, str]:
    """
    Load configuration paths for the project.
    
    Returns:
        Dictionary containing absolute paths to key project directories and files.
    """
    base_dir = Path(__file__).resolve().parent.parent
    code_dir = base_dir / "code"
    data_dir = base_dir / "data"
    
    paths = {
        "base_dir": str(base_dir),
        "code_dir": str(code_dir),
        "data_dir": str(data_dir),
        "raw_data_dir": str(data_dir / "raw"),
        "processed_dir": str(data_dir / "processed"),
        "evaluation_dir": str(data_dir / "evaluation"),
        "logs_dir": str(data_dir / "logs"),
        
        # Specific file paths
        "models_path": str(data_dir / "evaluation" / "trained_models.pkl"),
        "processed_descriptors_path": str(data_dir / "processed" / "computed_descriptors.csv"),
        "dataset_schema_path": str(data_dir / "contracts" / "dataset.schema.yaml"),
        "model_output_schema_path": str(data_dir / "contracts" / "model_output.schema.yaml"),
    }
    
    return paths

def load_env() -> Dict[str, str]:
    """
    Load environment variables.
    
    Returns:
        Dictionary of environment variables.
    """
    return {k: v for k, v in os.environ.items()}
