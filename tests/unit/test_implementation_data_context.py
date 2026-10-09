"""Implementation reports must see measured data, not invent sample numbers."""
from llmxive.speckit.implement_cmd import _current_data_context, ImplementerAgent
from tests.unit.test_implementer_feedback_injection import _project, _ctx, _MECH


def test_real_prompt_contains_current_measurements(tmp_path):
    project = _project(tmp_path)
    (project/'data').mkdir()
    actual = '{"N":10000,"p":5,"tv_unconditional":0.1452}'
    (project/'data/summary.json').write_text(actual)
    mech = {**_MECH, 'next_task_line': '- [ ] T010 Write docs/research.md from results'}
    prompt = ImplementerAgent().build_prompt(_ctx(project.parent.parent, project), mech)[-1].content
    assert actual in prompt
    assert 'data/summary.json (sha256 ' in prompt
    assert 'Files may be stale or from a failed run' in prompt
    assert 'successful execution and independent verification are still required' in prompt


def test_context_is_bounded_and_does_not_follow_external_links(tmp_path):
    project = tmp_path/'project'
    (project/'data').mkdir(parents=True)
    (project/'data/small.json').write_text('{"measured": 12}')
    (project/'data/large.csv').write_text('a,b\n' + '1,2\n' * 10000)
    secret = tmp_path/'outside'
    secret.mkdir()
    (secret/'private.json').write_text('PRIVATE_SENTINEL')
    (project/'data/link.json').symlink_to(secret/'private.json')
    (project/'data/linked').symlink_to(secret, target_is_directory=True)
    (project/'results').symlink_to(secret, target_is_directory=True)
    text = _current_data_context(project, max_chars=500)
    assert len(text) <= 500
    assert '{"measured": 12}' in text
    assert 'large.csv' in text and 'contents omitted' in text
    assert 'PRIVATE_SENTINEL' not in text
    assert 'link.json' not in text


def test_empty_project_adds_no_data_context(tmp_path):
    assert _current_data_context(tmp_path) == ''
