#!/bin/bash
# Run the full llmXive pipeline on a small subset to verify end-to-end flow.
# This script executes: generate_trajectories.py -> simulate_agent.py -> analyze_results.py -> visualize_results.py
# It stops on any failure and logs exit codes.

set -e  # Exit immediately if a command exits with a non-zero status

# Project root relative to script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

# Change to project root
cd "$PROJECT_ROOT"

echo "=== llmXive Pipeline Execution ==="
echo "Working directory: $(pwd)"
echo "Date: $(date)"
echo ""

# Helper function to run a step
run_step() {
    local step_name="$1"
    local script_path="$2"
    local args="$3"
    
    echo "--- Running $step_name ---"
    echo "Command: python $script_path $args"
    
    if python "$script_path" $args; then
        echo "✓ $step_name completed successfully."
        echo ""
    else
        echo "✗ ERROR: $step_name failed with exit code $?"
        echo "Pipeline execution halted."
        exit 1
    fi
}

# 1. Generate Trajectories (Small Subset: 50 for speed)
# Output: data/raw/trajectories.json
run_step "Trajectory Generation" \
    "code/generate_trajectories.py" \
    "--output data/raw/trajectories.json --count 50 --seed 42"

# 2. Simulate Agent
# Input: data/raw/trajectories.json
# Output: data/processed/simulation_results.csv
run_step "Agent Simulation" \
    "code/simulate_agent.py" \
    "--input data/raw/trajectories.json --output data/processed/simulation_results.csv --batch-size 10 --seed 42"

# 3. Analyze Results
# Input: data/processed/simulation_results.csv
# Output: output/regression_summary.json, output/hypothesis_summary.md
run_step "Statistical Analysis" \
    "code/analyze_results.py" \
    "--input data/processed/simulation_results.csv --output-dir output"

# 4. Visualize Results
# Input: output/regression_summary.json
# Output: output/plots/regime_map.png
run_step "Visualization" \
    "code/visualize_results.py" \
    "--input output/regression_summary.json --output output/plots/regime_map.png"

echo "=== Pipeline Execution Complete ==="
echo "Generated artifacts:"
echo "  - data/raw/trajectories.json"
echo "  - data/processed/simulation_results.csv"
echo "  - output/regression_summary.json"
echo "  - output/hypothesis_summary.md"
echo "  - output/plots/regime_map.png"
echo ""
echo "All steps passed. End-to-end verification successful."
