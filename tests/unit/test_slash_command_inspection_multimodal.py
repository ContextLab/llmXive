"""spec 026 slice 7: the speckit inspection-record hook
(``_maybe_write_inspection`` in ``speckit/slash_command.py``) must survive a
ChatMessage carrying multimodal parts — extracting ``.content`` and joining it
into a JSON-serialized record used to silently crash on a parts tuple (caught
by the hook's own broad ``except Exception: pass`` and swallowed), meaning the
record was simply never written. ``render_text_content`` fixes that: images
render as a metadata-only placeholder and the record is written correctly.
"""
from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from pathlib import Path

from llmxive.backends.base import ChatMessage, ImagePart, TextPart
from llmxive.speckit.slash_command import SlashCommandContext, _maybe_write_inspection
from llmxive.types import BackendName, Outcome

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 512


def _ctx(spec_root: Path) -> SlashCommandContext:
    return SlashCommandContext(
        project_id="PROJ-999-test",
        project_dir=spec_root / "projects" / "PROJ-999-test",
        run_id="run-1",
        task_id="task-1",
        inputs=[],
        expected_outputs=[],
        prompt_template_path=Path("agents/prompts/fake.md"),
        default_backend=BackendName.DARTMOUTH,
        fallback_backends=[],
        default_model="fake-model",
        prompt_version="1.0.0",
        agent_name="fake_speckit_agent",
    )


def test_multimodal_message_writes_metadata_not_raw_bytes(tmp_path: Path, monkeypatch):
    inspection_dir = tmp_path / "specs" / "999-fake" / "inspections" / "PROJ-999-test"
    monkeypatch.setenv("LLMXIVE_INSPECTION_DIR", str(inspection_dir))

    ctx = _ctx(tmp_path)
    messages = [
        ChatMessage(role="system", content="you are a test agent"),
        ChatMessage(
            role="user",
            content=(
                TextPart("do the thing"),
                ImagePart(mime="image/png", data=_PNG, width=64, height=32),
            ),
        ),
    ]

    _maybe_write_inspection(
        ctx=ctx,
        started=datetime.now(UTC),
        ended=datetime.now(UTC),
        outcome=Outcome.SUCCESS,
        failure_reason=None,
        messages=messages,
        llm_response_text="ok",
        model_used="fake-model",
        backend_used=BackendName.DARTMOUTH,
    )

    expected = tmp_path / "specs" / "999-fake" / "inspections" / "PROJ-999-test" / "fake_speckit_agent.json"
    assert expected.exists(), "record must be written, not silently swallowed"

    raw_json = expected.read_text()
    assert _PNG.hex() not in raw_json
    assert base64.b64encode(_PNG).decode() not in raw_json

    record = json.loads(raw_json)
    user_prompt = record["prompts"]["user"]
    assert "do the thing" in user_prompt
    assert "image/png" in user_prompt
    assert "64x32" in user_prompt
    assert str(len(_PNG)) in user_prompt
