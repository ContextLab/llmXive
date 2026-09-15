import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from config import load_config, ensure_directories
from model import fit_regression_model
from clean import load_cleaned_data
from validity import check_construct_validity
from exceptions import MathematicalCouplingError

logger = logging.getLogger(__name__)

def save_regression_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save regression results (coefficients, p-values, diagnostics) to a JSON file.

    Args:
        results: Dictionary containing regression model results.
        output_path: Path where the JSON file will be saved.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # Ensure numpy types are converted to native Python types for JSON serialization
            def json_serial(obj):
                if isinstance(obj, (int, float, str, bool, type(None))):
                    return obj
                if hasattr(obj, 'item'):  # numpy scalars
                    return obj.item()
                if hasattr(obj, 'tolist'):  # numpy arrays
                    return obj.tolist()
                return str(obj)

            json.dump(results, f, indent=2, default=json_serial)
        logger.info(f"Regression results saved to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write regression results to {output_path}: {e}")
        raise

def main() -> None:
    """
    Main function to load data, fit the regression model, and save results.
    """
    config = load_config()
    ensure_directories(config)
    
    # Set random seed
    from config import set_seed
    set_seed(config.get('random_seed', 42))

    # Load cleaned data
    data_path = Path(config['paths']['processed_data'])
    if not data_path.exists():
        logger.error(f"Cleaned data file not found at {data_path}. Run data cleaning first.")
        sys.exit(1)
    
    df = load_cleaned_data(data_path)
    logger.info(f"Loaded {len(df)} rows from {data_path}")

    # Check construct validity before modeling
    try:
        check_construct_validity(df, 'baseline_anxiety', 'anxiety_score')
        logger.info("Construct validity check passed.")
    except MathematicalCouplingError as e:
        logger.error(f"Construct validity check failed: {e}")
        sys.exit(1)

    # Fit regression model
    logger.info("Fitting regression model...")
    model_results = fit_regression_model(df)
    
    if model_results is None:
        logger.error("Regression model fitting failed.")
        sys.exit(1)

    # Add metadata
    model_results['metadata'] = {
        'dataset_rows': len(df),
        'dataset_columns': list(df.columns),
        'model_formula': model_results.get('formula', 'anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender')
    }

    # Save results
    output_path = Path(config['paths']['output_dir']) / 'regression_results.json'
    save_regression_results(model_results, output_path)

    logger.info("Task T021 completed successfully.")

if __name__ == "__main__":
    main()
