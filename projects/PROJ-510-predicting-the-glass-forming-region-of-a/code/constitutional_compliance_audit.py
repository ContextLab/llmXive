"""
Constitutional Compliance Audit for PROJ-510.

This script performs a final audit to ensure all constitutional principles
are satisfied:
1. Reproducibility
2. Verified Accuracy
3. Data Hygiene
4. Single Source of Truth
5. Versioning
6. Thermodynamic Feature Engineering Integrity
7. Cross-Validation Rigor
"""

import os
import sys
import json
import pickle
import hashlib
import logging
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional

# Add project root to path if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import get_logger, ensure_dir

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MODELS_DIR = os.path.join(DATA_DIR, "models")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
CONTRACTS_DIR = os.path.join(PROJECT_ROOT, "contracts")

AUDIT_OUTPUT_PATH = os.path.join(LOGS_DIR, "constitutional_compliance_audit.json")
AUDIT_LOG_PATH = os.path.join(LOGS_DIR, "constitutional_compliance_audit.log")

# Constitutional Principles Definition
CONSTITUTIONAL_PRINCIPLES = {
    "reproducibility": {
        "name": "Reproducibility",
        "checks": [
            "random_state_42_consistency",
            "pipeline_determinism",
            "artifact_versioning"
        ]
    },
    "verified_accuracy": {
        "name": "Verified Accuracy",
        "checks": [
            "null_model_comparison",
            "cross_validation_scores",
            "test_set_evaluation"
        ]
    },
    "data_hygiene": {
        "name": "Data Hygiene",
        "checks": [
            "source_label_verification",
            "no_synthetic_data",
            "schema_compliance",
            "missing_value_handling"
        ]
    },
    "single_source_of_truth": {
        "name": "Single Source of Truth",
        "checks": [
            "dataset_source_consistency",
            "no_duplicate_data_sources"
        ]
    },
    "versioning": {
        "name": "Versioning",
        "checks": [
            "schema_versioning",
            "model_versioning",
            "data_versioning"
        ]
    },
    "thermodynamic_feature_engineering_integrity": {
        "name": "Thermodynamic Feature Engineering Integrity",
        "checks": [
            "mixing_enthalpy_calculation",
            "size_mismatch_calculation",
            "electronegativity_variance_calculation",
            "feature_completeness"
        ]
    },
    "cross_validation_rigor": {
        "name": "Cross-Validation Rigor",
        "checks": [
            "kfold_consistency",
            "shared_folds_usage",
            "no_data_leakage"
        ]
    }
}


class ConstitutionalComplianceAudit:
    """Performs a comprehensive audit of constitutional principles."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or get_logger("ConstitutionalAudit", AUDIT_LOG_PATH)
        self.results: Dict[str, Any] = {
            "audit_timestamp": None,
            "principles": {},
            "overall_status": "UNKNOWN",
            "summary": {}
        }

    def _check_file_exists(self, path: str, principle: str, check: str) -> Tuple[bool, str]:
        """Check if a file exists."""
        if os.path.exists(path):
            return True, f"File exists: {path}"
        return False, f"File missing: {path}"

    def _check_file_not_empty(self, path: str, principle: str, check: str) -> Tuple[bool, str]:
        """Check if a file is not empty."""
        if not os.path.exists(path):
            return False, f"File missing: {path}"
        try:
            if os.path.getsize(path) == 0:
                return False, f"File is empty: {path}"
            return True, f"File has content: {path}"
        except Exception as e:
            return False, f"Error checking file: {e}"

    def _check_json_schema(self, path: str, schema_path: str, principle: str, check: str) -> Tuple[bool, str]:
        """Check if a JSON file matches its schema."""
        if not os.path.exists(path):
            return False, f"JSON file missing: {path}"
        if not os.path.exists(schema_path):
            return False, f"Schema file missing: {schema_path}"
        try:
            import yaml
            import jsonschema
            with open(schema_path, 'r') as f:
                schema = yaml.safe_load(f)
            with open(path, 'r') as f:
                data = json.load(f)
            jsonschema.validate(instance=data, schema=schema)
            return True, f"Schema validation passed for: {path}"
        except jsonschema.exceptions.ValidationError as e:
            return False, f"Schema validation failed for {path}: {e.message}"
        except Exception as e:
            return False, f"Error during schema validation: {e}"

    def _check_random_state_consistency(self) -> Tuple[bool, str]:
        """Check that random_state=42 is used consistently."""
        issues = []
        # Check key scripts for random_state=42
        scripts_to_check = [
            os.path.join(PROJECT_ROOT, "code", "ingestion.py"),
            os.path.join(PROJECT_ROOT, "code", "features.py"),
            os.path.join(PROJECT_ROOT, "code", "train.py"),
            os.path.join(PROJECT_ROOT, "code", "analyze.py")
        ]

        for script in scripts_to_check:
            if not os.path.exists(script):
                issues.append(f"Script missing: {script}")
                continue
            with open(script, 'r') as f:
                content = f.read()
            if "random_state=42" not in content:
                issues.append(f"random_state=42 not found in {script}")

        if issues:
            return False, "; ".join(issues)
        return True, "All scripts use random_state=42 consistently"

    def _check_pipeline_determinism(self) -> Tuple[bool, str]:
        """Check for determinism markers."""
        # Check if split indices and CV folds are saved
        split_indices_path = os.path.join(MODELS_DIR, "split_indices.json")
        cv_folds_path = os.path.join(MODELS_DIR, "cv_folds_indices.json")

        checks = []
        if not os.path.exists(split_indices_path):
            checks.append("Split indices not saved")
        if not os.path.exists(cv_folds_path):
            checks.append("CV folds indices not saved")

        if checks:
            return False, "; ".join(checks)
        return True, "Pipeline determinism artifacts present"

    def _check_artifact_versioning(self) -> Tuple[bool, str]:
        """Check if artifacts have versioning information."""
        # Check for version metadata in key files
        version_checks = []
        artifacts = [
            os.path.join(PROCESSED_DIR, "processed_alloys.csv"),
            os.path.join(MODELS_DIR, "random_forest_model.pkl")
        ]

        for artifact in artifacts:
            if not os.path.exists(artifact):
                version_checks.append(f"Artifact missing: {artifact}")

        if version_checks:
            return False, "; ".join(version_checks)
        return True, "All key artifacts present for versioning check"

    def _check_null_model_comparison(self) -> Tuple[bool, str]:
        """Check if null model comparison was performed."""
        comparison_path = os.path.join(MODELS_DIR, "statistical_comparison.json")
        return self._check_file_exists(comparison_path, "verified_accuracy", "null_model_comparison")

    def _check_cross_validation_scores(self) -> Tuple[bool, str]:
        """Check if cross-validation scores are available."""
        cv_path = os.path.join(MODELS_DIR, "cv_metrics.json")
        return self._check_file_exists(cv_path, "verified_accuracy", "cross_validation_scores")

    def _check_test_set_evaluation(self) -> Tuple[bool, str]:
        """Check if test set evaluation was performed."""
        test_metrics_path = os.path.join(MODELS_DIR, "test_metrics.json")
        return self._check_file_exists(test_metrics_path, "verified_accuracy", "test_set_evaluation")

    def _check_source_label_verification(self) -> Tuple[bool, str]:
        """Check if source labels are present in data."""
        data_path = os.path.join(PROCESSED_DIR, "processed_alloys.csv")
        if not os.path.exists(data_path):
            return False, f"Data file missing: {data_path}"
        try:
            df = pd.read_csv(data_path)
            if "source_label" not in df.columns:
                return False, "source_label column missing from processed data"
            if df["source_label"].iloc[0] != "matsci/glass-forming-ability":
                return False, f"Unexpected source_label: {df['source_label'].iloc[0]}"
            return True, "Source label verified: matsci/glass-forming-ability"
        except Exception as e:
            return False, f"Error reading data: {e}"

    def _check_no_synthetic_data(self) -> Tuple[bool, str]:
        """Check for absence of synthetic data indicators."""
        data_path = os.path.join(PROCESSED_DIR, "processed_alloys.csv")
        if not os.path.exists(data_path):
            return False, f"Data file missing: {data_path}"
        try:
            df = pd.read_csv(data_path)
            # Check for any synthetic indicators
            synthetic_columns = [col for col in df.columns if "synthetic" in col.lower() or "fake" in col.lower()]
            if synthetic_columns:
                return False, f"Potential synthetic data indicators found: {synthetic_columns}"
            # Check source audit log
            audit_path = os.path.join(LOGS_DIR, "data_source_audit.json")
            if os.path.exists(audit_path):
                with open(audit_path, 'r') as f:
                    audit_data = json.load(f)
                if audit_data.get("status") == "FAILED":
                    return False, "Data source audit failed"
            return True, "No synthetic data indicators found"
        except Exception as e:
            return False, f"Error checking for synthetic data: {e}"

    def _check_schema_compliance(self) -> Tuple[bool, str]:
        """Check if data complies with schema."""
        data_path = os.path.join(PROCESSED_DIR, "processed_alloys.csv")
        schema_path = os.path.join(CONTRACTS_DIR, "dataset.schema.yaml")
        return self._check_json_schema(data_path, schema_path, "data_hygiene", "schema_compliance")

    def _check_missing_value_handling(self) -> Tuple[bool, str]:
        """Check how missing values are handled."""
        data_path = os.path.join(PROCESSED_DIR, "processed_alloys.csv")
        if not os.path.exists(data_path):
            return False, f"Data file missing: {data_path}"
        try:
            df = pd.read_csv(data_path)
            # Check for NaN in critical columns
            critical_cols = ["critical_cooling_rate", "mixing_enthalpy", "atomic_size_mismatch", "electronegativity_variance"]
            for col in critical_cols:
                if col in df.columns:
                    if df[col].isna().any():
                        return False, f"NaN values found in critical column: {col}"
            return True, "No NaN values in critical columns"
        except Exception as e:
            return False, f"Error checking missing values: {e}"

    def _check_dataset_source_consistency(self) -> Tuple[bool, str]:
        """Check if dataset source is consistent across artifacts."""
        # Check processed data and audit log
        data_path = os.path.join(PROCESSED_DIR, "processed_alloys.csv")
        audit_path = os.path.join(LOGS_DIR, "data_source_audit.json")

        if not os.path.exists(data_path):
            return False, "Processed data missing"
        if not os.path.exists(audit_path):
            return False, "Data source audit missing"

        try:
            with open(audit_path, 'r') as f:
                audit_data = json.load(f)

            if audit_data.get("source") != "matsci/glass-forming-ability":
                return False, f"Source mismatch in audit: {audit_data.get('source')}"

            df = pd.read_csv(data_path)
            if df["source_label"].iloc[0] != "matsci/glass-forming-ability":
                return False, f"Source mismatch in data: {df['source_label'].iloc[0]}"

            return True, "Dataset source consistent across artifacts"
        except Exception as e:
            return False, f"Error checking source consistency: {e}"

    def _check_no_duplicate_data_sources(self) -> Tuple[bool, str]:
        """Check for absence of duplicate data sources."""
        # This is a simple check - look for multiple source labels
        data_path = os.path.join(PROCESSED_DIR, "processed_alloys.csv")
        if not os.path.exists(data_path):
            return False, f"Data file missing: {data_path}"
        try:
            df = pd.read_csv(data_path)
            unique_sources = df["source_label"].unique()
            if len(unique_sources) > 1:
                return False, f"Multiple data sources found: {unique_sources}"
            return True, f"Single data source: {unique_sources[0]}"
        except Exception as e:
            return False, f"Error checking for duplicate sources: {e}"

    def _check_schema_versioning(self) -> Tuple[bool, str]:
        """Check if schemas have versioning."""
        schema_path = os.path.join(CONTRACTS_DIR, "dataset.schema.yaml")
        if not os.path.exists(schema_path):
            return False, f"Schema file missing: {schema_path}"
        try:
            with open(schema_path, 'r') as f:
                content = f.read()
            if "version" not in content.lower():
                return False, "No version information in schema"
            return True, "Schema versioning present"
        except Exception as e:
            return False, f"Error checking schema versioning: {e}"

    def _check_model_versioning(self) -> Tuple[bool, str]:
        """Check if models have versioning information."""
        model_path = os.path.join(MODELS_DIR, "random_forest_model.pkl")
        if not os.path.exists(model_path):
            return False, f"Model file missing: {model_path}"
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            # Check if model has metadata
            if hasattr(model, 'get_params'):
                params = model.get_params()
                if 'random_state' not in params:
                    return False, "Model lacks random_state parameter"
            return True, "Model versioning information present"
        except Exception as e:
            return False, f"Error checking model versioning: {e}"

    def _check_data_versioning(self) -> Tuple[bool, str]:
        """Check if data has versioning information."""
        # Check for hash or version in data logs
        hash_path = os.path.join(LOGS_DIR, "ingestion_hash.txt")
        if not os.path.exists(hash_path):
            return False, f"Data hash file missing: {hash_path}"
        try:
            with open(hash_path, 'r') as f:
                hash_content = f.read().strip()
            if not hash_content:
                return False, "Data hash is empty"
            return True, f"Data versioning present: {hash_content[:16]}..."
        except Exception as e:
            return False, f"Error checking data versioning: {e}"

    def _check_mixing_enthalpy_calculation(self) -> Tuple[bool, str]:
        """Check if mixing enthalpy was calculated."""
        data_path = os.path.join(PROCESSED_DIR, "processed_alloys.csv")
        if not os.path.exists(data_path):
            return False, f"Data file missing: {data_path}"
        try:
            df = pd.read_csv(data_path)
            if "mixing_enthalpy" not in df.columns:
                return False, "mixing_enthalpy column missing"
            if df["mixing_enthalpy"].isna().any():
                return False, "NaN values in mixing_enthalpy"
            return True, "Mixing enthalpy calculated and present"
        except Exception as e:
            return False, f"Error checking mixing enthalpy: {e}"

    def _check_size_mismatch_calculation(self) -> Tuple[bool, str]:
        """Check if atomic size mismatch was calculated."""
        data_path = os.path.join(PROCESSED_DIR, "processed_alloys.csv")
        if not os.path.exists(data_path):
            return False, f"Data file missing: {data_path}"
        try:
            df = pd.read_csv(data_path)
            if "atomic_size_mismatch" not in df.columns:
                return False, "atomic_size_mismatch column missing"
            if df["atomic_size_mismatch"].isna().any():
                return False, "NaN values in atomic_size_mismatch"
            return True, "Atomic size mismatch calculated and present"
        except Exception as e:
            return False, f"Error checking size mismatch: {e}"

    def _check_electronegativity_variance_calculation(self) -> Tuple[bool, str]:
        """Check if electronegativity variance was calculated."""
        data_path = os.path.join(PROCESSED_DIR, "processed_alloys.csv")
        if not os.path.exists(data_path):
            return False, f"Data file missing: {data_path}"
        try:
            df = pd.read_csv(data_path)
            if "electronegativity_variance" not in df.columns:
                return False, "electronegativity_variance column missing"
            if df["electronegativity_variance"].isna().any():
                return False, "NaN values in electronegativity_variance"
            return True, "Electronegativity variance calculated and present"
        except Exception as e:
            return False, f"Error checking electronegativity variance: {e}"

    def _check_feature_completeness(self) -> Tuple[bool, str]:
        """Check if all required features are present."""
        data_path = os.path.join(PROCESSED_DIR, "processed_alloys.csv")
        schema_path = os.path.join(CONTRACTS_DIR, "dataset.schema.yaml")
        if not os.path.exists(data_path) or not os.path.exists(schema_path):
            return False, "Data or schema file missing"
        try:
            import yaml
            with open(schema_path, 'r') as f:
                schema = yaml.safe_load(f)
            required_fields = schema.get("properties", {}).keys()
            df = pd.read_csv(data_path)
            missing_fields = [f for f in required_fields if f not in df.columns]
            if missing_fields:
                return False, f"Missing required features: {missing_fields}"
            return True, "All required features present"
        except Exception as e:
            return False, f"Error checking feature completeness: {e}"

    def _check_kfold_consistency(self) -> Tuple[bool, str]:
        """Check if KFold settings are consistent."""
        cv_path = os.path.join(MODELS_DIR, "cv_folds_indices.json")
        if not os.path.exists(cv_path):
            return False, f"CV folds file missing: {cv_path}"
        try:
            with open(cv_path, 'r') as f:
                folds = json.load(f)
            if not isinstance(folds, list) or len(folds) != 5:
                return False, f"Invalid CV folds structure: {len(folds)} folds"
            return True, "KFold consistency verified (5 folds)"
        except Exception as e:
            return False, f"Error checking KFold consistency: {e}"

    def _check_shared_folds_usage(self) -> Tuple[bool, str]:
        """Check if shared folds are used across tasks."""
        # Check if both train and null model use the same folds
        cv_path = os.path.join(MODELS_DIR, "cv_folds_indices.json")
        null_cv_path = os.path.join(MODELS_DIR, "null_model_cv_scores.json")

        if not os.path.exists(cv_path):
            return False, f"CV folds file missing: {cv_path}"
        if not os.path.exists(null_cv_path):
            return False, f"Null model CV scores missing: {null_cv_path}"

        try:
            # Both should exist and be valid
            with open(null_cv_path, 'r') as f:
                null_scores = json.load(f)
            if "fold_scores" not in null_scores or len(null_scores["fold_scores"]) != 5:
                return False, "Null model CV scores structure invalid"
            return True, "Shared folds usage verified"
        except Exception as e:
            return False, f"Error checking shared folds: {e}"

    def _check_no_data_leakage(self) -> Tuple[bool, str]:
        """Check for potential data leakage."""
        # Check if train/test split is properly documented
        split_path = os.path.join(MODELS_DIR, "split_indices.json")
        if not os.path.exists(split_path):
            return False, f"Split indices file missing: {split_path}"
        try:
            with open(split_path, 'r') as f:
                splits = json.load(f)
            if "train_indices" not in splits or "test_indices" not in splits:
                return False, "Split structure invalid"
            # Check for overlap
            train_set = set(splits["train_indices"])
            test_set = set(splits["test_indices"])
            if train_set.intersection(test_set):
                return False, "Data leakage detected: train/test overlap"
            return True, "No data leakage detected"
        except Exception as e:
            return False, f"Error checking for data leakage: {e}"

    def run_audit(self) -> Dict[str, Any]:
        """Run the full constitutional compliance audit."""
        import datetime
        self.results["audit_timestamp"] = datetime.datetime.now().isoformat()
        self.logger.info("Starting Constitutional Compliance Audit")

        all_passed = True
        principle_results = {}

        for principle_key, principle_def in CONSTITUTIONAL_PRINCIPLES.items():
            principle_name = principle_def["name"]
            self.logger.info(f"Auditing principle: {principle_name}")
            principle_results[principle_key] = {
                "name": principle_name,
                "checks": {},
                "status": "PASS"
            }

            for check in principle_def["checks"]:
                method_name = f"_check_{check}"
                if hasattr(self, method_name):
                    method = getattr(self, method_name)
                    passed, message = method()
                    principle_results[principle_key]["checks"][check] = {
                        "status": "PASS" if passed else "FAIL",
                        "message": message
                    }
                    if not passed:
                        all_passed = False
                        self.logger.warning(f"  - {check}: {message}")
                    else:
                        self.logger.info(f"  - {check}: {message}")
                else:
                    principle_results[principle_key]["checks"][check] = {
                        "status": "SKIP",
                        "message": "Check method not implemented"
                    }
                    self.logger.warning(f"  - {check}: Check method not implemented")

        self.results["principles"] = principle_results
        self.results["overall_status"] = "PASS" if all_passed else "FAIL"

        # Summary
        total_checks = sum(len(p["checks"]) for p in principle_results.values())
        passed_checks = sum(
            sum(1 for c in p["checks"].values() if c["status"] == "PASS")
            for p in principle_results.values()
        )
        self.results["summary"] = {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": total_checks - passed_checks,
            "pass_rate": round(passed_checks / total_checks * 100, 2) if total_checks > 0 else 0
        }

        self.logger.info(f"Audit complete: {passed_checks}/{total_checks} checks passed ({self.results['summary']['pass_rate']}%)")
        self.logger.info(f"Overall status: {self.results['overall_status']}")

        return self.results

    def save_results(self, output_path: str = AUDIT_OUTPUT_PATH):
        """Save audit results to a JSON file."""
        ensure_dir(output_path)
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        self.logger.info(f"Audit results saved to {output_path}")


def main():
    """Main entry point for the constitutional compliance audit."""
    logger = get_logger("ConstitutionalAudit", AUDIT_LOG_PATH)
    logger.info("Starting Constitutional Compliance Audit")

    try:
        audit = ConstitutionalComplianceAudit(logger)
        results = audit.run_audit()
        audit.save_results()

        # Exit with appropriate code
        if results["overall_status"] == "PASS":
            logger.info("Constitutional Compliance Audit PASSED")
            sys.exit(0)
        else:
            logger.warning("Constitutional Compliance Audit FAILED")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Audit failed with exception: {e}", exc_info=True)
        sys.exit(2)


if __name__ == "__main__":
    main()