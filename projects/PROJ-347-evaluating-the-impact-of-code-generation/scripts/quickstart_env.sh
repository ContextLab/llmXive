#!/usr/bin/env bash
#
# Quickstart environment sanity check.
# Creates a reproducible virtual environment, installs pinned dependencies,
# pulls required Docker images, and verifies that the environment is functional.
# All output (including timestamps) is written to logs/quickstart_env.log.
#
set -euo pipefail

# ----------------------------------------------------------------------
# Helper to write timestamped messages to both stdout and the log file.
# ----------------------------------------------------------------------
LOG_PATH="logs/quickstart_env.log"
mkdir -p "$(dirname "$LOG_PATH")"

log() {
  local msg="$1"
  echo "$(date +"%Y-%m-%d %H:%M:%S") $msg" | tee -a "$LOG_PATH"
}

log "=== Starting quickstart environment setup ==="

# ----------------------------------------------------------------------
# 1. Create (or reuse) a virtual environment in the project root.
# ----------------------------------------------------------------------
if [ ! -d ".venv" ]; then
  log "Creating virtual environment at .venv"
  python -m venv .venv
else
  log "Virtual environment .venv already exists – reusing it"
fi

# ----------------------------------------------------------------------
# 2. Activate the virtual environment.
# ----------------------------------------------------------------------
# shellcheck source=/dev/null
source .venv/bin/activate
log "Activated virtual environment"

# ----------------------------------------------------------------------
# 3. Verify Python installation.
# ----------------------------------------------------------------------
log "Python version:"
python --version | tee -a "$LOG_PATH"

# ----------------------------------------------------------------------
# 4. Upgrade pip (ensures we have the latest installer that respects
#    the pinned versions in requirements.txt).
# ----------------------------------------------------------------------
log "Upgrading pip"
pip install --upgrade pip >> "$LOG_PATH" 2>&1

# ----------------------------------------------------------------------
# 5. Install exact pinned dependencies.
# ----------------------------------------------------------------------
log "Installing dependencies from requirements.txt"
pip install -r requirements.txt >> "$LOG_PATH" 2>&1

# ----------------------------------------------------------------------
# 6. Verify Docker installation.
# ----------------------------------------------------------------------
log "Docker version:"
docker version >> "$LOG_PATH" 2>&1

# ----------------------------------------------------------------------
# 7. Pull required Docker images (Semgrep, SonarQube Community, CodeQL).
# ----------------------------------------------------------------------
declare -a images=(
  "returntocorp/semgrep:1.46.0"
  "sonarqube:9.9-community"
  "ghcr.io/github/codeql-action:latest"
)

for img in "${images[@]}"; do
  log "Pulling Docker image $img"
  docker pull "$img" >> "$LOG_PATH" 2>&1
done

log "=== Quickstart environment setup completed successfully ==="
exit 0
