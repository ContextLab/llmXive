#!/usr/bin/env bash
#
# verify_stability.sh
#
# Executes the stability verification script and exits with status 0 if the
# stability criterion (rank‑difference ≤ 1 across the three runs) is satisfied,
# otherwise exits with a non‑zero status.
#
set -euo pipefail

# Path to the JSON file produced by the stability assessment script
STABILITY_JSON="output/stability_rankings.json"

if [[ ! -f "${STABILITY_JSON}" ]]; then
    echo "Error: Stability rankings file '${STABILITY_JSON}' not found." >&2
    exit 1
fi

# Run the Python helper that performs the actual verification.
python - <<PYTHON
import json
import sys
from pathlib import Path

stability_path = Path("${STABILITY_JSON}")

if not stability_path.is_file():
    print(f"Error: File {stability_path} does not exist.", file=sys.stderr)
    sys.exit(1)

try:
    data = json.load(stability_path.open())
except json.JSONDecodeError as e:
    print(f"Error: Failed to parse JSON – {e}", file=sys.stderr)
    sys.exit(1)

# Normalise the JSON structure.
# Expected formats:
#   1. {"run1": {"featureA": 1, "featureB": 2, ...}, "run2": {...}, "run3": {...}}
#   2. {"run1": ["featureA", "featureB", ...], "run2": [...], "run3": [...]}
#   3. A list of runs: [{"featureA": 1, ...}, {...}, {...}]
# The script extracts a mapping of feature -> list of ranks across runs.

ranks_per_feature = {}

def register_rank(feature: str, rank: int):
    ranks_per_feature.setdefault(feature, []).append(rank)

if isinstance(data, dict):
    # Dict of runs
    for run_key, run_val in data.items():
  if isinstance(run_val, dict):
      for feat, rank in run_val.items():
          if isinstance(rank, (int, float)):
              register_rank(feat, int(rank))
  elif isinstance(run_val, list):
      for idx, feat in enumerate(run_val):
          register_rank(str(feat), idx + 1)
elif isinstance(data, list):
    # List of runs
    for run_val in data:
  if isinstance(run_val, dict):
      for feat, rank in run_val.items():
          if isinstance(rank, (int, float)):
              register_rank(feat, int(rank))
  elif isinstance(run_val, list):
      for idx, feat in enumerate(run_val):
          register_rank(str(feat), idx + 1)

# Verify the stability criterion: for every feature present in at least two runs,
# the maximum rank difference must be ≤ 1.
failed = False
for feat, ranks in ranks_per_feature.items():
    if len(ranks) < 2:
  continue  # Not enough information to assess stability for this feature
    diff = max(ranks) - min(ranks)
    if diff > 1:
  print(f"Feature '{feat}' rank difference {diff} exceeds allowed maximum of 1.", file=sys.stderr)
  failed = True

if failed:
    sys.exit(1)
else:
    print("Stability criterion satisfied: all rank differences ≤ 1.")
    sys.exit(0)
PYTHON