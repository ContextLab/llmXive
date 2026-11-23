"""
Standalone verification runner for the T002 simulation generator
unit tests (tests/unit/test_generator.py).

Executes every ``test_*`` function in the test module directly,
without requiring pytest to be installed, so the T002 verification
criterion (injected tau^2 matches the empirical between-study
variance within 0.05, with deterministic seeding) can be checked
in any environment. Exits non-zero on the first failure.
"""
import importlib.util
import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
TEST_FILE = PROJECT_ROOT / "tests" / "unit" / "test_generator.py"

for p in (str(CODE_DIR), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

def main() -> int:
    if not TEST_FILE.exists():
        print(f"ERROR: test file not found: {TEST_FILE}")
        return 1

    spec = importlib.util.spec_from_file_location("test_generator", TEST_FILE)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        traceback.print_exc()
        print("ERROR: could not import tests/unit/test_generator.py")
        return 1

    test_names = sorted(
        n for n in dir(module) if n.startswith("test_") and callable(getattr(module, n))
    )
    if not test_names:
        print("ERROR: no test functions found in test_generator.py")
        return 1

    failures = []
    for name in test_names:
        print(f"RUN  {name} ...", end=" ", flush=True)
        try:
            getattr(module, name)()
            print("PASS")
        except Exception:
            print("FAIL")
            traceback.print_exc()
            failures.append(name)

    print("=" * 60)
    print(f"{len(test_names) - len(failures)}/{len(test_names)} tests passed.")
    if failures:
        print("FAILED TESTS: " + ", ".join(failures))
        return 1
    print("T002 VERIFICATION PASSED: all generator unit tests pass.")
    return 0

if __name__ == "__main__":
    sys.exit(main())