"""Backend reachability pre-check (T114).

For each backend in the agent registry, attempts a cheap probe:
  - dartmouth: the chat catalog — confirms key validity + service health
  - huggingface: the router catalog (keyless)
  - local: its model inventory — confirms the dep is installed

A remote provider (dartmouth, huggingface) is probed only when its credential is
configured, by the same rule preflight uses (``preflight.PROVIDER_CONFIGURED``:
the Dartmouth key, or HF_TOKEN plus LLMXIVE_HF_BILL_TO). Exits 1 only when NO
remote provider is both configured and reachable; a provider that is down or not
configured while another one is usable is reported as info. ``local`` is an
advisory fallback (its failure is a soft warning).
"""

from __future__ import annotations

import sys
import time

from llmxive.agents import registry as registry_loader
from llmxive.backends import router as backend_router
from llmxive.backends.base import BackendError
from llmxive.config import repo_root as _repo_root
from llmxive.preflight import PROVIDER_CONFIGURED

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

    usable: list[str] = []  # remote providers configured AND reachable
    down: list[str] = []  # remote providers not configured or not reachable
    warnings: list[str] = []
    for backend_entry in reg.backends:
        name = backend_entry.name.value
        remote = name in PROVIDER_CONFIGURED
        if remote:
            configured, problems = PROVIDER_CONFIGURED[name]()
            if not configured:
                down.append(f"{name}: not configured ({'; '.join(problems) or 'credential unset'})")
                continue

        try:
            backend = backend_router.make_backend(name)
        except BackendError as exc:
            (down if remote else warnings).append(f"{name} unreachable: {exc}")
            continue

        models, err = _probe_models(backend)
        if err is not None:
            msg = f"{name} unreachable after {_PROBE_ATTEMPTS} attempts: {err}"
            (down if remote else warnings).append(msg)
            continue
        if not models:
            (down if remote else warnings).append(f"{name}: list_models() returned empty list")
            continue
        print(f"backends-check: {name} OK ({len(models)} models reachable)")
        if remote:
            usable.append(name)

    for w in warnings:
        print(f"backends-check: WARN: {w}", file=sys.stderr)
    if not usable:
        print("backends-check: FAIL: no usable model provider", file=sys.stderr)
        for line in down:
            print(f"backends-check: FAIL: {line}", file=sys.stderr)
        return 1
    for line in down:
        print(f"backends-check: INFO: {line}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
