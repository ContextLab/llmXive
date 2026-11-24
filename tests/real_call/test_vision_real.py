"""SC-008 vision verification (Constitution II): real image UNDERSTANDING, not
merely payload acceptance."""
from __future__ import annotations

import io

from llmxive.backends.base import ChatMessage, ImagePart, TextPart
from llmxive.model_selection.route import route_chat
from llmxive.model_selection.types import RequirementOverrides


def _red_square_png() -> tuple[bytes, int, int]:
    """A 256x256 PURE RED png. A model that ignores the image cannot name red."""
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (256, 256), (255, 0, 0)).save(buf, format="PNG")
    return buf.getvalue(), 256, 256


def _asks_for_the_colour() -> list[ChatMessage]:
    png, w, h = _red_square_png()
    return [
        ChatMessage(role="system", content="Answer with ONE word."),
        ChatMessage(role="user", content=(
            TextPart("What is the dominant colour of this image? One word."),
            ImagePart(mime="image/png", data=png, width=w, height=h),
        )),
    ]


def test_qwen35_actually_understands_images():
    """THE GATE for the policy attribution: qwen3.5-122b must READ the image."""
    resp = route_chat(_asks_for_the_colour(), profile="vision", max_tokens=64)
    assert resp.model == "qwen.qwen3.5-122b"
    assert "red" in resp.text.lower(), f"no image understanding; got {resp.text!r}"


def test_qwen3_vl_serves_the_canonical_multimodal_representation():
    """SC-008 names qwen.qwen3-vl:32b as the vision tier INDEPENDENTLY of the
    qwen3.5 attribution; it must also consume the new ContentPart form."""
    resp = route_chat(
        _asks_for_the_colour(), profile="vision", max_tokens=64,
        overrides=RequirementOverrides(exclude_leader=True),
    )
    assert resp.model == "qwen.qwen3-vl:32b"
    assert "red" in resp.text.lower(), f"no image understanding; got {resp.text!r}"
