"""
Validator for Analysis outputs (AnalysisResult schema).
"""
import json
from typing import Any, Dict, List, Optional
from dataclasses import asdict
from data.models import AnalysisResult


class AnalysisValidator:
    """
    Validates Analysis artifacts (AnalysisResult objects) against the expected schema.
    """

    REQUIRED_FIELDS = [
        "analysis_id",
        "timestamp",
        "method_comparison",
        "ks_test_p_value",
        "ks_test_statistic",
        "change_point_threshold",
        "change_point_confidence",
        "memory_reduction_pct",
        "summary_text",
        "cutoffs_tested",
    ]

    @classmethod
    def validate_analysis_result(cls, result: AnalysisResult) -> Dict[str, Any]:
        """
        Validates a single AnalysisResult instance.

        Args:
            result: The AnalysisResult instance to validate.

        Returns:
            A dict with 'valid' (bool) and 'errors' (list of str).
        """
        errors = []
        result_dict = asdict(result)

        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            if field not in result_dict or result_dict[field] is None:
                errors.append(f"Missing required field: {field}")

        # Validate numeric constraints
        numeric_fields = [
            "ks_test_p_value",
            "ks_test_statistic",
            "change_point_confidence",
            "memory_reduction_pct",
        ]

        for field in numeric_fields:
            val = result_dict.get(field)
            if val is not None:
                if not isinstance(val, (int, float)):
                    errors.append(f"{field} must be numeric")

        # Specific range checks
        if result_dict.get("ks_test_p_value") is not None:
            if not (0 <= result_dict["ks_test_p_value"] <= 1):
                errors.append("ks_test_p_value must be in [0, 1]")

        if result_dict.get("ks_test_statistic") is not None:
            if not (0 <= result_dict["ks_test_statistic"] <= 1):
                errors.append("ks_test_statistic must be in [0, 1]")

        if result_dict.get("change_point_confidence") is not None:
            if not (0 <= result_dict["change_point_confidence"] <= 1):
                errors.append("change_point_confidence must be in [0, 1]")

        # Validate change_point_threshold (should be a float or None)
        if result_dict.get("change_point_threshold") is not None:
            if not isinstance(result_dict["change_point_threshold"], (int, float)):
                errors.append("change_point_threshold must be numeric or null")

        # Validate cutoffs_tested is a list
        if result_dict.get("cutoffs_tested") is not None:
            if not isinstance(result_dict["cutoffs_tested"], list):
                errors.append("cutoffs_tested must be a list")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    @classmethod
    def validate_analysis_file(cls, file_path: str) -> Dict[str, Any]:
        """
        Validates a JSON file containing an AnalysisResult record.

        Args:
            file_path: Path to the JSON file.

        Returns:
            Validation result dict.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return {
                    "valid": False,
                    "errors": ["JSON root must be a dictionary (single AnalysisResult)"],
                    "stats": {},
                }

            # Check required fields in raw dict
            missing = set(cls.REQUIRED_FIELDS) - set(data.keys())
            if missing:
                return {
                    "valid": False,
                    "errors": [f"Missing fields in analysis record: {missing}"],
                    "stats": {},
                }

            try:
                result = AnalysisResult(**data)
            except TypeError as e:
                return {
                    "valid": False,
                    "errors": [f"Failed to instantiate AnalysisResult: {str(e)}"],
                    "stats": {},
                }

            return {
                "valid": True,
                "errors": [],
                "stats": {"analysis_id": result.analysis_id},
            }

        except FileNotFoundError:
            return {
                "valid": False,
                "errors": [f"File not found: {file_path}"],
                "stats": {},
            }
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "errors": [f"Invalid JSON: {str(e)}"],
                "stats": {},
            }
