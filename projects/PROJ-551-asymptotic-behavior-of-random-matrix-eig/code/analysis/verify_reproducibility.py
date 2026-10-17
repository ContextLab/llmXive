"""
Task T003: confirm reproducibility of the single-run analysis.

Loads data/processed/single_run_results.json, re-runs the exact same
computation (same seed, same parameters, same ARPACK settings) from the
raw matrix on disk, and asserts that the top eigenvalue matches the
stored value within 1e-6. Also re-checks the theoretical outlier rule
and JSON well-formedness. Writes the outcome to
data/logs/reproducibility_check.txt.
"""

import json
import sys
from pathlib import Path

import numpy as np

from llmxive_toolkit import paths as llm_paths

# Make the project's `code` package importable regardless of cwd.
ROOT = llm_paths.root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from code.main import (  # noqa: E402
    _compute_top_eigenvalues,
    _create_diagonal_perturbation,
    _is_outlier,
)


def main() -> int:
    processed = llm_paths.data("processed")
    logs_dir = llm_paths.data("logs")
    raw_dir = llm_paths.data("raw")

    json_path = processed / "single_run_results.json"
    if not json_path.is_file():
        print(f"FAIL: {json_path} not found; run code.main first.")
        return 1

    with open(json_path, "r", encoding="utf-8") as f:
        record = json.load(f)

    N = int(record["N"])
    seed = int(record["seed"])
    theta = float(record["theta"])
    stored_top = float(record["eigenvalues"][0]["value"])

    matrix_path = raw_dir / f"matrix_N{N}_seed{seed}.npy"
    if not matrix_path.is_file():
        print(f"FAIL: raw matrix {matrix_path} not found.")
        return 1

    matrix = np.load(matrix_path)
    perturbed = matrix + _create_diagonal_perturbation(N, theta)
    recomputed_top = float(_compute_top_eigenvalues(perturbed, k=10)[0])

    delta = abs(recomputed_top - stored_top)
    outlier_ok = _is_outlier(recomputed_top) == bool(record["eigenvalues"][0]["is_outlier"])

    lines = [
        f"Reproducibility check (T003): N={N}, seed={seed}, theta={theta}",
        f"stored top eigenvalue     = {stored_top!r}",
        f"recomputed top eigenvalue = {recomputed_top!r}",
        f"absolute difference       = {delta:.3e}",
    ]
    ok = delta <= 1e-6 and outlier_ok
    if delta <= 1e-6:
        lines.append("Sanity check Delta <= 1e-6: PASS")
    else:
        lines.append("Sanity check Delta <= 1e-6: FAIL")
    lines.append(f"outlier flag consistent with theoretical rule: {'PASS' if outlier_ok else 'FAIL'}")
    lines.append(f"OVERALL: {'PASS' if ok else 'FAIL'}")

    report = logs_dir / "reproducibility_check.txt"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"Report written to {report}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())