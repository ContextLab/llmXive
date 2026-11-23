"""T051b: Run Resource Usage Audit.

Executes the smoke test (code/scripts/run_smoke_test.py, from T050a/T050b)
as a subprocess while measuring the peak Resident Set Size (RSS) of all
child processes via ``resource.getrusage(RUSAGE_CHILDREN)``. The audit
result (peak RSS, duration, pass/fail against the 6 GB budget with a
safety margin below the 7 GB runner limit) is written to
``results/memory_profile.log``.

Usage:
    python scripts/run_memory_audit.py
"""

import os
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
LOG_FILE = RESULTS_DIR / "memory_profile.log"
SMOKE_TEST = ROOT / "code" / "scripts" / "run_smoke_test.py"

# Budget: peak RSS must remain below 6 GB (safety margin under the 7 GB
# GitHub Actions runner limit), per task T051b.
MEMORY_BUDGET_GB = 6.0


def main() -> int:
    if not SMOKE_TEST.is_file():
        print(f"ERROR: smoke test script not found at {SMOKE_TEST}", file=sys.stderr)
        return 1

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env.setdefault("SEED", "42")

    start = time.time()
    proc = subprocess.run(
        [sys.executable, str(SMOKE_TEST)],
        cwd=str(ROOT),
        env=env,
    )
    duration_s = time.time() - start

    # ru_maxrss is in KiB on Linux.
    peak_rss_kib = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    peak_rss_mb = peak_rss_kib / 1024.0
    peak_rss_gb = peak_rss_mb / 1024.0

    within_budget = peak_rss_gb < MEMORY_BUDGET_GB

    lines = [
        "Resource Usage Audit (T051b)",
        "============================",
        f"Command: python {SMOKE_TEST}",
        f"Smoke test exit code: {proc.returncode}",
        f"Wall-clock duration: {duration_s:.1f} s",
        f"Peak RSS (all child processes): {peak_rss_mb:.1f} MB "
        f"({peak_rss_gb:.3f} GB)",
        f"Memory budget: {MEMORY_BUDGET_GB:.1f} GB "
        "(safety margin below the 7 GB runner limit)",
        f"RESULT: {'PASS' if within_budget else 'FAIL'} — peak RSS "
        f"{'is below' if within_budget else 'EXCEEDS'} the 6 GB budget.",
    ]

    if proc.returncode != 0:
        lines.append(
            "RESULT: FAIL — smoke test itself failed; audit is inconclusive."
        )

    LOG_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nAudit log written to {LOG_FILE}")

    if proc.returncode != 0:
        return proc.returncode
    return 0 if within_budget else 1


if __name__ == "__main__":
    sys.exit(main())