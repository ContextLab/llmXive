#!/usr/bin/env bash
set -e

# Resolve the path to the quickstart log file using the Python toolkit
LOG_FILE=$(python - <<'PY'
from llmxive_toolkit import paths
print(paths.logs("quickstart.log"))
PY
)
mkdir -p "$(dirname "$LOG_FILE")"

# Redirect all stdout/stderr to the log file
exec >"$LOG_FILE" 2>&1

echo "=== Quickstart: starting at $(date) ==="

# ----------------------------------------------------------------------
# 1. Create a virtual environment
# ----------------------------------------------------------------------
echo "Creating virtual environment..."
python -m venv .venv
source .venv/bin/activate

# ----------------------------------------------------------------------
# 2. Install pinned dependencies
# ----------------------------------------------------------------------
echo "Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# ----------------------------------------------------------------------
# 3. Pull required Docker images
# ----------------------------------------------------------------------
echo "Pulling Docker images..."
docker pull returntocorp/semgrep:1.46.0
docker pull sonarqube:9.9-community

# ----------------------------------------------------------------------
# 4. Run the orchestrator script
# ----------------------------------------------------------------------
echo "Running the research pipeline..."
python -m src.run_pipeline --seed 42 --max-pairs 300

echo "=== Quickstart completed successfully at $(date) ==="