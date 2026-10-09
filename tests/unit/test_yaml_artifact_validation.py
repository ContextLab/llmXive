"""Malformed YAML cannot retain a semantic completion receipt."""

import pytest
import yaml

from llmxive.agents import task_verifier as tv


@pytest.mark.parametrize("suffix", ["yaml", "yml"])
def test_yaml_syntax_is_checked_by_its_reader(tmp_path, suffix):
    target = tmp_path / f"manifest.{suffix}"
    target.write_text(r"git_commit: abc\nfiles:\n  data/result.csv: deadbeef\n")
    assert not tv._artifact_valid(tmp_path, target.name)
    target.write_text("git_commit: abc\nfiles:\n  data/result.csv: deadbeef\n")
    assert tv._artifact_valid(tmp_path, target.name)


@pytest.mark.parametrize(
    "contents", ["# only a comment\n", "[unterminated", "field: !!python/object:os.system {}"]
)
def test_unreadable_or_empty_yaml_is_not_completion_evidence(tmp_path, contents):
    (tmp_path / "config.yaml").write_text(contents)
    assert not tv._artifact_valid(tmp_path, "config.yaml")


def test_valid_multiple_documents_and_literal_backslashes_remain_supported(tmp_path):
    (tmp_path / "config.yaml").write_text("pattern: '\\d+\\n'\n---\nenabled: false\n")
    assert tv._artifact_valid(tmp_path, "config.yaml")


def test_legacy_positive_receipt_cannot_accept_malformed_yaml(tmp_path, monkeypatch):
    project = tmp_path / "projects/PROJ-test"
    feature = project / "specs/001-test"
    feature.mkdir(parents=True)
    manifest = project / "state/projects/PROJ-test.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(r"git_commit: abc\nfiles:\n  data/result.csv: deadbeef\n")
    definition = "T001 Generate state/projects/PROJ-test.yaml"
    tasks = feature / "tasks.md"
    tasks.write_text(f"- [X] {definition}\n")
    memory = project / ".specify/memory"
    memory.mkdir(parents=True)
    digest = tv._evidence_hash(definition + "\n\n" + tv.gather_evidence(project, definition))
    (memory / "task_verify_cache.yaml").write_text(
        yaml.safe_dump({"T001": {"c": True, "h": digest, "r": "old false approval"}})
    )
    assert tv.verified_done_keys(project, tasks) == set()

    def forbidden(**kwargs):
        pytest.fail("Malformed YAML must fail before a model call or cached approval")

    monkeypatch.setattr(tv, "verify_task", forbidden)
    result = tv.run_verification_pass(
        project,
        tasks,
        already_verified=set(),
        state_path=memory / "task_verify.yaml",
        notes_path=memory / "notes.md",
    )
    assert result["rejected"][0][0] == "T001"
    assert "invalid" in result["rejected"][0][1]
    assert "- [ ] T001" in tasks.read_text()
