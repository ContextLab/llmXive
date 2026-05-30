"""T024 — Execution receipt + signing (spec 016, US2).

Receipt is a frozen dataclass matching data-model.md.
sign_receipt / verify_receipt use HMAC-SHA256 over a deterministic
canonical JSON of all fields except 'hmac' (sorted keys).
load_signing_key resolves the process-local signing secret from env then
credentials file — exactly like the Dartmouth key loader.  The key is
NEVER stored on the Receipt object or passed into any model/agent context.
"""

from __future__ import annotations

import hashlib
import hmac as _hmac
import json
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from llmxive.credentials import (
    MissingCredentialError,
    check_permissions,
    credentials_path,
)

RECEIPT_KEY_ENV = "LLMXIVE_RECEIPT_KEY"
_CREDENTIALS_FIELD = "llmxive_receipt_key"


# ---------------------------------------------------------------------------
# Receipt dataclass (data-model.md)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Receipt:
    """Harness-signed execution receipt.  Minted ONLY by results/harness.py,
    never by an LLM or agent path.

    Field notes:
      result_id    — ``r_<sha8>``
      value        — scalar value or pointer to a table/figure artifact
      kind         — ``scalar | table | figure``
      producer     — ``{script_path, code_sha, entrypoint, seed}``
      inputs       — ``{dataset_id, data_sha256, params}``
      env_sha      — lock-file / environment hash
      captured     — ``{stdout_path, return_repr}``
      output_sha256— SHA-256 of the produced value / artifact
      created_at   — ISO-8601 mint time
      hmac         — HMAC-SHA256 hexdigest over canonical payload; key never
                     stored on this object
    """

    result_id: str
    value: str
    kind: str  # "scalar" | "table" | "figure"
    producer: dict
    inputs: dict
    env_sha: str
    captured: dict
    output_sha256: str
    created_at: str
    hmac: str


# ---------------------------------------------------------------------------
# Canonical payload
# ---------------------------------------------------------------------------

def _canonical_payload(fields: dict) -> bytes:
    """Deterministic JSON serialisation of all receipt fields except 'hmac'.

    Keys are sorted; no whitespace beyond what json.dumps adds.  This is the
    canonical form that sign_receipt and verify_receipt both hash.
    """
    payload = {k: v for k, v in fields.items() if k != "hmac"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")


def _receipt_to_fields(receipt: Receipt) -> dict:
    """Convert a Receipt to a plain dict (all fields)."""
    return {
        "result_id": receipt.result_id,
        "value": receipt.value,
        "kind": receipt.kind,
        "producer": receipt.producer,
        "inputs": receipt.inputs,
        "env_sha": receipt.env_sha,
        "captured": receipt.captured,
        "output_sha256": receipt.output_sha256,
        "created_at": receipt.created_at,
        "hmac": receipt.hmac,
    }


# ---------------------------------------------------------------------------
# sign / verify
# ---------------------------------------------------------------------------

def sign_receipt(payload: dict, *, key: bytes) -> str:
    """Return the HMAC-SHA256 hexdigest over the canonical payload.

    ``payload`` is the dict of all receipt fields **excluding** 'hmac'.
    The key is caller-supplied and never stored on the resulting Receipt.
    """
    canon = _canonical_payload(payload)
    return _hmac.new(key, canon, hashlib.sha256).hexdigest()


def verify_receipt(receipt: Receipt, *, key: bytes) -> bool:
    """Recompute the HMAC and compare with ``hmac.compare_digest``.

    Returns False (never raises) on any mismatch — the caller blocks.
    """
    fields = _receipt_to_fields(receipt)
    expected = sign_receipt(fields, key=key)
    # compare_digest prevents timing attacks; also safe for unequal lengths.
    return _hmac.compare_digest(expected, receipt.hmac)


# ---------------------------------------------------------------------------
# Key loader (process-local secret, env-first like Dartmouth)
# ---------------------------------------------------------------------------

def load_signing_key() -> bytes:
    """Resolve the receipt-signing key from the process environment.

    Resolution order:
        1. Env var ``LLMXIVE_RECEIPT_KEY`` (highest priority — CI / tests).
        2. ``~/.config/llmxive/credentials.toml`` field
           ``llmxive_receipt_key``.

    Raises :class:`~llmxive.credentials.MissingCredentialError` when the
    key is absent from both sources — signing fails fast rather than
    silently using an insecure default.

    The key is returned as raw UTF-8 bytes.  It is NEVER stored on a
    Receipt object or passed into any model / agent / prompt context.
    """
    env = os.environ.get(RECEIPT_KEY_ENV)
    if env and env.strip():
        return env.strip().encode("utf-8")

    chk = check_permissions()
    if not chk.ok:
        raise PermissionError(chk.reason)
    if chk.exists:
        try:
            data = tomllib.loads(chk.path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            data = {}
        raw_key = (data or {}).get(_CREDENTIALS_FIELD)
        if isinstance(raw_key, str) and raw_key.strip():
            return raw_key.strip().encode("utf-8")

    raise MissingCredentialError(
        f"Receipt signing key not found. "
        f"Set ${RECEIPT_KEY_ENV} or add "
        f'`{_CREDENTIALS_FIELD} = "..."` to {credentials_path()}.'
    )


__all__ = [
    "Receipt",
    "RECEIPT_KEY_ENV",
    "load_signing_key",
    "sign_receipt",
    "verify_receipt",
]
