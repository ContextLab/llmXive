"""Fail in seconds when a job cannot use the funded (Hugging Face) path.

The full-pipeline acceptance test works in a fresh ``git init`` repository that has
no ``origin``, so the funded ledger must be reachable through
``LLMXIVE_FUNDED_LEDGER_REMOTE`` with credentials git can find on its own. This
script checks that from the same kind of repository, before the long run starts:

1. the funded guard is live (bill-to id, token, anchor and ledger sync all present);
2. git may push to the ledger remote (a dry run; nothing is written).

Only fixed text and exception type names are printed. Messages and git output are
withheld because they can carry a remote URL, the bill-to id or a token.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

PROBE_REF = "refs/llmxive/preflight-probe"


def _git(repo: Path, *args: str) -> int:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False
    ).returncode


def check(repo: Path) -> str | None:
    """``None`` when the funded path is usable from ``repo``, else a reason that is
    safe to print."""
    from llmxive.backends.hf_budget import funded_guard
    from llmxive.model_selection.ledger_transport import funded_ledger_config_from_env

    try:
        guard = funded_guard(repo, now=datetime.now(UTC))
        remote = funded_ledger_config_from_env().remote
    except Exception as exc:
        return f"funded guard unavailable ({type(exc).__name__})"
    if guard.source != "live":
        return f"funded guard is {guard.source}, not live"
    if _git(repo, "push", "--dry-run", remote, f"HEAD:{PROBE_REF}") != 0:
        return "git may not push to the funded ledger remote"
    return None


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        identity = ["-c", "user.name=preflight", "-c", "user.email=preflight@llmxive.local"]
        if _git(repo, "init", "-q") or _git(repo, *identity, "commit", "-q", "--allow-empty", "-m", "probe"):
            print("funded preflight: could not create the probe repository")
            return 1
        reason = check(repo)
    if reason:
        print(f"funded preflight FAILED: {reason}")
        return 1
    print("funded preflight ok: guard live, ledger push allowed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
