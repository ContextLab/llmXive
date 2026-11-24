"""Verify the project Python environment.

Checks that every dependency declared in ``requirements.txt`` is
importable in the current interpreter and records the installed
versions plus interpreter metadata to
``results/environment_report.json``.  Exits non-zero if any required
package fails to import, so a broken environment is discovered
loudly instead of silently (T002).
"""

import importlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
REPORT_PATH = PROJECT_ROOT / "results" / "environment_report.json"

# Import-name overrides for packages whose distribution name differs
# from its import name.
IMPORT_NAME = {
    "scikit-learn": "sklearn",
    "pyyaml": "yaml",
    "numpyro": "numpyro",
}

REQUIRED = [
    "numpy",
    "pandas",
    "numpyro",
    "jax",
    "networkx",
    "scikit-learn",
    "pyyaml",
    "jsonschema",
    "pytest",
]


def parse_requirements(path: Path):
    """Yield (distribution, pinned_version) pairs from requirements.txt."""
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        if "==" in line:
            name, _, version = line.partition("==")
            yield name.strip(), version.strip()
        else:
            yield line.strip(), None


def main() -> int:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": sys.platform,
        "packages": {},
        "failures": [],
    }

    for dist, pinned in parse_requirements(REQUIREMENTS):
        mod_name = IMPORT_NAME.get(dist, dist.replace("-", "_"))
        try:
            mod = importlib.import_module(mod_name)
            version = getattr(mod, "__version__", "unknown")
            report["packages"][dist] = {
                "import_name": mod_name,
                "installed_version": version,
                "pinned_version": pinned,
            }
        except Exception as exc:  # noqa: BLE001 - report every failure
            report["failures"].append(
                {"distribution": dist, "error": f"{type(exc).__name__}: {exc}"}
            )

    # Explicit numpyro smoke check: the previously failing import
    # (jax.experimental.pjit.pjit_p) must now succeed.
    try:
        import numpyro

        numpyro.distributions.Bernoulli(0.5)
        report["numpyro_smoke_test"] = "passed"
    except Exception as exc:  # noqa: BLE001
        report["numpyro_smoke_test"] = f"failed: {exc}"
        report["failures"].append(
            {"distribution": "numpyro", "error": f"smoke test failed: {exc}"}
        )

    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(f"Environment report written to {REPORT_PATH}")

    if report["failures"]:
        for failure in report["failures"]:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("All required dependencies import successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
