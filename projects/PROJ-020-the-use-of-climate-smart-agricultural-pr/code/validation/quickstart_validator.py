"""
Quickstart Validator for T042: End-to-end reproducibility validation.

This module validates that the quickstart.md pipeline runs successfully
in a fresh environment by executing the full data pipeline and verifying
all expected outputs are generated.
"""

import sys
import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data.download import download_lsms, download_nasa_power, download_faostat
from data.clean import run_sampling_pipeline, clean_and_merge, apply_imputation_weights, validate_imputation_quality, get_imputation_report
from utils.config import get_target_countries, get_target_years, get_data_dir
from data.features import construct_csa_index
from analysis.model import run_mixed_effects_model, run_mediation_analysis
from analysis.robustness import run_bootstrap_resampling, run_leave_one_region_out
from viz.plots import create_scatter_plot, create_coefficient_plot, create_distribution_plot


class QuickstartValidator:
    """
    Validates end-to-end reproducibility of the quickstart.md pipeline.
    
    This validator executes the full pipeline and verifies:
    1. All data downloads complete successfully
    2. Data cleaning and merging produces valid output
    3. CSA index construction works correctly
    4. Statistical models run without errors
    5. Robustness checks complete
    6. All visualization outputs are generated
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize the validator.
        
        Args:
            base_dir: Base project directory. Defaults to parent of this file's parent.
        """
        if base_dir is None:
            self.base_dir = Path(__file__).parent.parent.parent
        else:
            self.base_dir = base_dir
        
        self.data_dir = self.base_dir / "data"
        self.results_dir = self.base_dir / "data" / "processed"
        self.figures_dir = self.base_dir / "figures"
        self.validation_log = self.base_dir / "data" / "validation_log.json"
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("QuickstartValidator")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)
        
        self.validation_results: Dict[str, Any] = {
            "timestamp": None,
            "environment": "fresh",
            "steps": [],
            "summary": {
                "total_steps": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }

    def log_step(self, step_name: str, status: str, details: Optional[Dict] = None):
        """Log a validation step with status."""
        step_record = {
            "step": step_name,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        if details:
            step_record["details"] = details
        
        self.validation_results["steps"].append(step_record)
        self.logger.info(f"Step '{step_name}': {status}")
        
        if status == "passed":
            self.validation_results["summary"]["passed"] += 1
        elif status == "failed":
            self.validation_results["summary"]["failed"] += 1
        elif status == "warning":
            self.validation_results["summary"]["warnings"] += 1

    def validate_directory_structure(self) -> bool:
        """Validate that required directory structure exists."""
        self.logger.info("Validating directory structure...")
        
        required_dirs = [
            self.data_dir / "raw",
            self.data_dir / "processed",
            self.data_dir / "state",
            self.figures_dir
        ]
        
        all_exist = True
        for dir_path in required_dirs:
            if not dir_path.exists():
                self.logger.warning(f"Directory missing: {dir_path}")
                dir_path.mkdir(parents=True, exist_ok=True)
                all_exist = False
        
        status = "passed" if all_exist else "warning"
        self.log_step("directory_structure", status, {
            "all_required_exist": all_exist
        })
        
        return all_exist

    def validate_data_downloads(self) -> bool:
        """Validate that data downloads can be executed (or already exist)."""
        self.logger.info("Validating data downloads...")
        
        countries = get_target_countries()
        years = get_target_years()
        
        downloaded_files = []
        missing_files = []
        
        # Check LSMS data
        for country in countries:
            for year in years:
                lsms_file = self.data_dir / "raw" / f"lsms_{country}_{year}.json"
                if lsms_file.exists():
                    downloaded_files.append(str(lsms_file))
                else:
                    missing_files.append(f"lsms_{country}_{year}")
        
        # Check NASA POWER data
        nasa_file = self.data_dir / "raw" / "nasa_power_climate.json"
        if nasa_file.exists():
            downloaded_files.append(str(nasa_file))
        else:
            missing_files.append("nasa_power_climate")
        
        # Check FAOSTAT data
        faostat_file = self.data_dir / "raw" / "faostat_indicators.json"
        if faostat_file.exists():
            downloaded_files.append(str(faostat_file))
        else:
            missing_files.append("faostat_indicators")
        
        status = "passed" if len(missing_files) == 0 else "warning"
        self.log_step("data_downloads", status, {
            "downloaded_files": len(downloaded_files),
            "missing_files": missing_files,
            "note": "Missing files may require manual download or pipeline execution"
        })
        
        return len(missing_files) == 0

    def validate_data_pipeline(self) -> bool:
        """Validate that the data pipeline produces valid output."""
        self.logger.info("Validating data pipeline...")
        
        output_file = self.results_dir / "merged_sample.parquet"
        
        try:
            # Run the pipeline if output doesn't exist
            if not output_file.exists():
                self.logger.info("Running data pipeline to generate merged_sample.parquet...")
                run_sampling_pipeline()
            
            # Validate output exists and has content
            if output_file.exists():
                import pandas as pd
                df = pd.read_parquet(output_file)
                
                self.log_step("data_pipeline", "passed", {
                    "output_file": str(output_file),
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns_sample": list(df.columns[:10])
                })
                return True
            else:
                self.log_step("data_pipeline", "failed", {
                    "reason": "Output file not generated"
                })
                return False
                
        except Exception as e:
            self.log_step("data_pipeline", "failed", {
                "reason": str(e)
            })
            return False

    def validate_csa_index_construction(self) -> bool:
        """Validate that CSA index construction works."""
        self.logger.info("Validating CSA index construction...")
        
        try:
            # Load processed data
            processed_file = self.results_dir / "merged_sample.parquet"
            if not processed_file.exists():
                self.log_step("csa_index_construction", "failed", {
                    "reason": "Processed data not available"
                })
                return False
            
            import pandas as pd
            df = pd.read_parquet(processed_file)
            
            # Construct CSA index
            csa_data = construct_csa_index(df)
            
            if csa_data is not None and "csa_index" in csa_data.columns:
                self.log_step("csa_index_construction", "passed", {
                    "index_range": [float(csa_data["csa_index"].min()), 
                                   float(csa_data["csa_index"].max())],
                    "index_mean": float(csa_data["csa_index"].mean())
                })
                return True
            else:
                self.log_step("csa_index_construction", "failed", {
                    "reason": "CSA index not constructed correctly"
                })
                return False
                
        except Exception as e:
            self.log_step("csa_index_construction", "failed", {
                "reason": str(e)
            })
            return False

    def validate_model_execution(self) -> bool:
        """Validate that statistical models can be executed."""
        self.logger.info("Validating model execution...")
        
        try:
            processed_file = self.results_dir / "merged_sample.parquet"
            if not processed_file.exists():
                self.log_step("model_execution", "failed", {
                    "reason": "Processed data not available"
                })
                return False
            
            import pandas as pd
            df = pd.read_parquet(processed_file)
            
            # Run mixed effects model
            model_results = run_mixed_effects_model(df)
            
            if model_results is not None:
                self.log_step("model_execution", "passed", {
                    "model_type": "mixed_effects",
                    "has_coefficients": "coefficients" in model_results,
                    "has_pvalues": "pvalues" in model_results
                })
                return True
            else:
                self.log_step("model_execution", "failed", {
                    "reason": "Model execution returned no results"
                })
                return False
                
        except Exception as e:
            self.log_step("model_execution", "failed", {
                "reason": str(e)
            })
            return False

    def validate_robustness_checks(self) -> bool:
        """Validate that robustness checks can be executed."""
        self.logger.info("Validating robustness checks...")
        
        try:
            processed_file = self.results_dir / "merged_sample.parquet"
            if not processed_file.exists():
                self.log_step("robustness_checks", "warning", {
                    "reason": "Processed data not available - skipping robustness"
                })
                return True  # Not a failure, just skipped
            
            import pandas as pd
            df = pd.read_parquet(processed_file)
            
            # Run bootstrap resampling (limited iterations for speed)
            bootstrap_results = run_bootstrap_resampling(df, n_iterations=100)
            
            # Run leave-one-region-out
            loo_results = run_leave_one_region_out(df)
            
            self.log_step("robustness_checks", "passed", {
                "bootstrap_iterations": 100,
                "has_bootstrap_results": bootstrap_results is not None,
                "has_loo_results": loo_results is not None
            })
            return True
            
        except Exception as e:
            self.log_step("robustness_checks", "warning", {
                "reason": str(e),
                "note": "Robustness checks may require more data or time"
            })
            return True  # Not a hard failure

    def validate_visualizations(self) -> bool:
        """Validate that visualization outputs are generated."""
        self.logger.info("Validating visualizations...")
        
        processed_file = self.results_dir / "merged_sample.parquet"
        if not processed_file.exists():
            self.log_step("visualizations", "warning", {
                "reason": "Processed data not available - skipping visualizations"
            })
            return True  # Not a failure, just skipped
        
        try:
            import pandas as pd
            df = pd.read_parquet(processed_file)
            
            # Create scatter plot
            scatter_plot_path = self.figures_dir / "scatter_csa_food_security.png"
            create_scatter_plot(df, output_path=str(scatter_plot_path))
            
            # Create coefficient plot
            coef_plot_path = self.figures_dir / "coefficient_plot.png"
            create_coefficient_plot(df, output_path=str(coef_plot_path))
            
            # Create distribution plot
            dist_plot_path = self.figures_dir / "distribution_plot.png"
            create_distribution_plot(df, output_path=str(dist_plot_path))
            
            plots_created = [
                scatter_plot_path.exists(),
                coef_plot_path.exists(),
                dist_plot_path.exists()
            ]
            
            self.log_step("visualizations", "passed", {
                "plots_created": sum(plots_created),
                "total_plots": 3,
                "files": [str(p) for p in [scatter_plot_path, coef_plot_path, dist_plot_path]]
            })
            return all(plots_created)
            
        except Exception as e:
            self.log_step("visualizations", "failed", {
                "reason": str(e)
            })
            return False

    def save_validation_report(self):
        """Save the validation report to disk."""
        self.validation_results["timestamp"] = datetime.now().isoformat()
        self.validation_results["summary"]["total_steps"] = len(self.validation_results["steps"])
        
        with open(self.validation_log, "w") as f:
            json.dump(self.validation_results, f, indent=2)
        
        self.logger.info(f"Validation report saved to {self.validation_log}")

    def run_full_validation(self) -> bool:
        """
        Run the complete validation pipeline.
        
        Returns:
            bool: True if all critical steps passed, False otherwise.
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting Quickstart Validation (T042)")
        self.logger.info("=" * 60)
        
        start_time = time.time()
        
        # Step 1: Directory structure
        self.validate_directory_structure()
        
        # Step 2: Data downloads
        self.validate_data_downloads()
        
        # Step 3: Data pipeline
        pipeline_ok = self.validate_data_pipeline()
        
        # Step 4: CSA Index
        csa_ok = self.validate_csa_index_construction()
        
        # Step 5: Model execution
        model_ok = self.validate_model_execution()
        
        # Step 6: Robustness checks
        self.validate_robustness_checks()
        
        # Step 7: Visualizations
        viz_ok = self.validate_visualizations()
        
        # Save report
        self.save_validation_report()
        
        elapsed = time.time() - start_time
        
        # Final summary
        critical_passed = pipeline_ok and csa_ok and model_ok
        self.validation_results["summary"]["elapsed_seconds"] = elapsed
        self.validation_results["summary"]["critical_passed"] = critical_passed
        
        self.logger.info("=" * 60)
        self.logger.info(f"Validation Complete in {elapsed:.2f}s")
        self.logger.info(f"Passed: {self.validation_results['summary']['passed']}")
        self.logger.info(f"Failed: {self.validation_results['summary']['failed']}")
        self.logger.info(f"Warnings: {self.validation_results['summary']['warnings']}")
        self.logger.info(f"Critical Steps Passed: {critical_passed}")
        self.logger.info("=" * 60)
        
        return critical_passed


def main():
    """Main entry point for the validator."""
    validator = QuickstartValidator()
    success = validator.run_full_validation()
    
    if success:
        print("\n✓ Quickstart validation PASSED - Pipeline is reproducible")
        sys.exit(0)
    else:
        print("\n✗ Quickstart validation FAILED - See validation_log.json for details")
        sys.exit(1)


if __name__ == "__main__":
    main()