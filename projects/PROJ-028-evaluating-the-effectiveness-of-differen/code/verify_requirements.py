"""Verify the Python 3.11 project initialization for T002.

Checks that requirements.txt exists at the project root and contains
all required dependencies (transformers, torch[cpu], datasets, scipy,
pytest, psutil), and that the interpreter is Python 3.11+.
Writes a verification report to data/logs/requirements_check.json.
"""
import json
import sys

from llmxive_toolkit import paths

REQUIRED = {
    "transformers": "transformers",
    "torch": "torch",
    "datasets": "datasets",
    "scipy": "scipy",
    "pytest": "pytest",
    "psutil": "psutil",
}

def main() -> int:
    req_path = paths.root / "requirements.txt"
    if not req_path.exists():
        raise FileNotFoundError(f"requirements.txt not found at {req_path}")

    text = req_path.read_text(encoding="utf-8")
    lines = [
        ln.strip()
        for ln in text.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]

    missing = []
    for req_name, token in REQUIRED.items():
        found = any(
            token in ln.split(">=")[0].split("==")[0].split("<")[0].strip()
            for ln in lines
        )
        if not found:
            missing.append(req_name)

    torch_cpu = any(ln.startswith("torch[cpu]") for ln in lines)
    py_ok = sys.version_info >= (3, 11)

    report = {
        "python_version": sys.version.split()[0],
        "python_3_11_or_newer": py_ok,
        "requirements_file": str(req_path),
        "requirement_lines": lines,
        "missing_dependencies": missing,
        "torch_cpu_extra_specified": torch_cpu,
        "all_dependencies_present": len(missing) == 0,
    }

    out = paths.data("logs", "requirements_check.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

    if missing:
        raise SystemExit(
            f"FAILED: missing dependencies in requirements.txt: {missing}"
        )
    if not torch_cpu:
        raise SystemExit("FAILED: torch[cpu] extra not specified")
    if not py_ok:
        raise SystemExit(
            f"FAILED: Python >= 3.11 required, found {sys.version.split()[0]}"
        )
    print("T002 verification PASSED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())