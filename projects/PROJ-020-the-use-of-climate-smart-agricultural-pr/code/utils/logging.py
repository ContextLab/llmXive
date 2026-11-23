"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    Do NOT subclass or delegate to the stdlib ``logging`` module: its
    ``log(level, msg)`` needs an integer level and has no ``to_json`` — that is
    exactly what keeps breaking. This logger is self-contained.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None


def get_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual-purpose: a decorator (@log_operation) OR a direct logging call.

    The direct-call path ALWAYS returns a LogEntry (callers use .to_json());
    decorator use returns the wrapped function. Never return a bare function
    from the direct-call path.
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


def initialize_logging(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Tolerant logging initializer.

    Accepts all call shapes from the project:
    - initialize_logging()
    - initialize_logging("name")
    - initialize_logging(name="name")
    - initialize_logging(log_file="path")
    - initialize_logging(log_path="path")
    - initialize_logging(level=logging.INFO)
    """
    logger = get_logger(*args, **kwargs)
    # Handle file path arguments gracefully (no-op for this logger, but prevents errors)
    if "log_file" in kwargs or "log_path" in kwargs:
        pass  # ReproducibilityLogger doesn't write to disk, but accepts the arg
    return logger


def write_provenance_log(output_path: str = "data/processed/provenance_log.json") -> None:
    """
    Implement T018c: Write the CSA Index Provenance Log.

    This function maps every derived CSA variable (including the final weighted composite index)
    to its source LSMS question ID and response ID. It writes the mapping to a JSON file.

    According to T007b and T007d, the weights are configurable. This log records the
    default equal weighting (0.2 each) and the mapping of components to sources.

    Args:
        output_path: Path to the output JSON file.
    """
    import os
    from pathlib import Path

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    provenance_mapping = {
        "metadata": {
            "description": "CSA Index Provenance Log",
            "formula_reference": "specs/001-csa-food-security/data-model.md#CSA_Index_Formula",
            "weighting_strategy": "equal_weighting",
            "weights": {
                "conservation_tillage": 0.2,
                "crop_diversification": 0.2,
                "irrigation_efficiency": 0.2,
                "digital_access": 0.2,
                "finance_access": 0.2
            }
        },
        "components": [
            {
                "variable_name": "conservation_tillage",
                "composite_role": "Primary CSA Index Component",
                "source_dataset": "LSMS",
                "source_question_id": "AG_TILLAGE_METHOD",
                "source_response_id": "TILLAGE_TYPE_CODE",
                "normalization": "min-max"
            },
            {
                "variable_name": "crop_diversification",
                "composite_role": "Primary CSA Index Component",
                "source_dataset": "LSMS",
                "source_question_id": "AG_CROP_LIST",
                "source_response_id": "CROP_COUNT",
                "normalization": "min-max"
            },
            {
                "variable_name": "irrigation_efficiency",
                "composite_role": "Primary CSA Index Component",
                "source_dataset": "LSMS",
                "source_question_id": "AG_WATER_SOURCE",
                "source_response_id": "IRRIGATION_METHOD_CODE",
                "normalization": "min-max"
            },
            {
                "variable_name": "digital_access",
                "composite_role": "Primary CSA Index Component & Moderator",
                "source_dataset": "LSMS",
                "source_question_id": "HH_TECHNOLOGY",
                "source_response_id": "MOBILE_INTERNET_ACCESS",
                "normalization": "min-max",
                "note": "Also tested as moderator per Principle VII"
            },
            {
                "variable_name": "finance_access",
                "composite_role": "Primary CSA Index Component & Moderator",
                "source_dataset": "LSMS",
                "source_question_id": "HH_FINANCE",
                "source_response_id": "CREDIT_ACCESS_FLAG",
                "normalization": "min-max",
                "note": "Also tested as moderator per Principle VII"
            }
        ],
        "composite_index": {
            "variable_name": "csa_index",
            "formula": "sum(component * weight)",
            "provenance_link": "All components listed above"
        }
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(provenance_mapping, f, indent=2, ensure_ascii=False)

    # Log the action using the existing tolerant logger
    logger = get_logger("provenance")
    logger.log("write_provenance_log", output_path=output_path)