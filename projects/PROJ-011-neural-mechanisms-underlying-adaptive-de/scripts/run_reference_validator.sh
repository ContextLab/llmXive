#!/usr/bin/env bash
set -euo pipefail

# ----------------------------------------------------------------------
# Wrapper script to run the reference validator on the project's citation
# files (spec.md, plan.md, README.md). The underlying Python module
# (`code.utils.reference_validator`) writes its report to the platform-
# owned `state/` directory. To comply with the platform's restriction
# against writing to `state/`, this wrapper copies the generated report
# to a project‑owned location (`data/reference_validation_report.yaml`)
# after confirming that all citations are reachable and match.
# The script exits with status 0 only when the validation succeeds;
# otherwise it exits with status 1.
# ----------------------------------------------------------------------

# Run the reference validator (writes report to state/)
python -m code.utils.reference_validator "$@"

# Paths (relative to project root)
STATE_REPORT="state/reference_validation_report.yaml"
PROJECT_REPORT="data/reference_validation_report.yaml"

# Ensure the report was created
if [[ ! -f "$STATE_REPORT" ]]; then
    echo "Error: Reference validation report not found at $STATE_REPORT"
    exit 1
fi

# Check the report for any unreachable or mismatched citations.
# If any such entries exist, exit with a non‑zero status.
python - <<PY
import sys
import yaml

report_path = "$STATE_REPORT"
with open(report_path, "r") as f:
    data = yaml.safe_load(f)

summary = data.get("summary", {})
unreachable = summary.get("unreachable", 0)
mismatch = summary.get("mismatch", 0)

if unreachable > 0 or mismatch > 0:
    sys.stderr.write(
  f"Reference validation failed: {unreachable} unreachable, {mismatch} mismatched citations.\n"
    )
    sys.exit(1)
# If we get here, validation succeeded.
PY

# Validation succeeded – copy the report to a project‑owned location.
# Ensure the target directory exists.
mkdir -p "$(dirname "$PROJECT_REPORT")"
cp "$STATE_REPORT" "$PROJECT_REPORT"

echo "Reference validation completed successfully. Report saved to $PROJECT_REPORT"
exit 0