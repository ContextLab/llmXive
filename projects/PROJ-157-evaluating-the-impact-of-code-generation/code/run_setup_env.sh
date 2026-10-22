#!/usr/bin/env bash
set -euo pipefail
# Execute the deterministic environment setup script.
python "$(dirname "$0")/../setup_env.py"
# Verify that the expected output file exists.
if [[ ! -f "$(python -c 'from llmxive_toolkit import paths; print(paths.data("env_config.json"))')" ]]; then
  echo "ERROR: data/env_config.json was not created." >&2
  exit 1
fi
echo "Environment setup completed successfully."