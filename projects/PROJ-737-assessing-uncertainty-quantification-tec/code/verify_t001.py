"""T001 verification: skeleton directories, data contract, and SC-005 check."""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/results",
    "figures",
    "code/models",
    "code/metrics",
    "code/stats",
    "code/utils",
    "tests/unit",
    "tests/integration",
]

SCHEMA_PATH = ROOT / "specs" / "001-assessing-uncertainty-quantification-tec" / "contracts" / "per_sample_errors.schema.yaml"
SPEC_PATH = ROOT / "specs" / "001-assessing-uncertainty-quantification-tec" / "spec.md"

EXPECTED_COLUMNS = [
    "sample_id",
    "dataset",
    "method",
    "prediction",
    "lower_bound",
    "upper_bound",
    "ground_truth",
    "abs_error",
]

def main() -> int:
    failures = []

    # 1. Directory skeleton
    for d in REQUIRED_DIRS:
        p = ROOT / d
        p.mkdir(parents=True, exist_ok=True)
        if not p.is_dir():
            failures.append(f"directory missing: {d}")

    # 2. Data contract schema
    if not SCHEMA_PATH.is_file():
        failures.append(f"schema file missing: {SCHEMA_PATH}")
    else:
        with open(SCHEMA_PATH) as fh:
            schema = yaml.safe_load(fh)
        cols = [c["name"] for c in schema.get("columns", [])]
        if cols != EXPECTED_COLUMNS:
            failures.append(
                f"schema columns mismatch: {cols} != {EXPECTED_COLUMNS}"
            )
        for c in schema.get("columns", []):
            if not c.get("name") or not c.get("dtype"):
                failures.append(f"incomplete column entry: {c}")

    # 3. SC-005 dataset coverage in spec.md
    spec_text = SPEC_PATH.read_text()
    for ds in ["Band Gap", "Thermal Conductivity", "Formation Energy"]:
        if ds not in spec_text:
            failures.append(f"SC-005 dataset not listed in spec.md: {ds}")

    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        return 1
    print("T001 verification passed: directories, schema, and SC-005 all OK.")
    return 0

if __name__ == "__main__":
    sys.exit(main())