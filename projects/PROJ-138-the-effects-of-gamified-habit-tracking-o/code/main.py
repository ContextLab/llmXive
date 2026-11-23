import os
import sys
import json
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.utils.logging import setup_logger, log_pipeline_stage
from code.data.power_analysis import main as power_analysis_main
from code.data.validation import main as validation_main
from code.data.synthetic_generator import main as synthetic_generator_main
from code.data.ingestion import main as ingestion_main
from code.data.aggregation import main as aggregation_main
from code.analysis.modeling import main as modeling_main
from code.analysis.survival import main as survival_main
from code.analysis.robustness import main as robustness_main
from code.reports.generate_report import main as report_main
from code.utils.versioning import main as versioning_main

logger = setup_logger("pipeline")

def main():
    parser = argparse.ArgumentParser(description="Orchestrate the analysis pipeline.")
    parser.add_argument("--skip-power", action="store_true", help="Skip power analysis")
    parser.add_argument("--skip-consent", action="store_true", help="Skip consent check")
    parser.add_argument("--skip-gen", action="store_true", help="Skip synthetic data generation")
    parser.add_argument("--skip-ingestion", action="store_true", help="Skip ingestion")
    parser.add_argument("--skip-aggregation", action="store_true", help="Skip aggregation")
    parser.add_argument("--skip-modeling", action="store_true", help="Skip modeling")
    parser.add_argument("--skip-survival", action="store_true", help="Skip survival analysis")
    parser.add_argument("--skip-robustness", action="store_true", help="Skip robustness")
    parser.add_argument("--skip-report", action="store_true", help="Skip report generation")
    parser.add_argument("--skip-versioning", action="store_true", help="Skip versioning")
    args = parser.parse_args()

    try:
        log_pipeline_stage(logger, "START", "Pipeline Execution")

        if not args.skip_power:
            log_pipeline_stage(logger, "RUN", "Power Analysis")
            power_analysis_main()

        if not args.skip_consent:
            log_pipeline_stage(logger, "RUN", "Consent Check")
            validation_main()

        if not args.skip_gen:
            log_pipeline_stage(logger, "RUN", "Synthetic Data Generation")
            synthetic_generator_main()

        if not args.skip_ingestion:
            log_pipeline_stage(logger, "RUN", "Data Ingestion")
            ingestion_main()

        if not args.skip_aggregation:
            log_pipeline_stage(logger, "RUN", "Data Aggregation")
            aggregation_main()

        if not args.skip_modeling:
            log_pipeline_stage(logger, "RUN", "Statistical Modeling")
            modeling_main()

        if not args.skip_survival:
            log_pipeline_stage(logger, "RUN", "Survival Analysis")
            survival_main()

        if not args.skip_robustness:
            log_pipeline_stage(logger, "RUN", "Robustness Validation")
            robustness_main()

        if not args.skip_report:
            log_pipeline_stage(logger, "RUN", "Report Generation")
            report_main()

        if not args.skip_versioning:
            log_pipeline_stage(logger, "RUN", "Versioning & Hashing")
            versioning_main()

        log_pipeline_stage(logger, "SUCCESS", "Pipeline Completed Successfully")
        return 0

    except Exception as e:
        log_pipeline_stage(logger, "ERROR", f"Pipeline failed: {str(e)}")
        # Write error log
        error_log_path = "logs/pipeline_error.log"
        os.makedirs("logs", exist_ok=True)
        with open(error_log_path, "a") as f:
            f.write(f"{datetime.now()}: {str(e)}\n")
        raise

if __name__ == "__main__":
    sys.exit(main())
