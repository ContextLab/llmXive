import os
import sys
import yaml
from pydantic import BaseModel, Field, ValidationError
from typing import Optional

# Import custom exception
from exceptions import E_NO_DATA

# Define the configuration model based on the schema
class Config(BaseModel):
    seed: int = Field(42, description="Random seed for reproducibility")
    permutations: int = Field(1000, description="Number of permutations for MMD test")
    window_size: int = Field(12, description="Size of the sliding window in weeks")
    stride: int = Field(1, description="Stride for the sliding window")
    alpha: float = Field(0.01, description="Significance level for hypothesis testing")

    class Config:
        extra = "forbid"  # Prevent unknown fields

def load_config(config_path: str = "code/config.yaml") -> Config:
    """
    Loads configuration from a YAML file and validates it against the Config model.
    
    Args:
        config_path: Path to the configuration YAML file.
        
    Returns:
        Config: Validated configuration object.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        ValidationError: If the config file content does not match the schema.
        yaml.YAMLError: If the config file is not valid YAML.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        try:
            raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML file: {e}")

    try:
        config = Config(**raw_config)
    except ValidationError as e:
        raise ValidationError(f"Configuration validation failed:\n{e}")

    return config

def validate_data_availability():
    """
    Checks for the existence of required real CDC data files.
    
    Verifies that `data/raw/fluview_ili.csv` and `data/raw/ground_truth_events.csv`
    exist in the project root. If either is missing, raises E_NO_DATA.
    
    Raises:
        E_NO_DATA: If required data files are missing.
    """
    # Determine paths relative to project root
    # Assuming code/main.py is at code/main.py, so project root is parent of code/
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    fluview_path = os.path.join(project_root, "data", "raw", "fluview_ili.csv")
    ground_truth_path = os.path.join(project_root, "data", "raw", "ground_truth_events.csv")
    
    missing_files = []
    
    if not os.path.exists(fluview_path):
        missing_files.append("data/raw/fluview_ili.csv")
        
    if not os.path.exists(ground_truth_path):
        missing_files.append("data/raw/ground_truth_events.csv")
        
    if missing_files:
        file_list = ", ".join(missing_files)
        raise E_NO_DATA(f"Pipeline halted: Real CDC data unavailable. Missing: {file_list}")

def main():
    """
    Main entry point for the pipeline.
    Loads configuration and validates data availability.
    """
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    
    print("Loading configuration...")
    try:
        config = load_config(config_path)
        print("Configuration loaded successfully:")
        print(f"  Seed: {config.seed}")
        print(f"  Permutations: {config.permutations}")
        print(f"  Window Size: {config.window_size}")
        print(f"  Stride: {config.stride}")
        print(f"  Alpha: {config.alpha}")
    except (FileNotFoundError, yaml.YAMLError, ValidationError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("\nValidating data availability...")
    try:
        validate_data_availability()
        print("Data validation passed. Required files found.")
    except E_NO_DATA as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("\nPipeline initialization complete. Ready to run pipeline.")

if __name__ == "__main__":
    main()