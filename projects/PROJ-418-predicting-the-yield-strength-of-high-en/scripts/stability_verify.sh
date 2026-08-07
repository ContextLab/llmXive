#!/bin/bash
# T109b: Stability Verifier Script
# Reads output/stability_rankings.json and asserts rank-difference <= 1 across runs.

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

INPUT_FILE="$PROJECT_ROOT/output/stability_rankings.json"

if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: $INPUT_FILE not found. Run stability_check.sh first."
    exit 1
fi

echo "=== Verifying Stability Criterion (Rank Difference <= 1) ==="

# Use Python to perform the verification logic
python - << 'PYTHON_SCRIPT'
import json
import sys
import os

input_file = os.environ.get('INPUT_FILE', 'output/stability_rankings.json')

try:
    with open(input_file, 'r') as f:
  data = json.load(f)
except Exception as e:
    print(f"ERROR: Failed to load {input_file}: {e}")
    sys.exit(1)

if not isinstance(data, list) or len(data) < 2:
    print("ERROR: stability_rankings.json must contain at least 2 runs.")
    sys.exit(1)

# Extract the top-5 lists
runs = [entry.get('top_5_features', []) for entry in data]

if any(len(r) != 5 for r in runs):
    print("ERROR: Each run must have exactly 5 top features.")
    sys.exit(1)

# Check rank difference for each feature position
max_diff = 0
failed = False

for i in range(5):
    # Get the feature at rank i for all runs
    features_at_rank_i = [r[i] for r in runs]
    
    # If the feature is the same across all runs, diff is 0
    if len(set(features_at_rank_i)) == 1:
  continue
    
    # If features differ, we need to check if the rank difference is <= 1
    # This implies that if a feature is at rank i in run A, it should be at rank i-1, i, or i+1 in run B.
    # However, the spec says "rank-difference <= 1 across runs".
    # Interpretation: For every feature in the top 5 of any run, its position in other runs must be within +/- 1.
    # Let's check pairwise consistency for the top 5.
    
    # Simpler interpretation for "rank-difference <= 1":
    # The set of top 5 features should be largely consistent.
    # Let's check if the feature at rank i in run 0 appears in rank i-1, i, or i+1 in run 1, etc.
    
    base_feature = features_at_rank_i[0]
    for j in range(1, len(runs)):
  # Find rank of base_feature in run j
  try:
      rank_in_j = runs[j].index(base_feature)
  except ValueError:
      rank_in_j = -1 # Not found in top 5
  
  if rank_in_j == -1:
      # Feature not in top 5, diff is large (>= 5) -> Fail
      print(f"FAIL: Feature '{base_feature}' at rank {i} in run 0 is not in top 5 of run {j}.")
      failed = True
  elif abs(rank_in_j - i) > 1:
      print(f"FAIL: Feature '{base_feature}' at rank {i} in run 0 is at rank {rank_in_j} in run {j}. Diff > 1.")
      failed = True

if failed:
    print("Stability criterion FAILED: Rank difference > 1 detected.")
    sys.exit(1)
else:
    print("Stability criterion PASSED: Rank difference <= 1 across all runs.")
    sys.exit(0)
PYTHON_SCRIPT

exit $?