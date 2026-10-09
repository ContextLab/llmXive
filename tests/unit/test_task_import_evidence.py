"""Actual persisted local dependencies inform review without executing them."""

from llmxive.agents import _task_import_evidence as imports
from llmxive.agents import task_verifier as tv


def write(project, rel, contents):
    path = project / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents)
    return path


def test_nested_test_import_and_transitive_source_are_observed_without_execution(tmp_path):
    write(tmp_path, 'tests/test_tv.py',
          'def test_integration():\n    from analysis import analyze\n    assert analyze(100, 5)\n')
    write(tmp_path, 'code/analysis.py',
          'from utils import sieve\ndef analyze(n, p):\n    return sieve(n) % p\n')
    write(tmp_path, 'code/utils.py',
          "raise RuntimeError('DO NOT EXECUTE PROJECT CODE')\ndef sieve(n): return n\n")
    evidence = tv.gather_evidence(tmp_path, 'T007 Create tests/test_tv.py')
    assert 'Local import candidate `code/analysis.py`' in evidence
    assert 'def analyze(n, p)' in evidence
    assert 'Local import candidate `code/utils.py`' in evidence
    assert 'DO NOT EXECUTE PROJECT CODE' in evidence
    assert 'NOT proof of import resolution or successful execution' in evidence


def test_same_named_modules_are_candidates_not_a_runtime_resolution_claim(tmp_path):
    write(tmp_path, 'tests/test_check.py', 'import analysis\n')
    write(tmp_path, 'analysis.py', "VALUE = 'project-root variant'\n")
    write(tmp_path, 'code/analysis.py', "VALUE = 'code-root variant'\n")
    evidence = tv.gather_evidence(tmp_path, 'T001 Create tests/test_check.py')
    assert 'project-root variant' in evidence and 'code-root variant' in evidence
    assert 'Multiple candidates can exist' in evidence


def test_relative_import_and_package_initializers(tmp_path):
    write(tmp_path, 'code/pkg/test_check.py', 'from . import helper\n')
    write(tmp_path, 'code/pkg/helper.py', 'from .base import VALUE\n')
    write(tmp_path, 'code/pkg/base.py', 'VALUE = 41\n')
    evidence = tv.gather_evidence(tmp_path, 'T001 Create code/pkg/test_check.py')
    assert 'VALUE = 41' in evidence


def test_absolute_package_import_includes_initializer(tmp_path):
    write(tmp_path, 'tests/test_check.py', 'import pkg.helper\n')
    write(tmp_path, 'code/pkg/__init__.py', 'PACKAGE_POLICY = 42\n')
    write(tmp_path, 'code/pkg/helper.py', 'VALUE = 41\n')
    evidence = tv.gather_evidence(tmp_path, 'T001 Create tests/test_check.py')
    assert 'PACKAGE_POLICY = 42' in evidence and 'VALUE = 41' in evidence


def test_symlink_and_relative_escape_never_read_other_projects(tmp_path):
    project = tmp_path / 'project'
    outside = write(tmp_path, 'secret.py', "SECRET = 'never reveal this content'\n")
    write(project, 'tests/test_check.py', 'import analysis\nfrom ... import secret\n')
    (project / 'analysis.py').symlink_to(outside)
    evidence = tv.gather_evidence(project, 'T001 Create tests/test_check.py')
    assert 'never reveal this content' not in evidence
    assert imports.local_import_evidence(project, [outside]) == ''


def test_cycles_and_declared_sources_not_duplicated(tmp_path):
    write(tmp_path, 'code/a.py', 'import b\n')
    write(tmp_path, 'code/b.py', 'import a\n')
    evidence = tv.gather_evidence(tmp_path, 'T001 Create code/a.py and code/b.py')
    assert 'Local import candidate' not in evidence


def test_missing_dependency_creation_changes_evidence(tmp_path):
    write(tmp_path, 'tests/test_check.py', 'import analysis\n')
    before = tv.gather_evidence(tmp_path, 'T001 Create tests/test_check.py')
    write(tmp_path, 'code/analysis.py', 'VALUE = 1\n')
    after = tv.gather_evidence(tmp_path, 'T001 Create tests/test_check.py')
    assert tv._evidence_hash(before) != tv._evidence_hash(after)


def test_dependency_mutation_invalidates_saved_acceptance(tmp_path, monkeypatch):
    write(tmp_path, 'tests/test_check.py', 'from analysis import VALUE\nassert VALUE == 1\n')
    dependency = write(tmp_path, 'code/analysis.py', 'VALUE = 1\n')
    tasks = write(tmp_path, 'tasks.md', '- [X] T001 Create tests/test_check.py\n')
    calls = []
    def judge(**kwargs):
        calls.append(kwargs['evidence'])
        return tv.TaskVerdict('VALUE = 2' not in kwargs['evidence'], 'checked actual dependency')
    monkeypatch.setattr(tv, 'verify_task', judge)
    def run():
        return tv.run_verification_pass(tmp_path, tasks, already_verified=set(),
            notes_path=tmp_path/'notes.md', state_path=tmp_path/'verify.yaml')
    assert run()['accepted']
    assert run()['accepted']
    assert len(calls) == 1
    dependency.write_text('VALUE = 2\n')
    assert run()['rejected']
    assert len(calls) == 2
    assert '[X]' not in tasks.read_text()


def test_limits_are_explicit_and_do_not_read_unbounded_sources(tmp_path, monkeypatch):
    write(tmp_path, 'tests/test_check.py', 'import a\nimport b\n')
    write(tmp_path, 'code/a.py', 'VALUE = 1\n')
    write(tmp_path, 'code/b.py', 'VALUE = 2\n')
    monkeypatch.setattr(imports, 'MAX_DEPENDENCY_FILES', 1)
    evidence = tv.gather_evidence(tmp_path, 'T001 Create tests/test_check.py')
    assert evidence.count('Local import candidate') == 1
    assert 'NOT INSPECTED beyond the file limit' in evidence


def test_invalid_python_remains_evidence_not_executed(tmp_path):
    write(tmp_path, 'tests/test_check.py', 'import analysis\n')
    write(tmp_path, 'code/analysis.py', 'def malformed(:\n')
    evidence = tv.gather_evidence(tmp_path, 'T001 Create tests/test_check.py')
    assert 'def malformed(:' in evidence
    assert 'NOT INSPECTED (unreadable/invalid Python)' in evidence


def test_candidate_and_parse_budgets_report_partial_context(tmp_path, monkeypatch):
    write(tmp_path, 'tests/test_check.py', 'import x\n')
    write(tmp_path, 'code/x.py', 'VALUE = 1\n' * 10)
    task = 'T001 Create tests/test_check.py'
    monkeypatch.setattr(imports, 'MAX_IMPORT_CANDIDATES', 0)
    assert 'NOT INSPECTED beyond the candidate limit' in tv.gather_evidence(tmp_path, task)
    monkeypatch.setattr(imports, 'MAX_IMPORT_CANDIDATES', 256)
    monkeypatch.setattr(imports, 'MAX_PARSE_BYTES', 20)
    evidence = tv.gather_evidence(tmp_path, task)
    assert 'Local import candidate `code/x.py`' in evidence
    assert 'NOT INSPECTED (source size limit)' in evidence


def test_cyclic_dependency_symlink_does_not_crash_collector(tmp_path):
    write(tmp_path, 'code/main.py', 'import analysis\n')
    (tmp_path / 'code/analysis.py').symlink_to('analysis.py')
    evidence = tv.gather_evidence(tmp_path, 'T001 Create code/main.py')
    assert 'dependency NOT INSPECTED (unreadable path)' in evidence
    assert 'import analysis' in evidence
