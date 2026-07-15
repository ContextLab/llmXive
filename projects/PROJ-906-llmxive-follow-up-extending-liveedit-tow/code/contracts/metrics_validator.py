"""
Validator for Metrics (MetricRecord) schema.
"""
import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import asdict
from data.models import MetricRecord


class MetricsValidator:
    """
    Validates Metric artifacts (MetricRecord objects) against the expected schema.
    """

    REQUIRED_FIELDS = [
        "clip_id",
        "method",
        "timestamp",
        "inference_time_s",
        "peak_memory_mb",
        "ssim_score",
        "bss_score",
        "flow_normalized_ssim",
        "avg_flow_magnitude",
        "invalid_flow_count",
        "motion_category",
    ]

    VALID_METHODS = {"baseline", "flow_coherence"}
    VALID_MOTION_CATEGORIES = {"static", "slow_rigid", "fast_non_rigid"}

    @classmethod
    def validate_metric_record(cls, record: MetricRecord) -> Dict[str, Any]:
        """
        Validates a single MetricRecord instance.

        Args:
            record: The MetricRecord instance to validate.

        Returns:
            A dict with 'valid' (bool) and 'errors' (list of str).
        """
        errors = []
        record_dict = asdict(record)

        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            if field not in record_dict or record_dict[field] is None:
                errors.append(f"Missing required field: {field}")

        # Validate method
        if record_dict.get("method") not in cls.VALID_METHODS:
            errors.append(
                f"Invalid method: {record_dict.get('method')}. "
                f"Must be one of {cls.VALID_METHODS}"
            )

        # Validate motion_category
        if record_dict.get("motion_category") not in cls.VALID_MOTION_CATEGORIES:
            errors.append(
                f"Invalid motion_category: {record_dict.get('motion_category')}. "
                f"Must be one of {cls.VALID_MOTION_CATEGORIES}"
            )

        # Validate numeric constraints
        numeric_fields = [
            "inference_time_s",
            "peak_memory_mb",
            "ssim_score",
            "bss_score",
            "flow_normalized_ssim",
            "avg_flow_magnitude",
            "invalid_flow_count",
        ]

        for field in numeric_fields:
            val = record_dict.get(field)
            if val is not None:
                if not isinstance(val, (int, float)):
                    errors.append(f"{field} must be numeric")
                elif field in ["inference_time_s", "peak_memory_mb", "avg_flow_magnitude"] and val < 0:
                    errors.append(f"{field} must be non-negative")
                elif field in ["ssim_score", "bss_score", "flow_normalized_ssim"]:
                    if val < 0 or val > 1:
                        errors.append(f"{field} must be in range [0, 1]")

        if record_dict.get("invalid_flow_count", 0) < 0:
            errors.append("invalid_flow_count must be non-negative")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    @classmethod
    def validate_metrics_list(cls, records: List[MetricRecord]) -> Dict[str, Any]:
        """
        Validates a list of MetricRecord instances.

        Args:
            records: List of MetricRecord instances.

        Returns:
            Validation result dict.
        """
        all_errors = []
        valid_count = 0
        method_counts = {"baseline": 0, "flow_coherence": 0}

        for i, record in enumerate(records):
            result = cls.validate_metric_record(record)
            if not result["valid"]:
                all_errors.extend([f"[Record {i}] {e}" for e in result["errors"]])
            else:
                valid_count += 1
                method = record.method
                if method in method_counts:
                    method_counts[method] += 1

        return {
            "valid": len(all_errors) == 0,
            "errors": all_errors,
            "stats": {
                "total_records": len(records),
                "valid_records": valid_count,
                "invalid_records": len(records) - valid_count,
                "method_distribution": method_counts,
            },
        }

    @classmethod
    def validate_json_file(cls, file_path: str) -> Dict[str, Any]:
        """
        Validates a JSON file containing a list of MetricRecord records.

        Args:
            file_path: Path to the JSON file.

        Returns:
            Validation result dict.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                return {
                    "valid": False,
                    "errors": ["JSON root must be a list of metrics"],
                    "stats": {},
                }

            records = []
            for item in data:
                if all(k in item for k in cls.REQUIRED_FIELDS):
                    try:
                        record = MetricRecord(**item)
                        records.append(record)
                    except TypeError as e:
                        return {
                            "valid": False,
                            "errors": [f"Failed to instantiate MetricRecord: {str(e)}"],
                            "stats": {},
                        }
                else:
                    missing = set(cls.REQUIRED_FIELDS) - set(item.keys())
                    return {
                        "valid": False,
                        "errors": [f"Missing fields in metric record: {missing}"],
                        "stats": {},
                    }

            return cls.validate_metrics_list(records)

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
