"""Validate (and optionally stage) the fixed output profile of a cron workflow."""

import argparse
import subprocess
from pathlib import Path

if __package__:
    from .repository_layout import is_project_path
else:  # cron runs this file directly, without requiring an installed package
    from repository_layout import is_project_path

# Explicit workflow profiles, not arbitrary caller-supplied path allowlists.
# Pages builds a static docs mirror; it does not execute generated research.
OUTPUT_ROOTS = {
    "research": ("projects", "state", "web/data"),
    "pages": ("docs",),
}


def unexpected_writes(repo: Path, *, profile: str = "research") -> list[str]:
    roots = OUTPUT_ROOTS[profile]
    changed = []
    # Check the index and working tree separately: an unsafe staged change must
    # not be hidden by restoring only its working-tree copy. Disable rename
    # detection so a protected deletion cannot hide behind an allowed target.
    for args in (
        ["diff", "--cached", "--name-only", "--no-renames", "-z"],
        ["diff", "--name-only", "--no-renames", "-z"],
        ["ls-files", "--others", "--exclude-standard", "-z"],
    ):
        changed.extend(subprocess.check_output(["git", *args], cwd=repo).decode().split("\0"))

    def allowed(path: str) -> bool:
        if path.startswith("projects/"):
            return profile == "research" and is_project_path(path)
        return path.startswith(tuple(root + "/" for root in roots if root != "projects"))

    return sorted({path for path in changed if path and not allowed(path)})


def stage_outputs(repo: Path, *, profile: str) -> None:
    """Stage the validated profile roots, including completely deleted roots."""
    for root in OUTPUT_ROOTS[profile]:
        tracked = subprocess.check_output(["git", "ls-files", "-z", "--", root], cwd=repo)
        if (repo / root).is_dir() or tracked:
            subprocess.run(["git", "add", "-A", "--", root], cwd=repo, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=tuple(OUTPUT_ROOTS), default="research")
    parser.add_argument("--stage", action="store_true", help="stage validated output roots")
    args = parser.parse_args()
    repo = Path.cwd()
    bad = unexpected_writes(repo, profile=args.profile)
    if bad:
        print(f"Refusing {args.profile} pipeline commit: writes outside its output roots:")
        print("\n".join(bad))
        return 1
    if args.stage:
        stage_outputs(repo, profile=args.profile)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
