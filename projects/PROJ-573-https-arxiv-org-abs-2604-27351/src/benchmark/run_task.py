"""
run_task.py
--------------

Command-line utility to execute a single benchmark task.

Usage:
    python src/benchmark/run_task.py --task-id <TASK_ID> [--add-modality <MODALITY>]

The script:
    1. Loads the task definition from ``src/tasks/task_definitions.yaml``.
    2. Loads modality configuration files from ``src/benchmark/config/modalities``.
    3. Optionally adds an extra modality configuration (if ``--add-modality`` is supplied).
    4. Executes a very lightweight placeholder task (the real model logic lives in the
       ``src/models`` package).  For the purpose of the benchmark infrastructure we only
       need to return a JSON document containing:
           * ``prediction`` – a dummy string that identifies the task.
           * ``modality_contributions`` – a list of modality names that participated.
           * ``timing`` – elapsed time in seconds.
    5. Prints the JSON document to STDOUT and also writes it to ``data/run_task_<TASK_ID>.json``.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import yaml

logger = logging.getLogger(__name__)


def load_task_definition(task_id: str, definitions_path: Path = Path("src/tasks/task_definitions.yaml")) -> Dict[str, Any]:
    """
    Load a single task definition from the central ``task_definitions.yaml`` file.

    Parameters
    ----------
    task_id: str
        Identifier of the task (e.g., ``T001``).
    definitions_path: Path
        Path to the YAML file containing all task definitions.

    Returns
    -------
    dict
        The task definition dictionary.

    Raises
    ------
    FileNotFoundError
        If ``definitions_path`` does not exist.
    KeyError
        If the requested ``task_id`` is not present in the file.
    """
    if not definitions_path.is_file():
        raise FileNotFoundError(f"Task definitions file not found at {definitions_path}")

    with definitions_path.open("r", encoding="utf-8") as f:
        all_tasks = yaml.safe_load(f) or {}

    # The file is expected to contain a list of task dicts under a top‑level key ``tasks``
    tasks_list = all_tasks.get("tasks", [])
    for task in tasks_list:
        if str(task.get("task_id")) == str(task_id):
            logger.debug("Loaded task definition for %s", task_id)
            return task

    raise KeyError(f"Task definition not found for ID: {task_id}")


def load_modality_configs(
    modalities: List[str],
    config_dir: Path = Path("src/benchmark/config/modalities"),
) -> Dict[str, Dict[str, Any]]:
    """
    Load YAML configuration files for each modality required by a task.

    Parameters
    ----------
    modalities: List[str]
        List of modality identifiers (e.g., ``["timeseries", "tabular"]``).
    config_dir: Path
        Directory that holds the per‑modality configuration files.

    Returns
    -------
    dict
        Mapping from modality name to its configuration dictionary.
    """
    configs: Dict[str, Dict[str, Any]] = {}
    for modality in modalities:
        cfg_path = config_dir / f"{modality}.yaml"
        if not cfg_path.is_file():
            logger.warning("Modality config %s not found – skipping.", cfg_path)
            continue
        with cfg_path.open("r", encoding="utf-8") as f:
            configs[modality] = yaml.safe_load(f) or {}
        logger.debug("Loaded modality config for %s", modality)
    return configs


def execute_task(
    task_def: Dict[str, Any],
    modality_configs: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Execute a *placeholder* task.

    The real benchmark would route inputs through the appropriate model wrappers.
    For the infrastructure test we only need deterministic, lightweight behaviour.

    Returns
    -------
    dict
        JSON‑serialisable result containing ``prediction``, ``modality_contributions`` and ``timing``.
    """
    start = time.time()
    task_id = task_def.get("task_id", "UNKNOWN")
    # In a full implementation we would instantiate the ModalityRouter here.
    # For now we simply echo back the modalities that were loaded.
    contributions = list(modality_configs.keys())

    # Dummy prediction – in practice this would be the model output.
    prediction = f"dummy_prediction_for_{task_id}"

    elapsed = time.time() - start
    result = {
        "task_id": task_id,
        "prediction": prediction,
        "modality_contributions": contributions,
        "timing_seconds": elapsed,
    }
    logger.info("Executed task %s in %.3f seconds", task_id, elapsed)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute a single benchmark task.")
    parser.add_argument(
        "--task-id",
        required=True,
        help="Identifier of the task to run (e.g., T001).",
    )
    parser.add_argument(
        "--add-modality",
        help="Optional extra modality to load (e.g., image).",
    )
    args = parser.parse_args()

    try:
        task_def = load_task_definition(args.task_id)
    except (FileNotFoundError, KeyError) as exc:
        error_payload = {"status": "failed", "error": str(exc)}
        print(json.dumps(error_payload, indent=2))
        sys.exit(1)

    # Determine which modalities are required for this task.
    required_modalities = task_def.get("modalities", [])
    if args.add_modality:
        required_modalities.append(args.add_modality)

    modality_cfgs = load_modality_configs(required_modalities)

    result = execute_task(task_def, modality_cfgs)

    # Write result to a predictable location for downstream scripts / tests.
    output_path = Path("data") / f"run_task_{args.task_id}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    # Also print to STDOUT for CLI friendliness.
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    # Ensure a basic logger configuration if the host application hasn't set one up.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main()
