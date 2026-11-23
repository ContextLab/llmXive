#!/bin/bash
set -e

echo "Starting llmXive pipeline execution..."
echo "ENABLE_DOCKER flag: ${ENABLE_DOCKER:-true}"

# If ENABLE_DOCKER is explicitly set to "false", "0", "no", or "off", skip execution
if [[ "${ENABLE_DOCKER}" == "false" || "${ENABLE_DOCKER}" == "0" || "${ENABLE_DOCKER}" == "no" || "${ENABLE_DOCKER}" == "off" ]]; then
    echo "ENABLE_DOCKER is false. Skipping pipeline execution as per configuration."
    exit 0
fi

# Check if a specific script is provided as an argument, otherwise default to main.py
if [ -n "$1" ]; then
    EXEC_SCRIPT="$1"
else
    EXEC_SCRIPT="python code/main.py"
fi

echo "Executing: $EXEC_SCRIPT"
eval $EXEC_SCRIPT

if [ $? -eq 0 ]; then
    echo "Pipeline completed successfully."
else
    echo "Pipeline execution failed."
    exit 1
fi
