"""
Execution harness for Task T002 verification.

Runs every ``test_*`` function in ``tests/unit/test_generator.py``
directly (no pytest required) and writes the pass/fail evidence to
``data/results/generator_verification.json``. Exits non-zero if any
test fails, so the pipeline fails loudly.

Usage:
    python code/scripts/verify_generator.py
"""
import importlib.util
import json
import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
TEST_FILE = PROJECT_ROOT / "tests" / "unit" / "test_generator.py"
OUTPUT_FILE = PROJECT_ROOT / "data" / "results" / "generator_verification.json"

def main() -> int:
    if str(CODE_DIR) not in sys.path:
        sys.path.insert(0, str(CODE_DIR))

    spec = importlib.util.spec_from_file_location("test_generator_module", TEST_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    test_names = sorted(
        name for name in dir(module)
        if name.startswith("test_") and callable(getattr(module, name))
    )
    if not test_names:
        print(f"No test functions found in {TEST_FILE}", file=sys.stderr)
        return 1

    results = {}
    all_passed = True
    for name in test_names:
        try:
            getattr(module, name)()
            results[name] = {"status": "passed"}
            print(f"PASSED {name}")
        except Exception as exc:  # noqa: BLE001 - record any failure
            all_passed = False
            results[name] = {
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            }
            print(f"FAILED {name}: {exc}", file=sys.stderr)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "task_id": "T002",
        "test_file": str(TEST_FILE.relative_to(PROJECT_ROOT)),
        "n_tests": len(test_names),
        "n_passed": sum(1 for r in results.values() if r["status"] == "passed"),
        "all_passed": all_passed,
        "tests": results,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Verification evidence written to {OUTPUT_FILE}")
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
