"""Revision output instructions must not conflict across message priorities."""
from types import SimpleNamespace

import pytest

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage,ChatResponse
from llmxive.convergence.revisers._reviser_response import RESPONSE_FORMAT_BLOCK
from llmxive.convergence.revisers._self_consistency import invoke_reviser_backend
from pathlib import Path


@pytest.mark.parametrize('prompt', ['tasker.md','clarifier.md','implementer_research.md',
                                   'paper_tasker.md','paper_implementer.md'])
def test_actual_author_prompt_gets_active_contract_at_system_priority(prompt):
    root=Path(__file__).resolve().parents[2]
    system=render_prompt('agents/prompts/'+prompt,{'project_id':'PROJ-test','next_task_id':'T001'},repo_root=root)
    messages=[ChatMessage(role='system',content=system),
              ChatMessage(role='user',content='Revise the named artifact.\n'+RESPONSE_FORMAT_BLOCK)]
    calls=[]
    class Backend:
        def chat(self,messages,**kwargs):
            calls.append(list(messages))
            return ChatResponse(text='fixture output',model='fixture',backend='fixture')
    reviser=SimpleNamespace(_backend=Backend(),_model=None)
    assert invoke_reviser_backend(reviser,messages)=='fixture output'
    sent=calls[0]
    assert sent[0].role=='system'
    assert sent[0].content.endswith(RESPONSE_FORMAT_BLOCK)
    assert 'authoring output format described above does not apply' in sent[0].content
    assert sent[0].content.startswith(system)
    assert messages[0].content==system  # caller's messages remain unchanged
