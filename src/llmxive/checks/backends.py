"""Backend reachability pre-check (T114).

For each backend in the agent registry, attempts a cheap probe:
  - dartmouth: ChatDartmouth.list() — confirms key validity + service health
  - local: import transformers — confirms the dep is installed

Exits 1 if any required backend fails. The "required" set is just
`dartmouth` (the default for most agents); local is an advisory
fallback (its failure is a soft warning).
"""

from __future__ import annotations

import os
import sys
import time

from llmxive.agents import registry as registry_loader
from llmxive.backends import router as backend_router
from llmxive.backends.base import BackendError
from llmxive.config import repo_root as _repo_root

# A single transient blip from a provider's models endpoint (a momentary non-JSON
# response, a 5xx, a reset) must NOT fail the whole real-call gate — that brittleness
# repeatedly sank PR CI even when the backend was healthy. Retry the probe a few
# times with backoff; a GENUINE sustained outage still fails fast (within ~6s).
_PROBE_ATTEMPTS = 3
_PROBE_BASE_DELAY_S = 2.0


def _probe_models(backend: object) -> tuple[list[object] | None, Exception | None]:
    """Call ``backend.list_models()`` with bounded retry. Returns (models, last_error)."""
    last: Exception | None = None
    for attempt in range(_PROBE_ATTEMPTS):
        try:
            return list(backend.list_models()), None  # type: ignore[attr-defined]
        except Exception as exc:  # transient (BackendError, JSON decode, network)
            last = exc
            if attempt < _PROBE_ATTEMPTS - 1:
                time.sleep(_PROBE_BASE_DELAY_S * (attempt + 1))
    return None, last


def main() -> int:
    repo = _repo_root()
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
        except BackendError as exc:
            (failures if name == "dartmouth" else warnings).append(
                f"{name} unreachable: {exc}"
            )
            continue

        models, err = _probe_models(backend)
        if err is not None:
            msg = f"{name} unreachable after {_PROBE_ATTEMPTS} attempts: {err}"
            (failures if name == "dartmouth" else warnings).append(msg)
            continue
        if not models:
            warnings.append(f"{name}: list_models() returned empty list")
            continue
        print(f"backends-check: {name} OK ({len(models)} models reachable)")

    for w in warnings:
        print(f"backends-check: WARN: {w}", file=sys.stderr)
    if failures:
        for line in failures:
            print(f"backends-check: FAIL: {line}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
