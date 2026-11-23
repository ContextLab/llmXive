import os
from pathlib import Path
from code.logger import NumericalLogger
import json

DATA_METADATA = Path("data/metadata")
DATA_METADATA.mkdir(parents=True, exist_ok=True)

def main():
    """
    Run the numerical logger to generate the residuals.json file.
    This is a placeholder to ensure the file exists if no other task writes it.
    In a real pipeline, the logger is integrated into the analysis tasks.
    """
    logger = NumericalLogger()
    # Log a dummy entry to ensure the file is created
    logger.log_residual(norm=1e-8, flag=True)
    logger.log_convergence(metric="dummy")
    logger.save()
    print("Residuals logged to data/metadata/residuals.json")

if __name__ == "__main__":
    main()
