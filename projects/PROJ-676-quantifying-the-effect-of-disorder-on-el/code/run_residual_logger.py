"""
Script to initialize the NumericalLogger and write the schema definition.
This satisfies T017a by creating the output file with a schema definition entry.
"""
import os
from pathlib import Path
from code.logger import NumericalLogger

def main():
    """
    Initialize the logger and write a schema definition entry to data/metadata/residuals.json.
    """
    output_path = "data/metadata/residuals.json"
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize logger
    logger = NumericalLogger(output_path)
    
    # Log a schema definition entry
    logger.log_residual(
        norm=0.0,
        flag=True,
        task="init",
        description="Schema definition for residuals.json",
        schema={
            "task": "string",
            "residual_norm": "float",
            "converged": "bool",
            "L": "int",
            "W": "float",
            "realization_index": "int",
            "seed": "int"
        }
    )
    
    print(f"Initialized logger at {output_path}")
    print("Schema definition entry written.")

if __name__ == "__main__":
    main()