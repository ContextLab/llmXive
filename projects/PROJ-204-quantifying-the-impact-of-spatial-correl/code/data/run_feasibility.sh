#!/usr/bin/env bash
set -e
# Run the feasibility check; the script exits 1 if verdict is 'halt'.
python -m code.data.feasibility
# Verify that the report was created.
if [ ! -f "$(python -c 'from llmxive_toolkit import paths; print(paths.data("results","data_feasibility_report.json"))')" ]; then
  echo "Feasibility report not found!" >&2
  exit 1
fi
echo "Feasibility check completed successfully."