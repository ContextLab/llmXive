"""Prompt-existence pre-check (T114).

Iterates every entry in agents/registry.yaml and asserts:
  1. The `prompt_path` file exists.
  2. The file is non-empty.
  3. The file parses as valid Markdown (heuristic: starts with `#`).

Exits 1 with a one-line-per-failure message on any violation.
"""

from __future__ import annotations

import sys
from pathlib import Path

from llmxive.agents import registry as registry_loader


def main() -> int:
    repo = Path(__file__).resolve().parent.parent.parent.parent
    failures: list[str] = []
    try:
        reg = registry_loader.load(repo_root=repo)
    except Exception as exc:
        print(f"prompts-check: registry load failed: {exc}", file=sys.stderr)
        return 1

    for agent in reg.agents:
        prompt_path = repo / agent.prompt_path
        if not prompt_path.exists():
            failures.append(f"agent {agent.name!r}: prompt missing at {agent.prompt_path}")
            continue
        try:
            text = prompt_path.read_text(encoding="utf-8")
        except OSError as exc:
            failures.append(f"agent {agent.name!r}: prompt unreadable: {exc}")
            continue
        if not text.strip():
            failures.append(f"agent {agent.name!r}: prompt is empty")
            continue
        if not text.lstrip().startswith("#"):
            failures.append(
                f"agent {agent.name!r}: prompt missing top-level heading "
                f"(expected first non-blank line to start with '#')"
            )

    if failures:
        for line in failures:
            print(f"prompts-check: FAIL: {line}", file=sys.stderr)
        return 1
    print(f"prompts-check: OK ({len(reg.agents)} agents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
