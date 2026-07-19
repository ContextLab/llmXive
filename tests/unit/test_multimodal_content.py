"""Canonical multimodal path (spec 026 slice 7): content parts, skip-class
rejection, and a DEMONSTRABLE token upper bound.

Also covers the dimension-authority fix: ``ImagePart`` must derive its
dimensions CANONICALLY from the encoded bytes (the provider processes the
BYTES, not caller-supplied width/height metadata) and reject any mismatch,
mime/content mismatch, empty payload, over-dimension, over-byte-size, or
over-pixel-count payload.
"""
from __future__ import annotations

import io

import pytest

from llmxive.backends.base import (
    ChatMessage,
    ImagePart,
    PermanentBackendError,
    TextPart,
    UnsupportedFeatureError,
    parse_image_dimensions,
)
from llmxive.backends.router import CandidateDisposition, disposition_of
from llmxive.model_selection import tokens


def _pil_bytes(w: int, h: int, fmt: str = "PNG", color=(255, 0, 0)) -> bytes:
    """Build REAL encoded image bytes at exactly (w, h) via PIL."""
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, format=fmt)
    return buf.getvalue()


_MIME_FOR_FMT = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}

# A max-one-side (1536) but comfortably-under-the-pixel-cap image, used as the
# module default so "at the boundary" tests still exercise the true per-side
# maximum without tripping MAX_IMAGE_PIXELS (see test_pixel_count.py-ish
# tests below for the dedicated pixel-cap case, which uses the literal
# 1536x1536 square).
_DEFAULT_W, _DEFAULT_H = tokens.MAX_IMAGE_DIMENSION_PX, 1024
_PNG = _pil_bytes(_DEFAULT_W, _DEFAULT_H)


def _img(w=_DEFAULT_W, h=_DEFAULT_H, data=None, mime="image/png"):
    if data is None:
        data = _pil_bytes(w, h)
    return ImagePart(mime=mime, data=data, width=w, height=h)


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
        _img(w=tokens.MAX_IMAGE_DIMENSION_PX + 1, h=tokens.MAX_IMAGE_DIMENSION_PX)


def test_image_part_rejects_oversize_payload():
    with pytest.raises(ValueError, match="bytes"):
        _img(data=b"x" * (tokens.MAX_IMAGE_BYTES + 1))


def test_image_part_rejects_unknown_mime():
    with pytest.raises(ValueError, match="mime"):
        ImagePart(mime="application/pdf", data=_PNG, width=10, height=10)


# --- Dimension-authority fix (CONFIRMED HIGH-SEVERITY defect) -------------


def test_image_part_rejects_disguised_dimensions_png():
    """The confirmed repro: a 2000x2000 PNG declared 1x1 must be REJECTED —
    the provider processes the BYTES, not the declared metadata."""
    real = _pil_bytes(2000, 2000, "PNG")
    with pytest.raises(ValueError, match="do not match"):
        ImagePart(mime="image/png", data=real, width=1, height=1)


def test_image_part_rejects_disguised_dimensions_jpeg():
    """Same disguise, but for a COMPRESSED JPEG (a different header format)."""
    real = _pil_bytes(2000, 2000, "JPEG")
    with pytest.raises(ValueError, match="do not match"):
        ImagePart(mime="image/jpeg", data=real, width=1, height=1)


def test_image_part_rejects_disguised_dimensions_webp():
    """Same disguise, but for WebP (RIFF container, yet another header format)."""
    real = _pil_bytes(2000, 2000, "WEBP")
    with pytest.raises(ValueError, match="do not match"):
        ImagePart(mime="image/webp", data=real, width=1, height=1)


def test_highly_compressible_oversize_image_rejected_on_dimensions():
    """A flat-colour 4000x4000 PNG is TINY in bytes (well under
    MAX_IMAGE_BYTES) but enormous in pixels — proving a byte-size cap is NOT
    an adequate proxy for dimensions. It must be rejected because the
    CANONICAL parsed dimensions exceed MAX_IMAGE_DIMENSION_PX, even though
    declared == actual (so this isolates the dimension check, not the
    mismatch check) and even though the byte cap alone would pass it."""
    real = _pil_bytes(4000, 4000, "PNG", color=(10, 10, 10))
    assert len(real) < tokens.MAX_IMAGE_BYTES, "fixture must pass the byte cap to prove the point"
    with pytest.raises(ValueError, match="dimension"):
        ImagePart(mime="image/png", data=real, width=4000, height=4000)


def test_mime_content_mismatch_rejected():
    """mime='image/png' with actual JPEG bytes must be rejected — each
    per-format parser checks the format's own magic/signature bytes."""
    jpeg_bytes = _pil_bytes(64, 64, "JPEG")
    with pytest.raises(ValueError, match="PNG"):
        ImagePart(mime="image/png", data=jpeg_bytes, width=64, height=64)


def test_empty_payload_rejected():
    with pytest.raises(ValueError, match="empty"):
        ImagePart(mime="image/png", data=b"", width=1, height=1)


def test_excessive_pixel_count_within_per_side_limits_rejected():
    """The literal maximal square (1536x1536) individually satisfies the
    per-side MAX_IMAGE_DIMENSION_PX check on BOTH axes, yet its pixel count
    (2,359,296) exceeds MAX_IMAGE_PIXELS (2,097,152) — proving the per-side
    check alone does not bound total decode cost for every aspect ratio."""
    w = h = tokens.MAX_IMAGE_DIMENSION_PX
    assert w <= tokens.MAX_IMAGE_DIMENSION_PX and h <= tokens.MAX_IMAGE_DIMENSION_PX
    assert w * h > tokens.MAX_IMAGE_PIXELS, "fixture must actually exceed the pixel cap"
    real = _pil_bytes(w, h, "PNG")
    with pytest.raises(ValueError, match="pixels"):
        ImagePart(mime="image/png", data=real, width=w, height=h)


@pytest.mark.parametrize("fmt", ["PNG", "JPEG", "WEBP"])
def test_honest_in_bounds_images_still_accepted(fmt):
    """No regression: a real, honestly-declared, in-bounds image of each
    allowed mime still constructs cleanly."""
    data = _pil_bytes(200, 150, fmt, color=(20, 40, 60))
    part = ImagePart(mime=_MIME_FOR_FMT[fmt], data=data, width=200, height=150)
    assert (part.width, part.height) == (200, 150)


@pytest.mark.parametrize("fmt", ["PNG", "JPEG", "WEBP"])
def test_from_bytes_derives_correct_dimensions(fmt):
    data = _pil_bytes(321, 213, fmt, color=(70, 80, 90))
    part = ImagePart.from_bytes(mime=_MIME_FOR_FMT[fmt], data=data)
    assert (part.width, part.height) == (321, 213)


@pytest.mark.parametrize("fmt", ["PNG", "JPEG", "WEBP"])
def test_parse_image_dimensions_matches_pil_ground_truth(fmt):
    from PIL import Image

    data = _pil_bytes(77, 55, fmt, color=(1, 2, 3))
    assert parse_image_dimensions(_MIME_FOR_FMT[fmt], data) == (77, 55)
    assert Image.open(io.BytesIO(data)).size == (77, 55)


def test_parse_image_dimensions_rejects_garbage():
    with pytest.raises(ValueError):
        parse_image_dimensions("image/png", b"not an image at all")


# --- Existing coverage (unchanged behavior) --------------------------------


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
