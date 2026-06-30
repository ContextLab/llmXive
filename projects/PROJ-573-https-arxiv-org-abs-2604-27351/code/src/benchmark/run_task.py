import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


def load_task_definition(task_id: Any) -> Optional[Dict[str, Any]]:
    """
    Load a single task definition from ``src/tasks/task_definitions.yaml``.

    The function accepts either the raw identifier (e.g., ``3``) or the
    full string identifier (e.g., ``\"T003\"``).  Numeric identifiers are
    automatically zero‑padded to three digits to match the convention used
    throughout the project.

    Parameters
    ----------
    task_id : Any
        The identifier of the task to load.  Can be ``int`` or ``str``.

    Returns
    -------
    dict | None
        The task definition dictionary if found, otherwise ``None``.
    """
    task_defs_path = Path(__file__).parents[2] / "tasks" / "task_definitions.yaml"
    if not task_defs_path.is_file():
        logger.error(f"Task definitions file not found at {task_defs_path}")
        return None

    with task_defs_path.open("r", encoding="utf-8") as f:
        try:
            all_tasks = yaml.safe_load(f) or []
        except yaml.YAMLError as exc:
            logger.error(f"Failed to parse task definitions YAML: {exc}")
            return None

    # Normalise the incoming id to the canonical ``T###`` format
    if isinstance(task_id, int):
        canonical_id = f"T{task_id:03d}"
    elif isinstance(task_id, str):
        canonical_id = task_id.strip()
        if not canonical_id.upper().startswith("T"):
            # Allow callers to pass a plain number as a string
            try:
                num = int(canonical_id)
                canonical_id = f"T{num:03d}"
            except ValueError:
                logger.error(f"Invalid task_id format: {task_id}")
                return None
    else:
        logger.error(f"Unsupported task_id type: {type(task_id)}")
        return None

    # ``all_tasks`` may be a list of dicts or a dict keyed by id.
    if isinstance(all_tasks, dict):
        task = all_tasks.get(canonical_id)
        if task:
            logger.debug(f"Found task definition for {canonical_id}")
        return task
    elif isinstance(all_tasks, list):
        for task in all_tasks:
            if task.get("task_id") == canonical_id:
                logger.debug(f"Found task definition for {canonical_id}")
                return task
    logger.warning(f"Task definition not found for ID: {canonical_id}")
    return None


def load_modality_configs() -> Dict[str, Dict[str, Any]]:
    """
    Load all modality configuration YAML files located under
    ``src/benchmark/config/modalities/``.

    Returns
    -------
    dict
        Mapping from modality name (filename without extension) to the
        configuration dictionary.
    """
    config_dir = Path(__file__).parents[2] / "benchmark" / "config" / "modalities"
    configs: Dict[str, Dict[str, Any]] = {}
    if not config_dir.is_dir():
        logger.error(f"Modality config directory not found: {config_dir}")
        return configs

    for yaml_path in config_dir.glob("*.yaml"):
        modality_name = yaml_path.stem  # filename without .yaml
        with yaml_path.open("r", encoding="utf-8") as f:
            try:
                cfg = yaml.safe_load(f) or {}
                configs[modality_name] = cfg
            except yaml.YAMLError as exc:
                logger.error(f"Failed to parse {yaml_path}: {exc}")
    logger.debug(f"Loaded modality configs: {list(configs.keys())}")
    return configs


def _simulate_prediction(modality: str, data: Any) -> Any:
    """
    Placeholder prediction logic for a given modality.

    In a full implementation this would invoke the appropriate model
    wrapper (e.g., ``TimeSeriesModel``, ``TabularModel`` or ``TextModel``).
    For the purposes of the benchmark runner we return a deterministic
    dummy value that makes the output JSON well‑formed.
    """
    # Deterministic dummy: hash of modality name + length of data (if iterable)
    try:
        length = len(data) if hasattr(data, "__len__") else 0
    except Exception:
        length = 0
    dummy_score = (hash(modality) % 1000) / 1000.0 + (length % 10) * 0.01
    return round(dummy_score, 4)


def execute_task(
    task_def: Dict[str, Any],
    modality_configs: Dict[str, Dict[str, Any]],
    add_modality: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute a single benchmark task.

    Parameters
    ----------
    task_def : dict
        The task definition loaded from ``task_definitions.yaml``.
    modality_configs : dict
        Mapping of modality name to its configuration.
    add_modality : str | None
        Optional extra modality to inject into the task (e.g., ``image``).

    Returns
    -------
    dict
        JSON‑serialisable result containing:
        - ``prediction``: aggregate dummy prediction (float)
        - ``modality_contributions``: mapping modality → dummy prediction
        - ``timing_seconds``: execution time (float)
    """
    start_time = time.time()

    # Gather the list of modalities for this task
    task_modalities: List[str] = task_def.get("modalities", [])
    if add_modality:
        task_modalities.append(add_modality)

    contributions: Dict[str, Any] = {}
    for modality in task_modalities:
        cfg = modality_configs.get(modality)
        if cfg is None:
            # Missing modality configuration – log and continue with a placeholder
            logger.warning(
                f"Missing configuration for modality '{modality}'. "
                "Using placeholder contribution."
            )
            contributions[modality] = None
            continue

        # In a real system we would load the actual input data here.
        # For the benchmark runner we pass a simple placeholder.
        placeholder_input = {"modality": modality, "config": cfg}
        pred = _simulate_prediction(modality, placeholder_input)
        contributions[modality] = pred

    # Simple aggregation: mean of available numeric contributions
    numeric_vals = [
        v for v in contributions.values() if isinstance(v, (int, float))
    ]
    aggregate_prediction = (
        sum(numeric_vals) / len(numeric_vals) if numeric_vals else None
    )

    elapsed = time.time() - start_time
    result = {
        "task_id": task_def.get("task_id"),
        "prediction": aggregate_prediction,
        "modality_contributions": contributions,
        "timing_seconds": round(elapsed, 4),
    }
    logger.info(
        f"Executed task {task_def.get('task_id')} in {elapsed:.4f}s "
        f"with prediction {aggregate_prediction}"
    )
    return result


def main() -> None:
    """
    Command‑line entry point for ``run_task.py``.

    Example usage:
        python src/benchmark/run_task.py --task-id 3 --add-modality image
    """
    parser = argparse.ArgumentParser(
        description="Execute a single benchmark task."
    )
    parser.add_argument(
        "--task-id",
        required=True,
        help="Identifier of the task to run (e.g., 3 or T003).",
    )
    parser.add_argument(
        "--add-modality",
        required=False,
        help="Optional extra modality to inject into the task.",
    )
    args = parser.parse_args()

    # Load definitions and configurations
    task = load_task_definition(args.task_id)
    if task is None:
        error_payload = {
            "error": f"Task definition not found for ID: {args.task_id}",
            "status": "failed",
        }
        print(json.dumps(error_payload, indent=2))
        sys.exit(1)

    modality_cfgs = load_modality_configs()

    # Execute the task
    result = execute_task(task, modality_cfgs, add_modality=args.add_modality)

    # Output the result as pretty‑printed JSON
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    # Initialise a basic logger configuration for direct execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    main()