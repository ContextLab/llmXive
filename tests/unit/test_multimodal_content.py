"""Canonical multimodal path (spec 026 slice 7): content parts, skip-class
rejection, and a DEMONSTRABLE token upper bound."""
from __future__ import annotations

import pytest

from llmxive.backends.base import (
    ChatMessage,
    ImagePart,
    PermanentBackendError,
    TextPart,
    UnsupportedFeatureError,
)
from llmxive.backends.router import CandidateDisposition, disposition_of
from llmxive.model_selection import tokens

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 512


def _img(w=1536, h=1536, data=_PNG):
    return ImagePart(mime="image/png", data=data, width=w, height=h)


def test_string_content_still_valid_and_unchanged():
    assert ChatMessage(role="user", content="plain text").content == "plain text"


def test_parts_content_is_an_immutable_tuple():
    import dataclasses

    m = ChatMessage(role="user", content=(TextPart("look:"), _img()))
    assert isinstance(m.content, tuple)
    with pytest.raises(dataclasses.FrozenInstanceError):
        m.content = "mutated"          # frozen dataclass


def test_image_part_rejects_oversize_dimensions():
    with pytest.raises(ValueError, match="dimension"):
        _img(w=tokens.MAX_IMAGE_DIMENSION_PX + 1)


def test_image_part_rejects_oversize_payload():
    with pytest.raises(ValueError, match="bytes"):
        _img(data=b"x" * (tokens.MAX_IMAGE_BYTES + 1))


def test_image_part_rejects_unknown_mime():
    with pytest.raises(ValueError, match="mime"):
        ImagePart(mime="application/pdf", data=_PNG, width=10, height=10)


def test_unsupported_feature_is_SKIP_not_ABORT():
    """A text-only backend refusing an image must SKIP the candidate. A plain
    PermanentBackendError would ABORT the whole chain (router.py:211)."""
    assert disposition_of(UnsupportedFeatureError("no vision")) is CandidateDisposition.SKIP
    assert disposition_of(PermanentBackendError("hard refusal")) is CandidateDisposition.ABORT
    assert isinstance(UnsupportedFeatureError("x"), PermanentBackendError)


def test_estimator_is_at_least_the_documented_maximum_at_boundary():
    """UPPER-bound proof: a max-dimension image must price AT OR ABOVE the
    documented per-image worst case — not merely above an average-looking floor."""
    msgs = [ChatMessage(role="user", content=(TextPart("hi"), _img()))]
    assert tokens.max_input_tokens_upper_bound(msgs) >= tokens.TOKENS_PER_IMAGE


def test_estimator_scales_with_image_count():
    one = tokens.max_input_tokens_upper_bound([ChatMessage(role="user", content=(_img(),))])
    three = tokens.max_input_tokens_upper_bound(
        [ChatMessage(role="user", content=(_img(), _img(), _img()))]
    )
    assert three >= one + 2 * tokens.TOKENS_PER_IMAGE


def test_mixed_text_and_image_accounting():
    text_only = tokens.max_input_tokens_upper_bound(
        [ChatMessage(role="user", content="a" * 4000)]
    )
    mixed = tokens.max_input_tokens_upper_bound(
        [ChatMessage(role="user", content=(TextPart("a" * 4000), _img()))]
    )
    assert mixed >= text_only + tokens.TOKENS_PER_IMAGE


def test_local_backend_rejects_multimodal_with_the_skip_class():
    from llmxive.backends.local import LocalBackend

    with pytest.raises(UnsupportedFeatureError):
        LocalBackend().chat(
            [ChatMessage(role="user", content=(_img(),))],
            model="Qwen/Qwen2.5-3B-Instruct",
        )
