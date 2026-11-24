"""Shared backend pieces extracted from the Dartmouth backend (spec 027)."""

from __future__ import annotations

import struct
import zlib

import pytest

from llmxive.backends.base import (
    BackendCredentialError,
    BackendUnavailable,
    ChatResponse,
    CircuitBreaker,
    ImagePart,
    PermanentBackendError,
    TextPart,
    TransientBackendError,
    openai_content,
)
from llmxive.backends.router import CandidateDisposition, disposition_of


def _red_png() -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    ihdr = struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\xff\x00\x00" * 2 for _ in range(2))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def test_breaker_is_shared_and_dartmouth_alias_is_the_same_class():
    from llmxive.backends import dartmouth

    assert dartmouth._CircuitBreaker is CircuitBreaker


def test_dartmouth_open_error_message_unchanged():
    br = CircuitBreaker(max_consecutive=1, window_s=1800.0, clock=lambda: 0.0)
    with pytest.raises(TransientBackendError):
        br.call(lambda: (_ for _ in ()).throw(TransientBackendError("x")))
    with pytest.raises(BackendUnavailable, match="circuit open: Dartmouth endpoint persistently unavailable"):
        br.call(lambda: "never")


def test_breaker_label_appears_in_open_error():
    br = CircuitBreaker(max_consecutive=1, window_s=1800.0, clock=lambda: 0.0, label="Hugging Face")
    with pytest.raises(TransientBackendError):
        br.call(lambda: (_ for _ in ()).throw(TransientBackendError("x")))
    with pytest.raises(BackendUnavailable, match="Hugging Face endpoint persistently unavailable"):
        br.call(lambda: "never")


def test_openai_content_passthrough_and_image_data_url():
    assert openai_content("hi") == "hi"
    png = _red_png()
    out = openai_content((TextPart("what colour?"), ImagePart.from_bytes("image/png", png)))
    assert out[0] == {"type": "text", "text": "what colour?"}
    assert out[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_credential_error_skips_candidate():
    assert disposition_of(BackendCredentialError("401")) is CandidateDisposition.SKIP
    assert isinstance(BackendCredentialError("x"), PermanentBackendError)


def test_chat_response_token_counts_default_to_none():
    r = ChatResponse(text="t", model="m", backend="b")
    assert r.input_tokens is None and r.output_tokens is None and r.cost_estimate_usd == 0.0
