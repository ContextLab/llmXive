"""Actual author -> production writer -> independent verifier -> optional TeX toolchain."""
import json
import os
import secrets
import shutil
from pathlib import Path

import pytest

from llmxive.agents.task_verifier import DEFAULT_MODEL, verified_done_keys
from llmxive.backends.router import chat_with_fallback
from llmxive.speckit.paper_implement_cmd import PaperImplementerAgent
from llmxive.speckit.slash_command import SlashCommandContext
from llmxive.types import BackendName

pytestmark = pytest.mark.skipif(
    os.environ.get('LLMXIVE_REAL_TESTS') != '1' or not os.environ.get('DARTMOUTH_CHAT_API_KEY'),
    reason='live Dartmouth unavailable',
)


def test_real_empty_source_paper_bootstrap(tmp_path, monkeypatch):
    from llmxive.agents import _task_verdict_receipt, task_verifier
    # Exercise durable verification without requiring a production signing key.
    # Author and independent verifier calls below remain real primary calls.
    signing_key = secrets.token_bytes(32)
    monkeypatch.setattr(_task_verdict_receipt, 'load_signing_key', lambda: signing_key)
    verifier_models = []
    real_verify_chat = task_verifier.chat_with_fallback
    def observed_verifier(*args, **kwargs):
        response = real_verify_chat(*args, **kwargs)
        verifier_models.append(response.model)
        return response
    monkeypatch.setattr(task_verifier, "chat_with_fallback", observed_verifier)
    repo = Path(__file__).resolve().parents[2]
    (tmp_path / 'agents').symlink_to(repo / 'agents')
    project = tmp_path / 'projects/PROJ-901-paper-bootstrap'
    feature = project / 'paper/specs/001-paper'
    feature.mkdir(parents=True)
    (feature / 'spec.md').write_text('Paper scaffolding: create a minimal article without scientific claims, citations or external files. Later tasks compose actual results.')
    (feature / 'plan.md').write_text('First scaffold a compilable main.tex. Later add the accepted research.')
    tasks = feature / 'tasks.md'
    tasks.write_text('- [ ] T001 [kind:latex-build] Create paper/source/main.tex using article class and amsthm, with a document containing only the text Paper scaffold. No inputs, citations, figures, metadata, title, abstract, or bibliography yet.\n'
                     '- [ ] T002 [kind:prose] Later write paper/source/results.tex from the accepted research report.\n')
    memory = project / 'paper/.specify/memory'
    memory.mkdir(parents=True)
    (memory / 'constitution.md').write_text('Do not invent scientific results. Only scaffold the selected task.')
    ctx = SlashCommandContext(project.name, project, 'real-bootstrap', 'T001', [], [], repo / 'unused',
                              BackendName.DARTMOUTH, [], DEFAULT_MODEL, '1', 'paper_implementer')
    agent = PaperImplementerAgent()
    step = agent.mechanical_step(ctx)
    assert not (project / 'paper/source').exists()
    messages = agent.build_prompt(ctx, step)
    response = chat_with_fallback(messages, default_backend='dartmouth', fallback_backends=[], model=DEFAULT_MODEL)
    assert response.model == DEFAULT_MODEL
    (tmp_path / 'author-response.json').write_text(json.dumps({'model': response.model, 'text': response.text}, indent=2))
    agent.write_artifacts(ctx, step, response)  # real independent verification is inside the production writer
    assert verifier_models == [DEFAULT_MODEL]
    assert (project / 'paper/source/main.tex').is_file()
    assert verified_done_keys(project, tasks, model=DEFAULT_MODEL) == {'T001'}
    assert '[X] T001' in tasks.read_text() and '[ ] T002' in tasks.read_text()
    assert not (memory / 'human_input_needed.yaml').exists()
    # Hosted PR workers intentionally lack TeX; local acceptance additionally
    # compiles these exact model-created bytes and persists the build result.
    if shutil.which('pdflatex'):
        from llmxive.agents.latex_build import build_paper
        result = build_paper(project.name, repo_root=tmp_path)
        (tmp_path / 'actual-produced-source-build.json').write_text(json.dumps(result, indent=2))
        assert result['ok'], result['stdout']
        assert Path(result['pdf_path']).read_bytes().startswith(b'%PDF')
