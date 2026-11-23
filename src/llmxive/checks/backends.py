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

``--read-only-gate`` answers a narrower question for CI jobs that run pull-request
code (they cannot push the funded ledger): is a FREE hosted provider (Dartmouth)
configured and reachable? It writes ``usable=true|false`` to ``$GITHUB_OUTPUT`` and
exits 0 either way, so such a job can skip its model steps cleanly during an outage;
a registry load failure or an unexpected error still exits 1.
"""

from __future__ import annotations

import os
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


def _check_backend(name: str) -> tuple[int | None, str, str]:
    """Probe one registry backend by the shared rule: a remote provider must first be
    configured (``PROVIDER_CONFIGURED``), then answer its model catalog.

    Returns ``(model count, "", "")`` when usable, else ``(None, detail, kind)`` where
    ``detail`` is the full message and ``kind`` is safe to print anywhere (a fixed
    phrase or an exception TYPE name, never exception text)."""
    if name in PROVIDER_CONFIGURED:
        configured, problems = PROVIDER_CONFIGURED[name]()
        if not configured:
            return None, f"{name}: not configured ({'; '.join(problems) or 'credential unset'})", "not configured"
    try:
        backend = backend_router.make_backend(name)
    except BackendError as exc:
        return None, f"{name} unreachable: {exc}", type(exc).__name__
    models, err = _probe_models(backend)
    if err is not None:
        return None, f"{name} unreachable after {_PROBE_ATTEMPTS} attempts: {err}", type(err).__name__
    if not models:
        return None, f"{name}: list_models() returned empty list", "empty model list"
    return len(models), "", ""


#: Providers a READ-ONLY run (pull-request code: no push to the funded ledger) can
#: call: the free hosted ones. Hugging Face is funded — a call needs a hold pushed to
#: the ledger first, so it fails closed in such a run and does not count here.
READ_ONLY_PROVIDERS = ("dartmouth",)


def read_only_gate() -> int:
    """``--read-only-gate``: can a run that cannot write the funded ledger call a model?

    Writes ``usable=true|false`` to ``$GITHUB_OUTPUT`` (when set), prints one line
    saying which and why, and exits 0 either way. A registry load failure or any
    unexpected error exits 1: a broken checkout must not look like an outage."""
    try:
        reg = registry_loader.load(repo_root=_repo_root())
    except Exception as exc:
        print(f"backends-check: registry load failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    try:
        registered = {entry.name.value for entry in reg.backends}
        usable: list[str] = []
        reasons: list[str] = []
        for name in READ_ONLY_PROVIDERS:
            if name not in registered:
                reasons.append(f"{name}: not in the registry")
                continue
            count, _detail, kind = _check_backend(name)
            if count is None:
                reasons.append(f"{name}: {kind}")
            else:
                usable.append(name)
        ok = bool(usable)
        out = os.environ.get("GITHUB_OUTPUT")
        if out:
            with open(out, "a", encoding="utf-8") as fh:
                fh.write(f"usable={'true' if ok else 'false'}\n")
    except Exception as exc:
        print(f"backends-check: read-only gate failed unexpectedly: {type(exc).__name__}", file=sys.stderr)
        return 1
    if ok:
        print(f"backends-check: read-only gate: usable=true ({', '.join(usable)} reachable)")
    else:
        print(
            f"backends-check: read-only gate: usable=false ({'; '.join(reasons)}; "
            "huggingface not counted: a read-only run cannot reserve on the funded ledger)"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = argv or []
    if args == ["--read-only-gate"]:
        return read_only_gate()
    if args:
        print(f"backends-check: unknown arguments {args!r} (only --read-only-gate)", file=sys.stderr)
        return 2
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
        count, detail, _kind = _check_backend(name)
        if count is None:
            (down if remote else warnings).append(detail)
            continue
        print(f"backends-check: {name} OK ({count} models reachable)")
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
    raise SystemExit(main(sys.argv[1:]))
