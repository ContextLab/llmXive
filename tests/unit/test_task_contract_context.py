"""Contract packet limits are explicit and omissions cannot silently pass review."""

import pytest

from llmxive.speckit._task_contract_context import task_contract_context


@pytest.fixture
def feature(tmp_path):
    project = tmp_path / 'project'
    feature = project / 'specs/001-current'
    feature.mkdir(parents=True)
    return feature, project


def test_optional_absence_is_valid(feature):
    current, project = feature
    assert task_contract_context(current, project) == ''


@pytest.mark.parametrize('case', ['outside', 'feature_link', 'fifo', 'invalid_utf8', 'files', 'entries', 'total_bytes'])
def test_refuses_unsafe_or_incomplete_context(feature, tmp_path, case):
    current, project = feature
    contracts = current / 'contracts'
    contracts.mkdir()
    if case == 'outside':
        current = tmp_path / 'other-feature'
        current.mkdir()
    elif case == 'feature_link':
        link = current.parent / 'linked'
        link.symlink_to(current, target_is_directory=True)
        current = link
    elif case == 'fifo':
        import os
        os.mkfifo(contracts / 'blocked.yaml')
    elif case == 'invalid_utf8':
        (contracts / 'invalid.yaml').write_bytes(b'\xff')
    elif case == 'files':
        for i in range(33):
            (contracts / f'{i}.yaml').write_text('schema')
    elif case == 'entries':
        for i in range(256):
            (contracts / str(i)).mkdir()
    else:
        for i in range(3):
            (contracts / f'{i}.yaml').write_bytes(b'x' * 64 * 1024)
    with pytest.raises(ValueError, match='Task review context refused'):
        task_contract_context(current, project)
