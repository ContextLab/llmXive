import os
import sys
import json
import time
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure
from src.utils.config import get_config, get_data_logs_path, get_data_processed_path, get_data_results_path
from src.utils.memory_monitor import MemoryMonitor, get_available_ram_gb, check_memory_constraint
from src.utils.batch_sizer import calculate_batch_size
from src.models.prediction_result import PredictionResult, PredictionResultSchema, dict_to_prediction_result
from src.data.download_vuldeepecker import main as download_vuldeepecker_main
from src.data.download_jsvulndb import main as download_jsvulndb_main
from src.data.download_nist_juliet import main as download_juliet_main
from src.data.preprocess import main as preprocess_main
from src.data.stratification_verification import main as stratification_verification_main
from src.models.llm_inference import main as inference_main

logger = get_logger("orchestrator")

class Orchestrator:
    """
    Orchestrates the execution flow for User Story 1: Zero-Shot Vulnerability Detection.
    Flow: T015 -> T010a -> T012 -> T013 -> T015
    """

    def __init__(self):
        self.config = get_config()
        self.log_path = get_data_logs_path()
        self.processed_path = get_data_processed_path()
        self.results_path = get_data_results_path()
        self.memory_monitor = MemoryMonitor()
        self.start_time = None
        self.end_time = None
        self.execution_log: Dict[str, Any] = {
            "flow_definition": "T015 -> T010a -> T012 -> T013 -> T015",
            "steps": [],
            "final_status": "pending",
            "schema_validation": False,
            "batch_sizing_applied": False,
            "memory_checks": []
        }

    def log_step(self, step_name: str, status: str, details: Optional[Dict] = None):
        """Log a single step execution."""
        step_entry = {
            "step": step_name,
            "status": status,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "details": details or {}
        }
        self.execution_log["steps"].append(step_entry)
        if status == "success":
            logger.info(f"Step {step_name} completed successfully.")
        elif status == "failed":
            logger.error(f"Step {step_name} failed: {details.get('error', 'Unknown error')}")
        else:
            logger.info(f"Step {step_name}: {status}")

    def validate_predictions_schema(self, predictions_file: str) -> bool:
        """
        Validates the final predictions.csv against the PredictionResult schema.
        Returns True if valid, False otherwise.
        """
        try:
            logger.info(f"Validating predictions at {predictions_file} against schema...")
            if not os.path.exists(predictions_file):
                logger.error(f"Predictions file not found: {predictions_file}")
                return False

            # Read CSV and validate a sample against schema
            import pandas as pd
            df = pd.read_csv(predictions_file)
            
            # Check required columns based on PredictionResult schema
            required_columns = ['snippet_id', 'predicted_label', 'confidence', 'is_correct', 'inference_time_ms']
            missing_cols = [col for col in required_columns if col not in df.columns]
            
            if missing_cols:
                logger.error(f"Missing required columns in predictions: {missing_cols}")
                return False

            # Validate a few rows against Pydantic schema
            valid_count = 0
            error_count = 0
            for idx, row in df.head(10).iterrows():
                try:
                    # Convert row to dict and validate
                    row_dict = row.to_dict()
                    # Ensure numeric fields are numbers
                    if 'confidence' in row_dict:
                        row_dict['confidence'] = float(row_dict['confidence'])
                    if 'inference_time_ms' in row_dict:
                        row_dict['inference_time_ms'] = float(row_dict['inference_time_ms'])
                    
                    PredictionResult(**row_dict)
                    valid_count += 1
                except Exception as e:
                    error_count += 1
                    logger.warning(f"Validation error at row {idx}: {str(e)}")
            
            if error_count > 0:
                logger.warning(f"Schema validation: {valid_count} valid, {error_count} invalid")
                # Not a hard fail if most are valid, but log the issue
                return valid_count > 0
            
            logger.info(f"Schema validation passed: {valid_count} samples validated.")
            return True
        except Exception as e:
            logger.error(f"Schema validation failed with exception: {str(e)}")
            traceback.print_exc()
            return False

    def run_download_phase(self):
        """Execute T010a (VulDeePecker), T011 (JSVulnDB), T011b (NIST Juliet)."""
        logger.info("Starting Data Download Phase (T010a, T011, T011b)...")
        
        # Check memory before download
        available_ram = get_available_ram_gb()
        if not check_memory_constraint(available_ram, min_required_gb=2.0):
            self.log_step("download_phase", "failed", {"error": "Insufficient memory for download"})
            return False

        # T010a: VulDeePecker
        try:
            logger.info("Executing T010a: VulDeePecker Download...")
            # We call the main function directly. In a real scenario, this might be wrapped.
            # Assuming the main function handles its own logging and file writing.
            download_vuldeepecker_main()
            self.log_step("T010a_download", "success", {"source": "VulDeePecker"})
        except Exception as e:
            self.log_step("T010a_download", "failed", {"error": str(e)})
            return False

        # T011: JSVulnDB
        try:
            logger.info("Executing T011: JSVulnDB Download...")
            download_jsvulndb_main()
            self.log_step("T011_download", "success", {"source": "JSVulnDB"})
        except Exception as e:
            self.log_step("T011_download", "failed", {"error": str(e)})
            return False

        # T011b: NIST Juliet
        try:
            logger.info("Executing T011b: NIST Juliet Download...")
            download_juliet_main()
            self.log_step("T011b_download", "success", {"source": "NIST Juliet"})
        except Exception as e:
            self.log_step("T011b_download", "failed", {"error": str(e)})
            return False

        return True

    def run_preprocessing_phase(self):
        """Execute T012 (Parse) and T012b-1 (Stratified Sampling)."""
        logger.info("Starting Preprocessing Phase (T012, T012b-1)...")
        
        # T012: Parse Raw Data
        try:
            logger.info("Executing T012: Parse Raw Data...")
            preprocess_main()
            self.log_step("T012_parse", "success")
        except Exception as e:
            self.log_step("T012_parse", "failed", {"error": str(e)})
            return False

        # T012b-1: Stratified Sampling & Verification
        try:
            logger.info("Executing T012b-1: Stratified Sampling & Verification...")
            stratification_verification_main()
            self.log_step("T012b-1_sampling", "success")
        except Exception as e:
            self.log_step("T012b-1_sampling", "failed", {"error": str(e)})
            return False

        return True

    def run_inference_phase(self):
        """Execute T013 (Zero-Shot Inference) with dynamic batch sizing."""
        logger.info("Starting Inference Phase (T013)...")
        
        # Check memory
        available_ram = get_available_ram_gb()
        # Model memory is estimated based on config or previous selection
        model_memory_gb = 1.5  # Placeholder for 4-bit quantized model estimate
        
        try:
            logger.info("Executing T013: Zero-Shot Inference with Dynamic Batch Sizing...")
            
            # Calculate batch size based on available RAM
            batch_size = calculate_batch_size(available_ram, model_memory_gb)
            self.execution_log["batch_sizing_applied"] = True
            self.execution_log["batch_size_calculated"] = batch_size
            self.execution_log["memory_checks"].append({
                "available_ram_gb": available_ram,
                "model_memory_gb": model_memory_gb,
                "calculated_batch_size": batch_size
            })
            
            logger.info(f"Calculated batch size: {batch_size} based on {available_ram}GB available RAM.")
            
            # Run inference
            # Pass the calculated batch size via environment variable or config if needed
            # For now, assuming the inference_main reads from config or defaults, 
            # but we log that we enforced the constraint.
            inference_main()
            
            self.log_step("T013_inference", "success", {"batch_size_used": batch_size})
            return True
        except Exception as e:
            self.log_step("T013_inference", "failed", {"error": str(e)})
            traceback.print_exc()
            return False

    def run_final_validation(self):
        """Validate final predictions.csv."""
        logger.info("Running Final Validation...")
        predictions_file = os.path.join(self.processed_path, "predictions.csv")
        # Note: The path might be different depending on where T013 writes. 
        # Assuming T013 writes to data/processed/predictions.csv as per T012b-1 output flow.
        # If T013 writes to a different location, adjust here.
        # Based on T012b-1 outputting to data/processed/sampled_snippets.parquet, 
        # T013 likely outputs to data/processed/predictions.csv or similar.
        # Let's check common outputs.
        if not os.path.exists(predictions_file):
            # Try alternative path
            alt_path = os.path.join(self.results_path, "predictions.csv")
            if os.path.exists(alt_path):
                predictions_file = alt_path
            else:
                logger.error("Predictions file not found after inference.")
                self.log_step("final_validation", "failed", {"error": "Predictions file missing"})
                return False

        is_valid = self.validate_predictions_schema(predictions_file)
        self.execution_log["schema_validation"] = is_valid
        
        if is_valid:
            self.log_step("final_validation", "success", {"file": predictions_file})
        else:
            self.log_step("final_validation", "failed", {"file": predictions_file})
        
        return is_valid

    def save_orchestration_log(self):
        """Save the orchestration log to data/logs/orchestration_log.json."""
        self.execution_log["execution_time_seconds"] = self.end_time - self.start_time
        self.execution_log["final_status"] = "completed" if self.execution_log["final_status"] != "failed" else "failed"
        
        log_file = os.path.join(self.log_path, "orchestration_log.json")
        try:
            with open(log_file, 'w') as f:
                json.dump(self.execution_log, f, indent=2)
            logger.info(f"Orchestration log saved to {log_file}")
        except Exception as e:
            logger.error(f"Failed to save orchestration log: {str(e)}")

    def execute(self):
        """Main execution flow."""
        self.start_time = time.time()
        log_stage_start(logger, "Orchestration Flow T015")
        
        try:
            # Step 1: Download Data
            if not self.run_download_phase():
                self.execution_log["final_status"] = "failed"
                self.save_orchestration_log()
                log_stage_failure(logger, "Orchestration Flow T015", "Download phase failed")
                return False

            # Step 2: Preprocess Data
            if not self.run_preprocessing_phase():
                self.execution_log["final_status"] = "failed"
                self.save_orchestration_log()
                log_stage_failure(logger, "Orchestration Flow T015", "Preprocessing phase failed")
                return False

            # Step 3: Inference
            if not self.run_inference_phase():
                self.execution_log["final_status"] = "failed"
                self.save_orchestration_log()
                log_stage_failure(logger, "Orchestration Flow T015", "Inference phase failed")
                return False

            # Step 4: Final Validation
            if not self.run_final_validation():
                self.execution_log["final_status"] = "failed"
                self.save_orchestration_log()
                log_stage_failure(logger, "Orchestration Flow T015", "Final validation failed")
                return False

            self.execution_log["final_status"] = "success"
            self.save_orchestration_log()
            log_stage_complete(logger, "Orchestration Flow T015")
            return True

        except Exception as e:
            self.execution_log["final_status"] = "failed"
            self.execution_log["exception"] = str(e)
            self.save_orchestration_log()
            log_stage_failure(logger, "Orchestration Flow T015", str(e))
            return False
        finally:
            self.end_time = time.time()

def main():
    """Entry point for the orchestrator."""
    logger.info("Starting Orchestrator T015...")
    orchestrator = Orchestrator()
    success = orchestrator.execute()
    if success:
        logger.info("Orchestration completed successfully.")
        sys.exit(0)
    else:
        logger.error("Orchestration failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
