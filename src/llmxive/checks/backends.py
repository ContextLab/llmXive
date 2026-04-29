"""Backend reachability pre-check (T114).

For each backend in the agent registry, attempts a cheap probe:
  - dartmouth: ChatDartmouth.list() — confirms key validity + service health
  - huggingface: list_models() — static whitelist; success requires HF_TOKEN
  - local: import transformers — confirms the dep is installed

Exits 1 if any required backend fails. The "required" set is just
`dartmouth` (the default for most agents); HF and local are advisory
fallbacks (their failure is a soft warning).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from llmxive.agents import registry as registry_loader
from llmxive.backends import router as backend_router
from llmxive.backends.base import BackendError


def main() -> int:
    repo = Path(__file__).resolve().parent.parent.parent.parent
    try:
        reg = registry_loader.load(repo_root=repo)
    except Exception as exc:
        print(f"backends-check: registry load failed: {exc}", file=sys.stderr)
        return 1

    failures: list[str] = []
    warnings: list[str] = []
    for backend_entry in reg.backends:
        name = backend_entry.name.value
        # Skip backends whose required env vars aren't set (treat as
        # advisory, since CI may run without HF_TOKEN on forks).
        missing_env = [v for v in backend_entry.auth_env_vars if not os.environ.get(v)]
        if missing_env and name != "local":
            warnings.append(
                f"{name}: skipping probe — env vars not set: {missing_env}"
            )
            continue

        try:
            backend = backend_router.make_backend(name)
            models = backend.list_models()
            if not models:
                warnings.append(f"{name}: list_models() returned empty list")
                continue
            print(f"backends-check: {name} OK ({len(models)} models reachable)")
        except BackendError as exc:
            if name == "dartmouth":
                failures.append(f"{name} unreachable: {exc}")
            else:
                warnings.append(f"{name} unreachable: {exc}")

    for w in warnings:
        print(f"backends-check: WARN: {w}", file=sys.stderr)
    if failures:
        for line in failures:
            print(f"backends-check: FAIL: {line}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
