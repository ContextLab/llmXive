"""T026 — Execution harness: mint and verify receipts (spec 016, US2).

HARNESS-ONLY: this module is called exclusively from implementation/analysis
stage code (scripts, CI).  No LLM / agent / prompt path ever calls
``mint_receipt``.

mint_receipt(...)    — compute output_sha256, sign, persist, return Receipt.
result_backed(...)   — return a Receipt only when output_sha256 matches AND
                       verify_receipt passes; else None.
"""

from __future__ import annotations

import datetime
import hashlib
from pathlib import Path
from typing import Any

from llmxive.results.receipt import (
    Receipt,
    load_signing_key,
    sign_receipt,
    verify_receipt,
)
from llmxive.state import results as _result_store


def _sha256_of_value(value: Any) -> str:
    """Return the SHA-256 hexdigest of ``str(value)`` encoded as UTF-8."""
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def _result_id_from_sha(output_sha256: str) -> str:
    """Derive a stable result_id from the output hash: ``r_`` + first 8 chars."""
    return "r_" + output_sha256[:8]


def _now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def mint_receipt(
    *,
    value: Any,
    kind: str,
    producer: dict[str, Any],
    inputs: dict[str, Any],
    env_sha: str,
    captured: dict[str, Any],
    repo_root: Path,
    project_id: str,
    created_at: str | None = None,
) -> Receipt:
    """Compute output_sha256, sign all fields, persist, and return a Receipt.

    HARNESS-ONLY — never called from an LLM/agent path.

    Parameters
    ----------
    value:
        The scalar result value (or path to a table/figure artifact).
    kind:
        ``"scalar"`` | ``"table"`` | ``"figure"``
    producer:
        ``{script_path, code_sha, entrypoint, seed}``
    inputs:
        ``{dataset_id, data_sha256, params}``
    env_sha:
        Lock-file / environment hash.
    captured:
        ``{stdout_path, return_repr}``
    repo_root:
        Repo root used for persisting the receipt.
    project_id:
        Project identifier (used as the storage sub-directory).
    created_at:
        ISO-8601 string; defaults to ``now()`` when None.
    """
    str_value = str(value)
    output_sha256 = _sha256_of_value(str_value)
    result_id = _result_id_from_sha(output_sha256)
    ts = created_at or _now_iso()

    # Build the unsigned payload dict to sign over (hmac excluded from hash).
    unsigned: dict[str, Any] = {
        "result_id": result_id,
        "value": str_value,
        "kind": kind,
        "producer": producer,
        "inputs": inputs,
        "env_sha": env_sha,
        "captured": captured,
        "output_sha256": output_sha256,
        "created_at": ts,
        "hmac": "",  # placeholder so canonicalisation sees all keys
    }
    # sign_receipt ignores the 'hmac' key, so placeholder is fine.
    key = load_signing_key()
    sig = sign_receipt(unsigned, key=key)

    receipt = Receipt(
        result_id=result_id,
        value=str_value,
        kind=kind,
        producer=producer,
        inputs=inputs,
        env_sha=env_sha,
        captured=captured,
        output_sha256=output_sha256,
        created_at=ts,
        hmac=sig,
    )

    _result_store.save(project_id, receipt, repo_root=repo_root)
    return receipt


def result_backed(
    value: str,
    project_id: str,
    *,
    repo_root: Path,
) -> Receipt | None:
    """Return a Receipt for ``value`` only when it is provably backed.

    "Provably backed" means:
        1. A receipt exists for the project whose ``output_sha256`` matches
           the SHA-256 of ``value``.
        2. ``verify_receipt`` passes with the current signing key.

    Returns None if no matching receipt exists OR if HMAC verification fails
    (covers both missing-receipt and SC-004 forgery cases).
    """
    target_sha = _sha256_of_value(value)
    key = load_signing_key()

    for receipt in _result_store.load_all(project_id, repo_root=repo_root):
        if receipt.output_sha256 == target_sha:
            if verify_receipt(receipt, key=key):
                return receipt
            # HMAC mismatch — receipt was tampered with; do NOT return it.
            return None

    return None


__all__ = ["mint_receipt", "result_backed"]
