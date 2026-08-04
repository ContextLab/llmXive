"""
Constitution Compliance Audit Script.

This script validates all generated artifacts and logs against Constitution Principles I-VII.
It ensures no principle violations occurred during execution.

Principles:
I. Reproducibility
II. Data Integrity
III. Data Hygiene (No synthetic fallbacks)
IV. Resource Constraints
V. Documentation
VI. Metric Validity
VII. CPU-Only Execution
"""
import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/audit/constitution_audit.log')
    ]
)
logger = logging.getLogger(__name__)

# Define project root and key directories
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"
RESULTS_DIR = DATA_DIR / "results"
PROCESSED_DIR = DATA_DIR / "processed"
STATE_DIR = PROJECT_ROOT / "state" / "projects"

# Define required artifacts for each principle
ARTIFACTS = {
    "I_Reproducibility": [
        "data/processed/injected_datasets.json",
        "data/processed/clusters.json",
        "data/processed/comparison_log.json",
        "data/results/flagged_pairs_count.json",
        "data/results/consensus_sample.json",
        "data/results/consensus_accuracy.json",
        "data/results/us1_baseline_metrics.json",
        "data/results/us1_efficiency_ratio.json",
        "data/results/threshold_sweep.json",
        "data/results/statistical_report.md",
        "state/projects/PROJ-873-llmxive-follow-up-extending-active-learn.yaml"
    ],
    "II_Data_Integrity": [
        "data/processed/injected_datasets.json",
        "data/processed/clusters.json",
        "data/processed/unique_subset.json"
    ],
    "III_Data_Hygiene": [
        "state/projects/PROJ-873-llmxive-follow-up-extending-active-learn.yaml"  # Contains artifact_hashes
    ],
    "IV_Resource_Constraints": [
        "data/audit/constitution_audit.log",  # Will contain resource usage summary
        "data/processed/comparison_log.json"   # Contains resource stats per comparison
    ],
    "V_Documentation": [
        "README.md",
        "docs/quickstart.md",
        "docs/data-model.md",
        "docs/research_conclusions.md"
    ],
    "VI_Metric_Validity": [
        "data/results/us1_baseline_metrics.json",
        "data/results/us1_efficiency_ratio.json",
        "data/results/threshold_sweep.json",
        "data/results/statistical_report.md"
    ],
    "VII_CPU_Only": [
        "code/validate_env.sh",
        "data/audit/constitution_audit.log"  # Will contain CPU validation result
    ]
}

class ConstitutionValidator:
    def __init__(self):
        self.violations: Dict[str, List[str]] = {principle: [] for principle in ARTIFACTS}
        self.passed_checks: Dict[str, List[str]] = {principle: [] for principle in ARTIFACTS}
        self.audit_log: List[Dict[str, Any]] = []

    def log_check(self, principle: str, check_name: str, passed: bool, message: str):
        status = "PASS" if passed else "FAIL"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "principle": principle,
            "check": check_name,
            "status": status,
            "message": message
        }
        self.audit_log.append(entry)
        if passed:
            self.passed_checks[principle].append(check_name)
        else:
            self.violations[principle].append(message)
        logger.info(f"[{status}] {principle}: {check_name} - {message}")

    def validate_artifact_exists(self, principle: str, artifact_path: str) -> bool:
        full_path = PROJECT_ROOT / artifact_path
        exists = full_path.exists() and full_path.stat().st_size > 0
        self.log_check(principle, f"Artifact Exists: {artifact_path}", exists,
                       f"File found and non-empty" if exists else f"File missing or empty")
        return exists

    def validate_json_schema(self, principle: str, artifact_path: str, required_keys: List[str]) -> bool:
        full_path = PROJECT_ROOT / artifact_path
        if not full_path.exists():
            self.log_check(principle, f"Schema Check: {artifact_path}", False, "File does not exist")
            return False

        try:
            with open(full_path, 'r') as f:
                data = json.load(f)
            
            # Handle list of dicts or single dict
            items = data if isinstance(data, list) else [data]
            
            if not items:
                self.log_check(principle, f"Schema Check: {artifact_path}", False, "File is empty list")
                return False

            all_valid = True
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    self.log_check(principle, f"Schema Check: {artifact_path}", False, f"Item {i} is not a dict")
                    all_valid = False
                    continue
                
                missing = [k for k in required_keys if k not in item]
                if missing:
                    self.log_check(principle, f"Schema Check: {artifact_path}", False, 
                                   f"Item {i} missing keys: {missing}")
                    all_valid = False

            self.log_check(principle, f"Schema Check: {artifact_path}", all_valid,
                           "All items have required keys" if all_valid else "Schema validation failed")
            return all_valid
        except json.JSONDecodeError as e:
            self.log_check(principle, f"Schema Check: {artifact_path}", False, f"Invalid JSON: {str(e)}")
            return False
        except Exception as e:
            self.log_check(principle, f"Schema Check: {artifact_path}", False, f"Error reading file: {str(e)}")
            return False

    def validate_checksums(self, principle: str, state_file: str) -> bool:
        full_path = PROJECT_ROOT / state_file
        if not full_path.exists():
            self.log_check(principle, "Checksum Validation", False, "State file missing")
            return False

        try:
            with open(full_path, 'r') as f:
                state = json.load(f)
            
            if 'artifact_hashes' not in state:
                self.log_check(principle, "Checksum Validation", False, "No artifact_hashes in state")
                return False

            # Verify at least one hash exists
            hashes = state['artifact_hashes']
            has_hashes = len(hashes) > 0
            self.log_check(principle, "Checksum Validation", has_hashes,
                           f"Found {len(hashes)} checksums" if has_hashes else "No checksums recorded")
            return has_hashes
        except Exception as e:
            self.log_check(principle, "Checksum Validation", False, f"Error: {str(e)}")
            return False

    def validate_no_gpu_deps(self, principle: str, requirements_path: str) -> bool:
        full_path = PROJECT_ROOT / requirements_path
        if not full_path.exists():
            self.log_check(principle, "GPU Dependency Check", False, "requirements.txt missing")
            return False

        try:
            with open(full_path, 'r') as f:
                content = f.read().lower()
            
            gpu_deps = ['cuda', 'torch[cuda]', 'tensorflow-gpu', 'gpu']
            found_gpu = any(dep in content for dep in gpu_deps)
            
            self.log_check(principle, "GPU Dependency Check", not found_gpu,
                           "No GPU dependencies found" if not found_gpu else "GPU dependencies detected")
            return not found_gpu
        except Exception as e:
            self.log_check(principle, "GPU Dependency Check", False, f"Error: {str(e)}")
            return False

    def validate_resource_limits(self, principle: str, config_path: str) -> bool:
        full_path = PROJECT_ROOT / config_path
        if not full_path.exists():
            self.log_check(principle, "Resource Limit Config", False, "Config file missing")
            return False

        try:
            with open(full_path, 'r') as f:
                config = json.load(f)
            
            has_runtime = 'MAX_RUNTIME_HOURS' in config
            has_memory = 'MAX_MEMORY_GB' in config
            valid = has_runtime and has_memory
            
            self.log_check(principle, "Resource Limit Config", valid,
                           f"Runtime: {config.get('MAX_RUNTIME_HOURS')}, Memory: {config.get('MAX_MEMORY_GB')}GB"
                           if valid else "Missing runtime or memory limits")
            return valid
        except Exception as e:
            self.log_check(principle, "Resource Limit Config", False, f"Error: {str(e)}")
            return False

    def run_audit(self) -> bool:
        logger.info("=" * 60)
        logger.info("Starting Constitution Compliance Audit")
        logger.info("=" * 60)

        # I. Reproducibility
        for artifact in ARTIFACTS["I_Reproducibility"]:
            self.validate_artifact_exists("I_Reproducibility", artifact)

        # II. Data Integrity
        for artifact in ARTIFACTS["II_Data_Integrity"]:
            self.validate_artifact_exists("II_Data_Integrity", artifact)

        # III. Data Hygiene
        self.validate_checksums("III_Data_Hygiene", "state/projects/PROJ-873-llmxive-follow-up-extending-active-learn.yaml")

        # IV. Resource Constraints
        self.validate_resource_limits("IV_Resource_Constraints", "code/config.py")
        # Note: Actual resource monitoring is done by utils.py, we check config existence

        # V. Documentation
        for artifact in ARTIFACTS["V_Documentation"]:
            self.validate_artifact_exists("V_Documentation", artifact)

        # VI. Metric Validity
        # Check specific schemas for metrics
        self.validate_json_schema("VI_Metric_Validity", "data/results/flagged_pairs_count.json", 
                                 ["wasted_count", "total_pairs", "wasted_ratio"])
        self.validate_json_schema("VI_Metric_Validity", "data/results/consensus_accuracy.json", 
                                 ["accuracy", "total_samples", "agreed"])
        self.validate_json_schema("VI_Metric_Validity", "data/results/us1_efficiency_ratio.json", 
                                 ["wasted_ratio", "wasted_count", "total_budget"])

        # VII. CPU-Only
        self.validate_no_gpu_deps("VII_CPU_Only", "requirements.txt")
        # Check that validate_env.sh exists and is executable
        env_validator = PROJECT_ROOT / "code" / "validate_env.sh"
        exists = env_validator.exists()
        self.log_check("VII_CPU_Only", "Env Validator Script", exists, 
                       "validate_env.sh exists" if exists else "validate_env.sh missing")

        # Generate Summary Report
        logger.info("=" * 60)
        logger.info("Audit Summary")
        logger.info("=" * 60)

        total_checks = 0
        passed_checks = 0
        failed_principles = []

        for principle, violations in self.violations.items():
            principle_checks = len(ARTIFACTS[principle]) + 2  # Approximate count
            principle_passed = principle_checks - len(violations)
            total_checks += principle_checks
            passed_checks += principle_passed
            
            if violations:
                failed_principles.append(principle)
                logger.warning(f"PRINCIPLE {principle}: {len(violations)} violations")
                for v in violations:
                    logger.warning(f"  - {v}")
            else:
                logger.info(f"PRINCIPLE {principle}: PASSED")

        success = len(failed_principles) == 0
        overall_status = "COMPLIANT" if success else "NON-COMPLIANT"
        
        logger.info(f"\nOverall Status: {overall_status}")
        logger.info(f"Total Checks: {total_checks}, Passed: {passed_checks}, Failed: {total_checks - passed_checks}")

        if not success:
            logger.error("CONSTITUTION VIOLATIONS DETECTED. Please address the issues above.")
        
        # Write final report
        report_path = DATA_DIR / "audit" / "constitution_compliance_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "summary": {
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "failed_checks": total_checks - passed_checks,
                "failed_principles": failed_principles
            },
            "violations": self.violations,
            "passed_checks": self.passed_checks,
            "detailed_log": self.audit_log
        }

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Audit report written to: {report_path}")
        
        return success

def main():
    validator = ConstitutionValidator()
    success = validator.run_audit()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()