"""
Quickstart Validation Module for PROJ-020
Validates end-to-end reproducibility of the climate-smart agriculture pipeline.
"""
import sys
import os
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_config, get_target_countries, get_target_years, get_data_dir
from utils.logging import initialize_logging, log_provenance_mapping
from data.download import download_lsms, download_nasa_power, download_faostat
from data.clean import run_sampling_pipeline, clean_and_merge, apply_imputation_weights
from data.features import construct_csa_index
from analysis.model import run_mixed_effects_model, run_mediation_analysis
from analysis.diagnostics import calculate_vif, get_collinearity_report
from analysis.robustness import run_bootstrap_resampling, run_leave_one_region_out
from viz.plots import create_scatter_plot, create_coefficient_plot, create_distribution_plot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuickstartValidator:
    """
    Validates the end-to-end reproducibility of the CSA pipeline as described
    in quickstart.md.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the validator.

        Args:
            data_dir: Optional path to the data directory. If None, uses config.
        """
        self.config = get_config()
        self.data_dir = data_dir or get_data_dir()
        self.results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'countries': get_target_countries(),
            'years': get_target_years(),
            'stages': {},
            'errors': [],
            'warnings': []
        }

    def validate_directory_structure(self) -> bool:
        """
        Validates that the required directory structure exists.

        Returns:
            bool: True if structure is valid, False otherwise.
        """
        logger.info("Validating directory structure...")
        required_dirs = [
            self.data_dir / 'raw',
            self.data_dir / 'processed',
            self.data_dir / 'figures',
            project_root / 'state'
        ]

        all_exist = True
        for dir_path in required_dirs:
            if not dir_path.exists():
                logger.warning(f"Directory missing: {dir_path}")
                dir_path.mkdir(parents=True, exist_ok=True)
                self.results['warnings'].append(f"Created missing directory: {dir_path}")

        self.results['stages']['directory_structure'] = {
            'status': 'passed' if all_exist else 'warning',
            'message': 'Directory structure validated'
        }
        return True

    def validate_data_availability(self) -> bool:
        """
        Validates that required data files exist or can be downloaded.

        Returns:
            bool: True if data is available, False otherwise.
        """
        logger.info("Validating data availability...")
        processed_file = self.data_dir / 'processed' / 'merged_sample.parquet'

        if processed_file.exists():
            logger.info(f"Found processed data: {processed_file}")
            self.results['stages']['data_availability'] = {
                'status': 'passed',
                'message': 'Processed data file exists',
                'file_size_bytes': processed_file.stat().st_size
            }
            return True

        logger.warning("Processed data file not found. Attempting download...")
        try:
            # Attempt to download a minimal sample for validation
            # This is a validation run, so we use a small sample
            logger.info("Starting data download for validation...")
            download_lsms('Kenya', 2021)  # Example: Kenya 2021
            download_faostat('Crops')
            # Note: NASA POWER download requires coordinates, skipped for basic validation
            logger.info("Initial data download completed.")

            self.results['stages']['data_availability'] = {
                'status': 'passed',
                'message': 'Data downloaded successfully'
            }
            return True
        except Exception as e:
            error_msg = f"Data download failed: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            self.results['stages']['data_availability'] = {
                'status': 'failed',
                'message': error_msg
            }
            return False

    def validate_cleaning_pipeline(self) -> bool:
        """
        Validates the data cleaning and merging pipeline.

        Returns:
            bool: True if pipeline runs successfully, False otherwise.
        """
        logger.info("Validating cleaning pipeline...")
        try:
            # Check if raw data exists
            raw_files = list((self.data_dir / 'raw').glob('*.csv'))
            if not raw_files:
                logger.warning("No raw data files found. Skipping cleaning validation.")
                self.results['stages']['cleaning_pipeline'] = {
                    'status': 'skipped',
                    'message': 'No raw data files found'
                }
                return True

            # Run cleaning pipeline
            logger.info("Running cleaning pipeline...")
            cleaned_data = run_sampling_pipeline(self.data_dir)

            if cleaned_data is not None and len(cleaned_data) > 0:
                self.results['stages']['cleaning_pipeline'] = {
                    'status': 'passed',
                    'message': f'Cleaning pipeline completed. {len(cleaned_data)} rows processed.'
                }
                return True
            else:
                raise ValueError("Cleaning pipeline produced no output")

        except Exception as e:
            error_msg = f"Cleaning pipeline failed: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            self.results['stages']['cleaning_pipeline'] = {
                'status': 'failed',
                'message': error_msg
            }
            return False

    def validate_feature_construction(self) -> bool:
        """
        Validates the CSA index construction.

        Returns:
            bool: True if features are constructed successfully, False otherwise.
        """
        logger.info("Validating feature construction...")
        try:
            processed_file = self.data_dir / 'processed' / 'merged_sample.parquet'
            if not processed_file.exists():
                logger.warning("Processed data not found. Skipping feature validation.")
                self.results['stages']['feature_construction'] = {
                    'status': 'skipped',
                    'message': 'Processed data not found'
                }
                return True

            import pandas as pd
            data = pd.read_parquet(processed_file)

            # Construct CSA index
            csa_index = construct_csa_index(data)

            if csa_index is not None and 'csa_index' in csa_index.columns:
                self.results['stages']['feature_construction'] = {
                    'status': 'passed',
                    'message': f'CSA index constructed. Range: [{csa_index["csa_index"].min():.3f}, {csa_index["csa_index"].max():.3f}]'
                }
                return True
            else:
                raise ValueError("CSA index construction failed")

        except Exception as e:
            error_msg = f"Feature construction failed: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            self.results['stages']['feature_construction'] = {
                'status': 'failed',
                'message': error_msg
            }
            return False

    def validate_model_fitting(self) -> bool:
        """
        Validates the statistical model fitting.

        Returns:
            bool: True if model fits successfully, False otherwise.
        """
        logger.info("Validating model fitting...")
        try:
            processed_file = self.data_dir / 'processed' / 'merged_sample.parquet'
            if not processed_file.exists():
                logger.warning("Processed data not found. Skipping model validation.")
                self.results['stages']['model_fitting'] = {
                    'status': 'skipped',
                    'message': 'Processed data not found'
                }
                return True

            import pandas as pd
            data = pd.read_parquet(processed_file)

            # Run mixed effects model
            logger.info("Running mixed effects model...")
            model_results = run_mixed_effects_model(data)

            if model_results is not None:
                self.results['stages']['model_fitting'] = {
                    'status': 'passed',
                    'message': f'Model fitting completed. AIC: {model_results.aic:.2f}'
                }
                return True
            else:
                raise ValueError("Model fitting produced no results")

        except Exception as e:
            error_msg = f"Model fitting failed: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            self.results['stages']['model_fitting'] = {
                'status': 'failed',
                'message': error_msg
            }
            return False

    def validate_diagnostics(self) -> bool:
        """
        Validates the diagnostic checks.

        Returns:
            bool: True if diagnostics run successfully, False otherwise.
        """
        logger.info("Validating diagnostics...")
        try:
            processed_file = self.data_dir / 'processed' / 'merged_sample.parquet'
            if not processed_file.exists():
                logger.warning("Processed data not found. Skipping diagnostics validation.")
                self.results['stages']['diagnostics'] = {
                    'status': 'skipped',
                    'message': 'Processed data not found'
                }
                return True

            import pandas as pd
            data = pd.read_parquet(processed_file)

            # Calculate VIF
            logger.info("Calculating VIF...")
            vif_results = calculate_vif(data)

            if vif_results is not None:
                max_vif = vif_results['VIF Factor'].max()
                self.results['stages']['diagnostics'] = {
                    'status': 'passed',
                    'message': f'Diagnostics completed. Max VIF: {max_vif:.2f}'
                }
                return True
            else:
                raise ValueError("Diagnostics produced no results")

        except Exception as e:
            error_msg = f"Diagnostics failed: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            self.results['stages']['diagnostics'] = {
                'status': 'failed',
                'message': error_msg
            }
            return False

    def validate_visualization(self) -> bool:
        """
        Validates the visualization generation.

        Returns:
            bool: True if visualizations are generated successfully, False otherwise.
        """
        logger.info("Validating visualization...")
        try:
            processed_file = self.data_dir / 'processed' / 'merged_sample.parquet'
            if not processed_file.exists():
                logger.warning("Processed data not found. Skipping visualization validation.")
                self.results['stages']['visualization'] = {
                    'status': 'skipped',
                    'message': 'Processed data not found'
                }
                return True

            import pandas as pd
            data = pd.read_parquet(processed_file)

            # Create scatter plot
            logger.info("Creating scatter plot...")
            scatter_path = create_scatter_plot(data, self.data_dir / 'figures')

            # Create coefficient plot
            logger.info("Creating coefficient plot...")
            coeff_path = create_coefficient_plot(data, self.data_dir / 'figures')

            if scatter_path and coeff_path:
                self.results['stages']['visualization'] = {
                    'status': 'passed',
                    'message': f'Visualizations generated. Scatter: {scatter_path.name}, Coeff: {coeff_path.name}'
                }
                return True
            else:
                raise ValueError("Visualization generation failed")

        except Exception as e:
            error_msg = f"Visualization failed: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            self.results['stages']['visualization'] = {
                'status': 'failed',
                'message': error_msg
            }
            return False

    def run_full_validation(self) -> Dict[str, Any]:
        """
        Runs the full validation pipeline.

        Returns:
            dict: Validation results.
        """
        logger.info("Starting full validation pipeline...")
        start_time = time.time()

        # Run all validation stages
        self.validate_directory_structure()
        self.validate_data_availability()
        self.validate_cleaning_pipeline()
        self.validate_feature_construction()
        self.validate_model_fitting()
        self.validate_diagnostics()
        self.validate_visualization()

        end_time = time.time()
        self.results['total_duration_seconds'] = end_time - start_time

        # Determine overall status
        failed_stages = [
            stage for stage, result in self.results['stages'].items()
            if result.get('status') == 'failed'
        ]

        if failed_stages:
            self.results['overall_status'] = 'failed'
            self.results['failed_stages'] = failed_stages
        else:
            self.results['overall_status'] = 'passed'

        # Save results
        results_file = self.data_dir / 'validation_results.json'
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Validation completed. Results saved to {results_file}")
        return self.results


def main():
    """
    Main entry point for the quickstart validator.
    """
    validator = QuickstartValidator()
    results = validator.run_full_validation()

    # Print summary
    print("\n" + "="*50)
    print("QUICKSTART VALIDATION SUMMARY")
    print("="*50)
    print(f"Status: {results['overall_status'].upper()}")
    print(f"Duration: {results['total_duration_seconds']:.2f} seconds")
    print(f"Errors: {len(results['errors'])}")
    print(f"Warnings: {len(results['warnings'])}")

    if results['failed_stages']:
        print(f"\nFailed Stages: {', '.join(results['failed_stages'])}")

    for stage, result in results['stages'].items():
        status_icon = "✓" if result['status'] == 'passed' else "✗" if result['status'] == 'failed' else "⊘"
        print(f"{status_icon} {stage}: {result['message']}")

    print("="*50)

    # Return exit code based on validation status
    sys.exit(0 if results['overall_status'] == 'passed' else 1)


if __name__ == '__main__':
    main()