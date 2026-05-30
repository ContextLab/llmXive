"""T023 — Unit tests for results/receipt.py (spec 016, US2).

All tests use REAL tmp files and a real env key set via monkeypatch.
No mocks, no stubs, no pass-only logic.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from llmxive.credentials import MissingCredentialError
from llmxive.results.receipt import (
    RECEIPT_KEY_ENV,
    Receipt,
    load_signing_key,
    sign_receipt,
    verify_receipt,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_receipt(*, value: str = "42.0", hmac_val: str = "placeholder") -> dict:
    """Return a plain-dict receipt payload (all fields, including hmac)."""
    return {
        "result_id": "r_abcd1234",
        "value": value,
        "kind": "scalar",
        "producer": {"script_path": "code/run.py", "code_sha": "abc123",
                     "entrypoint": "main", "seed": 0},
        "inputs": {"dataset_id": "ds_xyz", "data_sha256": "deadbeef",
                   "params": {"n": 100}},
        "env_sha": "env_sha_xyz",
        "captured": {"stdout_path": "out.txt", "return_repr": "42.0"},
        "output_sha256": hashlib.sha256(b"42.0").hexdigest(),
        "created_at": "2026-05-30T00:00:00Z",
        "hmac": hmac_val,
    }


def _build_receipt(key: bytes) -> Receipt:
    """Sign + build a real Receipt from a fresh payload."""
    fields = _make_receipt()
    sig = sign_receipt(fields, key=key)
    fields["hmac"] = sig
    return Receipt(**fields)


# ---------------------------------------------------------------------------
# T023-a: sign → verify round-trip passes
# ---------------------------------------------------------------------------

class TestSignVerifyRoundTrip:
    def test_roundtrip_passes(self, monkeypatch, tmp_path):
        monkeypatch.setenv(RECEIPT_KEY_ENV, "unit-test-signing-key")
        key = load_signing_key()
        receipt = _build_receipt(key)
        assert verify_receipt(receipt, key=key) is True

    def test_different_keys_fail(self, monkeypatch):
        monkeypatch.setenv(RECEIPT_KEY_ENV, "unit-test-signing-key")
        key = load_signing_key()
        receipt = _build_receipt(key)
        wrong_key = b"totally-different-key"
        assert verify_receipt(receipt, key=wrong_key) is False


# ---------------------------------------------------------------------------
# T023-b: ANY field mutation → verify returns False
# ---------------------------------------------------------------------------

class TestFieldMutationInvalidates:
    """Each test mutates exactly one field of a correctly-signed receipt."""

    def _signed(self, key: bytes) -> Receipt:
        return _build_receipt(key)

    def test_mutate_value(self, monkeypatch):
        monkeypatch.setenv(RECEIPT_KEY_ENV, "unit-test-signing-key")
        key = load_signing_key()
        r = self._signed(key)
        bad = Receipt(
            result_id=r.result_id, value="999.0", kind=r.kind,
            producer=r.producer, inputs=r.inputs, env_sha=r.env_sha,
            captured=r.captured, output_sha256=r.output_sha256,
            created_at=r.created_at, hmac=r.hmac,
        )
        assert verify_receipt(bad, key=key) is False

    def test_mutate_output_sha256(self, monkeypatch):
        monkeypatch.setenv(RECEIPT_KEY_ENV, "unit-test-signing-key")
        key = load_signing_key()
        r = self._signed(key)
        bad = Receipt(
            result_id=r.result_id, value=r.value, kind=r.kind,
            producer=r.producer, inputs=r.inputs, env_sha=r.env_sha,
            captured=r.captured,
            output_sha256="aaaa" * 16,  # wrong sha
            created_at=r.created_at, hmac=r.hmac,
        )
        assert verify_receipt(bad, key=key) is False

    def test_mutate_result_id(self, monkeypatch):
        monkeypatch.setenv(RECEIPT_KEY_ENV, "unit-test-signing-key")
        key = load_signing_key()
        r = self._signed(key)
        bad = Receipt(
            result_id="r_forged00", value=r.value, kind=r.kind,
            producer=r.producer, inputs=r.inputs, env_sha=r.env_sha,
            captured=r.captured, output_sha256=r.output_sha256,
            created_at=r.created_at, hmac=r.hmac,
        )
        assert verify_receipt(bad, key=key) is False

    def test_mutate_producer(self, monkeypatch):
        monkeypatch.setenv(RECEIPT_KEY_ENV, "unit-test-signing-key")
        key = load_signing_key()
        r = self._signed(key)
        bad_producer = dict(r.producer)
        bad_producer["code_sha"] = "forged_sha"
        bad = Receipt(
            result_id=r.result_id, value=r.value, kind=r.kind,
            producer=bad_producer, inputs=r.inputs, env_sha=r.env_sha,
            captured=r.captured, output_sha256=r.output_sha256,
            created_at=r.created_at, hmac=r.hmac,
        )
        assert verify_receipt(bad, key=key) is False

    def test_mutate_env_sha(self, monkeypatch):
        monkeypatch.setenv(RECEIPT_KEY_ENV, "unit-test-signing-key")
        key = load_signing_key()
        r = self._signed(key)
        bad = Receipt(
            result_id=r.result_id, value=r.value, kind=r.kind,
            producer=r.producer, inputs=r.inputs, env_sha="tampered_env",
            captured=r.captured, output_sha256=r.output_sha256,
            created_at=r.created_at, hmac=r.hmac,
        )
        assert verify_receipt(bad, key=key) is False

    def test_mutate_created_at(self, monkeypatch):
        monkeypatch.setenv(RECEIPT_KEY_ENV, "unit-test-signing-key")
        key = load_signing_key()
        r = self._signed(key)
        bad = Receipt(
            result_id=r.result_id, value=r.value, kind=r.kind,
            producer=r.producer, inputs=r.inputs, env_sha=r.env_sha,
            captured=r.captured, output_sha256=r.output_sha256,
            created_at="1970-01-01T00:00:00Z", hmac=r.hmac,
        )
        assert verify_receipt(bad, key=key) is False


# ---------------------------------------------------------------------------
# T023-c: load_signing_key reads from real env var
# ---------------------------------------------------------------------------

class TestLoadSigningKey:
    def test_reads_from_env(self, monkeypatch):
        monkeypatch.setenv(RECEIPT_KEY_ENV, "my-real-test-key-value")
        key = load_signing_key()
        assert key == b"my-real-test-key-value"

    def test_returns_bytes(self, monkeypatch):
        monkeypatch.setenv(RECEIPT_KEY_ENV, "some-key")
        assert isinstance(load_signing_key(), bytes)

    def test_raises_when_absent(self, monkeypatch, tmp_path):
        # Remove env var AND point credentials to a tmp (non-existent) path.
        monkeypatch.delenv(RECEIPT_KEY_ENV, raising=False)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        with pytest.raises(MissingCredentialError):
            load_signing_key()

    def test_env_var_not_in_receipt_fields(self, monkeypatch):
        """The signing key must NOT appear on any Receipt field."""
        monkeypatch.setenv(RECEIPT_KEY_ENV, "super-secret-key-xyz")
        key = load_signing_key()
        receipt = _build_receipt(key)
        # Serialize the receipt's public fields to a string and check.
        as_json = json.dumps({
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
        })
        assert "super-secret-key-xyz" not in as_json

    def test_key_from_credentials_file(self, monkeypatch, tmp_path):
        """load_signing_key reads from the credentials file when env is unset."""
        monkeypatch.delenv(RECEIPT_KEY_ENV, raising=False)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        # Create a real credentials.toml with the receipt key field.
        creds_dir = tmp_path / "llmxive"
        creds_dir.mkdir(parents=True)
        creds_file = creds_dir / "credentials.toml"
        creds_file.write_text('llmxive_receipt_key = "file-based-key"\n',
                               encoding="utf-8")
        import os as _os
        _os.chmod(str(creds_file), 0o600)
        key = load_signing_key()
        assert key == b"file-based-key"
