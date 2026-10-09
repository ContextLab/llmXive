"""Explicit CI tick publication using the existing research commit boundary."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from llmxive.checks.pipeline_writes import unexpected_writes


class TickCheckpoint:
    """Publish completed ticks; never run concurrently with an artifact writer.

    This cannot preserve a graph step interrupted before it returns. The caller
    owns one pass budget and must stop when publication fails or platform inputs
    change during rebase. No alternate output profile or shell command is accepted.
    """

    def __init__(self, repo: Path):
        self.repo = repo.resolve()

    def persist(self, project_id: str, tick: int) -> int:
        """Return 0 to continue, 1 on failure, 2 after a platform-changing rebase."""
        try:
            top = self._git("rev-parse", "--show-toplevel").strip()
            if Path(top).resolve() != self.repo:
                raise RuntimeError("checkpoint repository must be the Git worktree root")
            # Validate with already-imported trusted code BEFORE executing the
            # repository script: an agent must not publish via an altered guard.
            bad = unexpected_writes(self.repo, profile="research")
            if bad:
                raise RuntimeError("writes outside research output roots: " + ", ".join(bad))
            before = self._git("rev-parse", "HEAD").strip()
            subprocess.run(
                ["bash", str(self.repo / "scripts/ci/commit-and-push.sh"),
                 f"advance({project_id}): checkpoint tick {tick}", "research"],
                cwd=self.repo, check=True,
            )
            # A successful concurrent rebase can update code/config/templates on
            # disk while this Python process still holds older imported modules.
            # Stop conservatively for any change outside generated output trees.
            changed = self._git("diff", "--name-only", "--no-renames", "-z", before, "HEAD")
            platform = [p for p in changed.split("\0") if p and not p.startswith(
                ("projects/", "state/", "web/data/", "docs/")
            )]
            if platform:
                print("[checkpoint] published; platform changed during rebase; "
                      "stopping pass: " + ", ".join(platform), flush=True)
                return 2
            print(f"[checkpoint] durable tick {tick} for {project_id}", flush=True)
            return 0
        except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
            print(f"[checkpoint] publication failed; stopping pass: {exc}",
                  file=sys.stderr, flush=True)
            return 1

    def _git(self, *args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=self.repo).decode()
