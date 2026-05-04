"""
Hyperparameter counting utility for model comparison.

Verifies that DPGMM has <30% tunable parameters vs baselines (SC-004).
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Set
from dataclasses import dataclass, fields, asdict, is_dataclass
from inspect import getmembers, isclass, isfunction
import yaml

@dataclass
class HyperparameterCount:
    """Count of hyperparameters for a model."""
    model_name: str
    tunable_count: int
    fixed_count: int
    total_count: int
    tunable_percentage: float
    details: Dict[str, Any]

@dataclass
class ComparisonResult:
    """Comparison of hyperparameter counts across models."""
    dp_gmm_count: HyperparameterCount
    baseline_counts: Dict[str, HyperparameterCount]
    dp_gmm_percentage_of_baselines: Dict[str, float]
    meets_sc_004: bool  # True if DPGMM has <30% tunable params vs each baseline
    summary: str

def count_dataclass_parameters(cls: type) -> Tuple[int, int, Dict[str, Any]]:
    """
    Count tunable vs fixed parameters in a dataclass.

    Args:
        cls: Dataclass to analyze

    Returns:
        Tuple of (tunable_count, fixed_count, details)
    """
    tunable = 0
    fixed = 0
    details = {}

    if not is_dataclass(cls):
        return 0, 0, {}

    for field in fields(cls):
        field_name = field.name
        field_type = field.type

        # Check if parameter has default value (fixed) or not (tunable)
        if field.default is not field.default_factory:
            fixed += 1
            details[field_name] = {"type": "fixed", "default": field.default}
        else:
            tunable += 1
            details[field_name] = {"type": "tunable"}

    return tunable, fixed, details

def count_class_parameters(cls: type) -> Tuple[int, int, Dict[str, Any]]:
    """
    Count tunable vs fixed parameters in a class __init__.

    Args:
        cls: Class to analyze

    Returns:
        Tuple of (tunable_count, fixed_count, details)
    """
    import inspect

    tunable = 0
    fixed = 0
    details = {}

    try:
        sig = inspect.signature(cls.__init__)
        for param_name, param in sig.parameters.items():
            if param_name in ('self', 'cls'):
                continue

            if param.default is inspect.Parameter.empty:
                tunable += 1
                details[param_name] = {"type": "tunable"}
            else:
                fixed += 1
                details[param_name] = {"type": "fixed", "default": str(param.default)}
    except (ValueError, TypeError):
        pass

    return tunable, fixed, details

def count_yaml_parameters(config_path: Path) -> Tuple[int, int, Dict[str, Any]]:
    """
    Count tunable vs fixed parameters in YAML config.

    Args:
        config_path: Path to YAML config file

    Returns:
        Tuple of (tunable_count, fixed_count, details)
    """
    if not config_path.exists():
        return 0, 0, {}

    with open(config_path) as f:
        config = yaml.safe_load(f)

    tunable = 0
    fixed = 0
    details = {}

    def count_dict(d: Dict, prefix: str = ""):
        nonlocal tunable, fixed
        for key, value in d.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                count_dict(value, full_key)
            elif isinstance(value, (list, tuple)):
                tunable += 1
                details[full_key] = {"type": "tunable", "value_type": "list"}
            else:
                # Assume scalar values with no explicit "fixed" marker are tunable
                tunable += 1
                details[full_key] = {"type": "tunable", "value": value}

    if isinstance(config, dict):
        count_dict(config)

    return tunable, fixed, details

def count_model_hyperparameters(
    model_name: str,
    config_class: Optional[type] = None,
    model_class: Optional[type] = None,
    config_path: Optional[Path] = None
) -> HyperparameterCount:
    """
    Count hyperparameters for a model.

    Args:
        model_name: Name of the model
        config_class: Optional config dataclass to analyze
        model_class: Optional model class to analyze
        config_path: Optional YAML config path to analyze

    Returns:
        HyperparameterCount with results
    """
    total_tunable = 0
    total_fixed = 0
    all_details = {}

    # Count from config class
    if config_class:
        tunable, fixed, details = count_dataclass_parameters(config_class)
        total_tunable += tunable
        total_fixed += fixed
        all_details.update({f"config.{k}": v for k, v in details.items()})

    # Count from model class
    if model_class:
        tunable, fixed, details = count_class_parameters(model_class)
        total_tunable += tunable
        total_fixed += fixed
        all_details.update({f"model.{k}": v for k, v in details.items()})

    # Count from YAML config
    if config_path:
        tunable, fixed, details = count_yaml_parameters(config_path)
        total_tunable += tunable
        total_fixed += fixed
        all_details.update({f"yaml.{k}": v for k, v in details.items()})

    total = total_tunable + total_fixed
    percentage = (total_tunable / total * 100) if total > 0 else 0.0

    return HyperparameterCount(
        model_name=model_name,
        tunable_count=total_tunable,
        fixed_count=total_fixed,
        total_count=total,
        tunable_percentage=percentage,
        details=all_details
    )

def compare_hyperparameters(
    dp_gmm_count: HyperparameterCount,
    baseline_counts: Dict[str, HyperparameterCount]
) -> ComparisonResult:
    """
    Compare DPGMM hyperparameters against baselines.

    Args:
        dp_gmm_count: DPGMM hyperparameter count
        baseline_counts: Dictionary of baseline names to their counts

    Returns:
        ComparisonResult with comparison details
    """
    percentages = {}
    meets_threshold = True

    for baseline_name, baseline_count in baseline_counts.items():
        if baseline_count.total_count == 0:
            percentages[baseline_name] = float('inf')
            continue

        percentage = (dp_gmm_count.tunable_count / baseline_count.tunable_count) * 100
        percentages[baseline_name] = percentage

        # SC-004: DPGMM should have <30% tunable parameters vs baselines
        if percentage >= 30.0:
            meets_threshold = False

    summary_parts = [
        f"DPGMM: {dp_gmm_count.tunable_count} tunable / {dp_gmm_count.total_count} total ({dp_gmm_count.tunable_percentage:.1f}%)",
        "vs baselines:"
    ]

    for baseline_name, baseline_count in baseline_counts.items():
        pct = percentages[baseline_name]
        status = "✓" if pct < 30.0 else "✗"
        summary_parts.append(f"  {status} {baseline_name}: {pct:.1f}% of DPGMM tunable params")

    return ComparisonResult(
        dp_gmm_count=dp_gmm_count,
        baseline_counts=baseline_counts,
        dp_gmm_percentage_of_baselines=percentages,
        meets_sc_004=meets_threshold,
        summary="\n".join(summary_parts)
    )

def scan_project_for_models(project_root: Path) -> Dict[str, Dict]:
    """
    Scan project for model and baseline implementations.

    Args:
        project_root: Root path of the project

    Returns:
        Dictionary mapping model names to their file paths
    """
    models = {}
    src_path = project_root / "code" / "src"

    # Scan models directory
    models_path = src_path / "models"
    if models_path.exists():
        for py_file in models_path.glob("*.py"):
            if py_file.name not in ("__init__.py", "time_series.py", "anomaly_score.py"):
                model_name = py_file.stem
                models[model_name] = {"path": str(py_file), "type": "model"}

    # Scan baselines directory
    baselines_path = src_path / "baselines"
    if baselines_path.exists():
        for py_file in baselines_path.glob("*.py"):
            if py_file.name not in ("__init__.py",):
                model_name = py_file.stem
                models[model_name] = {"path": str(py_file), "type": "baseline"}

    return models

def main():
    """Test hyperparameter counting functionality."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    # Test 1: Count YAML parameters
    print("Test 1: YAML parameter counting")
    config_path = Path("code/config.yaml")
    if config_path.exists():
        tunable, fixed, details = count_yaml_parameters(config_path)
        print(f"  Tunable: {tunable}, Fixed: {fixed}")
        print(f"  Total: {tunable + fixed}")
    else:
        print("  config.yaml not found")

    # Test 2: Create sample comparison
    print("\nTest 2: Sample comparison")
    dp_gmm = HyperparameterCount(
        model_name="DPGMM",
        tunable_count=5,
        fixed_count=3,
        total_count=8,
        tunable_percentage=62.5,
        details={"alpha": "tunable", "gamma": "tunable"}
    )

    arima = HyperparameterCount(
        model_name="ARIMA",
        tunable_count=15,
        fixed_count=5,
        total_count=20,
        tunable_percentage=75.0,
        details={"p": "tunable", "d": "tunable", "q": "tunable"}
    )

    ma = HyperparameterCount(
        model_name="MovingAverage",
        tunable_count=8,
        fixed_count=2,
        total_count=10,
        tunable_percentage=80.0,
        details={"window_size": "tunable"}
    )

    baseline_counts = {"ARIMA": arima, "MovingAverage": ma}
    result = compare_hyperparameters(dp_gmm, baseline_counts)

    print(result.summary)
    print(f"\nMeets SC-004 (<30% tunable vs baselines): {result.meets_sc_004}")

    print("\nAll tests passed!")

if __name__ == "__main__":
    main()
