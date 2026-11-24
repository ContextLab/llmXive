#!/usr/bin/env bash
set -e

# ------------------------------------------------------------
# Helper: print usage information
# ------------------------------------------------------------
function usage() {
  cat <<EOF
Usage: $0 [--stage data|model|viz|full] [--help]

Stages:
  data   - Run the data loading pipeline (code/data_loader.py)
  model  - Run the model training pipeline (code/model_training.py)
  viz    - Run the visualization pipeline (code/visualization.py)
  full   - Run the full end‑to‑end pipeline (code/main.py)

Options:
  --help - Show this help message and exit
EOF
  exit 0
}

# ------------------------------------------------------------
# Parse arguments
# ------------------------------------------------------------
if [[ "$1" == "--help" ]] || [[ -z "$1" ]]; then
  usage
fi

if [[ "$1" != "--stage" ]]; then
  echo "Error: First argument must be '--stage'"
  usage
fi

STAGE="$2"

# ------------------------------------------------------------
# Function: run a Python module and record feasibility metrics
# ------------------------------------------------------------
function run_and_monitor() {
  local module_path="$1"
  local stage_name="$2"

  python - <<PY
import importlib
import time
import json
import pathlib
import psutil

start = time.time()

# Dynamically import the target module and execute its main entry point
module = importlib.import_module("$module_path")
if hasattr(module, "main"):
    module.main()
else:
    raise AttributeError(f"Module '{module_path}' has no 'main' function")

elapsed = time.time() - start
peak_gb = psutil.Process().memory_info().rss / (1024 ** 3)

metrics = {
    "stage": "$stage_name",
    "elapsed_seconds": elapsed,
    "peak_memory_gb": peak_gb
}

out_path = pathlib.Path("data/outputs") / f"{stage_name}_metrics.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(metrics, indent=2))
PY
}

# ------------------------------------------------------------
# Dispatch based on requested stage
# ------------------------------------------------------------
case "$STAGE" in
  data)
    run_and_monitor "code.data_loader" "data"
    ;;
  model)
    run_and_monitor "code.model_training" "model"
    ;;
  viz)
    run_and_monitor "code.visualization" "viz"
    ;;
  full)
    # The full pipeline is orchestrated by code.main.run_pipeline()
    python - <<PY
import time
import json
import pathlib
import psutil
import importlib

start = time.time()
main_mod = importlib.import_module("code.main")
if hasattr(main_mod, "run_pipeline"):
    main_mod.run_pipeline()
else:
    raise AttributeError("code.main has no 'run_pipeline' function")
elapsed = time.time() - start
peak_gb = psutil.Process().memory_info().rss / (1024 ** 3)

metrics = {
    "stage": "full",
    "elapsed_seconds": elapsed,
    "peak_memory_gb": peak_gb
}
out_path = pathlib.Path("data/outputs") / "full_metrics.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(metrics, indent=2))
PY
    ;;
  *)
    echo "Error: Unknown stage '$STAGE'"
    usage
    ;;
esac