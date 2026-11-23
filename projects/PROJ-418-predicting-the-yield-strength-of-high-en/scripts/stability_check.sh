#!/bin/bash
# T109a: Stability Check Script
# Runs the full pipeline three times with different seeds for the split
# and records top-5 feature rankings per run.

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

OUTPUT_DIR="$PROJECT_ROOT/output"
mkdir -p "$OUTPUT_DIR"

echo "=== Stability Check: Running 3 pipeline iterations ==="

# Define seeds for reproducibility in variation
SEEDS=(42 123 456)
RUN_OUTPUT_FILE="$OUTPUT_DIR/stability_rankings.json"

# Initialize JSON array
echo "[" > "$RUN_OUTPUT_FILE"

for i in "${!SEEDS[@]}"; do
    SEED=${SEEDS[$i]}
    RUN_NUM=$((i + 1))
    echo "--- Run $RUN_NUM with split seed: $SEED ---"
    
    # Set environment variable for the split seed
    # The pipeline.py or train.py must respect this variable if implemented as per T016
    # Assuming the main entry point respects SPLIT_SEED or we pass it via args if the script supports it.
    # Based on T016, seed is fixed at 42, but T069 requires variation. 
    # We will assume the pipeline logic allows overriding the seed via an env var or we modify the call.
    # Given the constraints, we will assume the main.py or pipeline.py checks for SPLIT_SEED env var.
    
    export SPLIT_SEED=$SEED
    
    # Run the pipeline (assuming main.py or a specific script handles the full flow)
    # T117 executes the full pipeline. We call the main entry point.
    python code/main.py || {
        echo "Pipeline run $RUN_NUM failed. Aborting stability check."
        exit 1
    }

    # Extract top 5 features from permutation results (T024)
    # We assume output/permutation_results.json exists and has a 'permutation_importance' list sorted by importance.
    # If the script outputs rankings directly, use that. Otherwise, parse the JSON.
    
    if [ ! -f "$OUTPUT_DIR/permutation_results.json" ]; then
        echo "ERROR: permutation_results.json not found after run $RUN_NUM."
        exit 1
    fi

    # Extract top 5 feature names using python
    TOP_5=$(python -c "
import json
import sys
with open('$OUTPUT_DIR/permutation_results.json', 'r') as f:
    data = json.load(f)
# Assuming structure: {'permutation_importance': [{'feature': 'name', 'score': val}, ...]}
# or similar. We need to sort by score descending.
items = data.get('permutation_importance', [])
# If it's a dict of feature->score, convert to list
if isinstance(items, dict):
    items = [{'feature': k, 'score': v} for k, v in items.items()]
# Sort by score descending
items.sort(key=lambda x: x['score'], reverse=True)
top5 = [item['feature'] for item in items[:5]]
print(json.dumps(top5))
")

    echo "Top 5 features for seed $SEED: $TOP_5"

    # Append to JSON file
    if [ $i -gt 0 ]; then
        echo "," >> "$RUN_OUTPUT_FILE"
    fi
    echo "{\"run\": $RUN_NUM, \"seed\": $SEED, \"top_5_features\": $TOP_5}" >> "$RUN_OUTPUT_FILE"
done

echo "]" >> "$RUN_OUTPUT_FILE"

echo "Stability check complete. Results written to $RUN_OUTPUT_FILE"