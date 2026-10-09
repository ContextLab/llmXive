"""Prompt evaluation must exercise its requested model, including central defaults."""
import runpy
from pathlib import Path

import pytest

from llmxive.backends import router
from llmxive.backends.base import ChatResponse


def provider():
    return runpy.run_path(str(Path(__file__).resolve().parents[2] / 'eval/promptfoo/llmxive_provider.py'))['call_api']


@pytest.mark.parametrize('override', [None, 'explicit-model'])
def test_eval_uses_requested_model_and_real_user_payload(monkeypatch, override):
    monkeypatch.delenv('LLMXIVE_EVAL_MODEL', raising=False)
    monkeypatch.setenv('LLMXIVE_EVAL_BACKEND', 'dartmouth')
    monkeypatch.setattr(router, 'DEFAULT_MODEL', 'configured-primary')
    if override:
        monkeypatch.setenv('LLMXIVE_EVAL_MODEL', override)
    expected = override or 'configured-primary'
    calls = []
    def chat(messages, **kwargs):
        calls.append((messages, kwargs))
        return ChatResponse('review body', expected, 'dartmouth')
    monkeypatch.setattr(router, 'chat_with_fallback', chat)
    result = provider()('real system prompt', {}, {'vars': {'user_payload': 'real artifact bundle'}})
    assert result['output'] == 'review body'
    messages, kwargs = calls[0]
    assert [(m.role, m.content) for m in messages] == [
        ('system', 'real system prompt'), ('user', 'real artifact bundle')]
    assert kwargs['model'] == expected and kwargs['default_backend'] == 'dartmouth'
    assert kwargs['temperature'] == 0.0 and kwargs['max_tokens'] == router.REASONING_MAX_TOKENS


def test_peer_response_cannot_pass_primary_eval(monkeypatch):
    monkeypatch.setenv('LLMXIVE_EVAL_MODEL', 'requested-primary')
    monkeypatch.setattr(router, 'chat_with_fallback', lambda *a, **k:
                        ChatResponse('apparently valid review', 'different-peer', 'dartmouth'))
    result = provider()('prompt', {}, {})
    assert 'output' not in result
    assert 'requested-primary' in result['error'] and 'different-peer' in result['error']
