"""Prompt evaluation must exercise its requested model, including central defaults.

Spec 026: the central default is no longer a model constant — it is whoever the
selector ranks first for the eval profile, resolved here by the REAL selector
over the offline snapshot (``tests/conftest.py``).
"""
import runpy
from pathlib import Path

import pytest

from llmxive.backends import router
from llmxive.backends.base import ChatResponse
from llmxive.model_selection import route

#: The selector's leader for ``deep_review`` over the offline snapshot.
CONFIGURED_PRIMARY = 'zai-org.glm-5.3'


def provider():
    return runpy.run_path(str(Path(__file__).resolve().parents[2] / 'eval/promptfoo/llmxive_provider.py'))['call_api']


@pytest.mark.parametrize('override', [None, 'explicit-model'])
def test_eval_uses_requested_model_and_real_user_payload(monkeypatch, override):
    monkeypatch.delenv('LLMXIVE_EVAL_MODEL', raising=False)
    monkeypatch.delenv('LLMXIVE_EVAL_PROFILE', raising=False)
    if override:
        monkeypatch.setenv('LLMXIVE_EVAL_MODEL', override)
    expected = override or CONFIGURED_PRIMARY
    calls = []
    def chat(messages, **kwargs):
        calls.append((messages, kwargs))
        return ChatResponse('review body', expected, 'dartmouth')
    monkeypatch.setattr(route, 'route_chat', chat)
    result = provider()('real system prompt', {}, {'vars': {'user_payload': 'real artifact bundle'}})
    assert result['output'] == 'review body'
    messages, kwargs = calls[0]
    assert [(m.role, m.content) for m in messages] == [
        ('system', 'real system prompt'), ('user', 'real artifact bundle')]
    assert kwargs['caller_model'] == expected and kwargs['profile'] == 'deep_review'
    assert kwargs['temperature'] == 0.0 and kwargs['max_tokens'] == router.REASONING_MAX_TOKENS


def test_peer_response_cannot_pass_primary_eval(monkeypatch):
    monkeypatch.setenv('LLMXIVE_EVAL_MODEL', 'requested-primary')
    monkeypatch.setattr(route, 'route_chat', lambda *a, **k:
                        ChatResponse('apparently valid review', 'different-peer', 'dartmouth'))
    result = provider()('prompt', {}, {})
    assert 'output' not in result
    assert 'requested-primary' in result['error'] and 'different-peer' in result['error']


def test_peer_response_cannot_pass_selected_leader_eval(monkeypatch):
    """With no explicit model the selector's leader is the model under evaluation,
    so a reply from a lower-ranked peer is rejected just the same."""
    monkeypatch.delenv('LLMXIVE_EVAL_MODEL', raising=False)
    monkeypatch.delenv('LLMXIVE_EVAL_PROFILE', raising=False)
    monkeypatch.setattr(route, 'route_chat', lambda *a, **k:
                        ChatResponse('apparently valid review', 'qwen.qwen3.5-122b', 'dartmouth'))
    result = provider()('prompt', {}, {})
    assert 'output' not in result
    assert CONFIGURED_PRIMARY in result['error'] and 'qwen.qwen3.5-122b' in result['error']
