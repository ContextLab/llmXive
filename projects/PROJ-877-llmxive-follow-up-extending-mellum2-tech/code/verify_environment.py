"""
Environment verification for T001a.

Runs the task's two stated verification checks and writes the evidence
to ``data/results/environment_check.json``:

1. ``import code.config`` succeeds (the module defines SEED=12345 and a
   primary frozen model identifier).
2. Every package pinned in ``code/requirements.txt`` is importable in
   the active environment (evidence that the pinned environment is
   installed and functional).

The script fails loudly (non-zero exit) if ``code.config`` cannot be
imported or does not define the required constants. Missing optional
pipeline packages are recorded honestly per-package in the report.
"""
import importlib
import json
import sys
from datetime import datetime, timezone

from llmxive_toolkit import paths

# Packages pinned in code/requirements.txt that must be importable.
PINNED_PACKAGES = [
    "datasets",
    "transformers",
    "tree_sitter",
    "tree_sitter_python",
    "tree_sitter_java",
    "sklearn",
    "statsmodels",
    "pandas",
    "numpy",
    "scipy",
    "matplotlib",
    "seaborn",
    "kenlm",
    "ruptures",
    "pwlf",
    "jsonschema",
    "pytest",
    "psutil",
]

def main() -> int:
    report: dict = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
    }

    # --- Check 1: import code.config ---------------------------------
    try:
        import code.config as cfg  # noqa: F401  (import itself is the check)
    except Exception as exc:  # pragma: no cover - loud failure path
        report["config_import"] = {"ok": False, "error": repr(exc)}
        _write(report)
        print(f"FAILED: import code.config raised {exc!r}", file=sys.stderr)
        return 1

    from code.config import SEED, PRIMARY_MODEL_ID, PRIMARY_MODEL_HF_ID

    config_ok = SEED == 12345 and PRIMARY_MODEL_ID in ("Mistral-7B", "Llama-3-8B")
    report["config_import"] = {
        "ok": config_ok,
        "SEED": SEED,
        "PRIMARY_MODEL_ID": PRIMARY_MODEL_ID,
        "PRIMARY_MODEL_HF_ID": PRIMARY_MODEL_HF_ID,
    }
    if not config_ok:
        _write(report)
        print("FAILED: code.config constants are invalid", file=sys.stderr)
        return 1

    # --- Check 2: pinned packages are importable ---------------------
    packages = {}
    all_ok = True
    for pkg in PINNED_PACKAGES:
        try:
            mod = importlib.import_module(pkg)
            version = getattr(mod, "__version__", "unknown")
            packages[pkg] = {"ok": True, "version": str(version)}
        except Exception as exc:
            all_ok = False
            packages[pkg] = {"ok": False, "error": repr(exc)}

    report["pinned_packages"] = packages
    report["all_pinned_packages_importable"] = all_ok
    _write(report)

    print(f"config import OK (SEED={SEED}, model={PRIMARY_MODEL_ID})")
    print(f"pinned packages importable: {all_ok}")
    out = paths.data("results", "environment_check.json")
    print(f"evidence written to {out}")
    return 0 if all_ok else 2

def _write(report: dict) -> None:
    out = paths.data("results", "environment_check.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

if __name__ == "__main__":
    sys.exit(main())