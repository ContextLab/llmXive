"""Malformed documents must not pin corrective retries to a healthy bad producer."""
from types import SimpleNamespace

import pytest

from llmxive.backends.base import BackendUnavailable, ChatMessage, ChatResponse
from llmxive.backends.router import GENERATION_MAX_TOKENS, chat_with_model_fallback
from llmxive.convergence.revisers._reviser_response import run_pass_with_artifact_retry
from llmxive.convergence.revisers._self_consistency import invoke_reviser_backend
from llmxive.convergence.revisers.tasks_reviser import TasksReviser

GLM = 'zai-org.glm-5.3'
GPT = 'openai.gpt-oss-120b'
GEMMA = 'google.gemma-4-31B-it'
PATH = 'projects/PROJ-test/specs/001-test/tasks.md'
VALID = f'```json\n{{"responses": []}}\n```\n===BEGIN_ARTIFACT {PATH}===\n- [ ] T001 Run the measured experiment.\n===END_ARTIFACT==='


class Backend:
    def __init__(self, *, invalid_peer=False, unavailable_peer=False, duplicate_ids=False):
        self.calls = []
        self.duplicate_ids = duplicate_ids
        self.invalid_peer = invalid_peer
        self.unavailable_peer = unavailable_peer

    def chat(self, messages, *, model, max_tokens=None, **kwargs):
        self.calls.append((model, max_tokens, list(messages)))
        if model == GLM or (model == GEMMA and self.unavailable_peer):
            raise BackendUnavailable('fixture outage')
        assert model in {GPT, GEMMA}, 'a format retry must not try paid models'
        # The observed failure: a complete-looking body without END_ARTIFACT.
        text = VALID if model == GEMMA and not self.invalid_peer else VALID.rsplit('\n', 1)[0]
        if model == GPT and self.duplicate_ids:
            text = VALID.replace('===END_ARTIFACT===', '- [ ] T001 Duplicate task.\n===END_ARTIFACT===')
        return ChatResponse(text=text, model=model, backend='fixture')


def revision_attempt(backend, tmp_path):
    reviser = TasksReviser(backend=backend, repo_root=tmp_path, project_id='PROJ-test', model=GLM)
    def run_pass(extra=''):
        text = invoke_reviser_backend(reviser, [ChatMessage(role='user', content=extra)])
        return reviser._parse_response(text, [], PATH)
    return reviser, run_pass


@pytest.mark.parametrize("duplicate_ids", [False, True])
def test_actual_fallback_producer_is_excluded_from_existing_corrective_attempt(tmp_path, duplicate_ids):
    backend = Backend(duplicate_ids=duplicate_ids)
    reviser, attempt = revision_attempt(backend, tmp_path)
    artifact, _ = run_pass_with_artifact_retry(attempt, reviser_name='TasksReviser', reviser=reviser)
    assert 'T001' in artifact
    assert [c[0] for c in backend.calls] == [GLM, GPT, GLM, GEMMA]
    assert all(c[1] == GENERATION_MAX_TOKENS for c in backend.calls)
    assert 'END_ARTIFACT' in backend.calls[-1][2][-1].content
    assert reviser._revision_excluded_models == frozenset()
    assert reviser._model == GLM  # no persistent mutation of user/model preference


def test_two_invalid_free_responses_still_fail_closed(tmp_path):
    backend = Backend(invalid_peer=True)
    reviser, attempt = revision_attempt(backend, tmp_path)
    with pytest.raises(RuntimeError, match='no usable'):
        run_pass_with_artifact_retry(attempt, reviser_name='TasksReviser', reviser=reviser)
    assert [c[0] for c in backend.calls] == [GLM, GPT, GLM, GEMMA]
    assert reviser._revision_excluded_models == frozenset()


def test_corrective_outage_does_not_escape_to_paid_or_retry_bad_producer(tmp_path):
    backend = Backend(unavailable_peer=True)
    reviser, attempt = revision_attempt(backend, tmp_path)
    with pytest.raises(BackendUnavailable):
        run_pass_with_artifact_retry(attempt, reviser_name='TasksReviser', reviser=reviser)
    assert [c[0] for c in backend.calls] == [GLM, GPT, GLM, GEMMA]
    assert reviser._revision_excluded_models == frozenset()


@pytest.mark.parametrize('error', [ValueError('logic bug'), RuntimeError('logic bug'), BackendUnavailable('outage')])
def test_non_format_errors_are_not_retried(error):
    calls = []
    def attempt(extra=''):
        calls.append(extra)
        raise error
    with pytest.raises(type(error), match=str(error)):
        run_pass_with_artifact_retry(attempt, reviser_name='TasksReviser', reviser=SimpleNamespace())
    assert len(calls) == 1


def test_valid_response_keeps_primary_selection():
    class ValidBackend:
        def chat(self, messages, *, model, **kwargs):
            assert model == GLM
            return ChatResponse(text=VALID, model=model, backend='fixture')
    assert chat_with_model_fallback(ValidBackend(), [], model=GLM).model == GLM


def test_unknown_model_preserves_existing_corrective_retry():
    reviser = SimpleNamespace(_model='private', _last_revision_model='private')
    calls = []
    def attempt(extra=''):
        calls.append(extra)
        if not extra:
            raise RuntimeError('no usable artifact')
        return 'corrected'
    assert run_pass_with_artifact_retry(attempt, reviser_name='private', reviser=reviser) == 'corrected'
    assert len(calls) == 2
    assert not hasattr(reviser, '_revision_excluded_models')
