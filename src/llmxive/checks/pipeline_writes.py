"""Reject pipeline writes outside the canonical output roots before a cron commit."""

import subprocess
from pathlib import Path

ALLOWED_ROOTS = ("projects/", "state/", "web/data/")


def unexpected_writes(repo: Path) -> list[str]:
    # NUL records handle spaces/newlines. Check tracked and untracked paths;
    # no shell interpolation and no mutation of the index or working tree.
    changed = (
        subprocess.check_output(
            ["git", "diff", "HEAD", "--name-only", "-z"],
            cwd=repo,
        )
        .decode()
        .split("\0")
    )
    untracked = (
        subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard", "-z"],
            cwd=repo,
        )
        .decode()
        .split("\0")
    )
    return sorted({p for p in changed + untracked if p and not p.startswith(ALLOWED_ROOTS)})


def main() -> int:
    bad = unexpected_writes(Path.cwd())
    if bad:
        print("Refusing pipeline commit: writes outside projects/, state/, web/data/:")
        print("\n".join(bad))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
