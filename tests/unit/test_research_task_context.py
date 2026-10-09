"""Replanning sees the current research template and actual failure diagnosis."""
from pathlib import Path
from types import SimpleNamespace

from llmxive.speckit.tasks_cmd import TaskerAgent


def test_replan_uses_current_template_and_preserves_requirements(tmp_path):
    root = Path(__file__).resolve().parents[2]
    project = tmp_path / "projects/PROJ-1"
    feature = project / "specs/001-study"
    feature.mkdir(parents=True)
    (feature / "spec.md").write_text("FR-001: Analyze p=5,7,11 for every specified N.")
    (feature / "plan.md").write_text("Reuse the tested code/src/utils/sieve.py.")
    (feature / "tasks.md").write_text("- [X] T001 Implement code/src/utils/sieve.py\n- [ ] T002 Connect the CLI\n")
    local_template = project / ".specify/templates/tasks-template.md"
    local_template.parent.mkdir(parents=True)
    local_template.write_text("Stale template: build authentication middleware before any analysis")
    for name in (".specify/templates/tasks-template.md", "agents/prompts/tasker.md"):
        dest = tmp_path / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text((root / name).read_text())
    memory = project / ".specify/memory"
    memory.mkdir()
    (memory / "kickback_feedback.md").write_text("T002 failed: CLI imports root/src instead of code/src.")
    (memory / "task_verifier_notes.md").write_text("Preserve the independently verified sieve; fix the CLI import.")
    reviews = project / "reviews/research"
    reviews.mkdir(parents=True)
    (reviews / "reviewer__2026-10-09__research.md").write_text("Report the nonmonotone conditional case honestly.")
    context = SimpleNamespace(project_dir=project, project_id="PROJ-1")
    mechanical = {f"{name}_path": str(feature / f"{name}.md") for name in ("spec", "plan", "tasks")}
    mechanical["tasks_template_path"] = str(local_template)
    messages = TaskerAgent().build_prompt(context, mechanical)
    prompt = messages[1].content
    assert "Stale template" not in prompt
    assert "first end-to-end analysis" in prompt
    assert "T002 failed: CLI imports root/src instead of code/src." in prompt
    assert "Preserve the independently verified sieve; fix the CLI import." in prompt
    assert "Report the nonmonotone conditional case honestly." in prompt
    assert "p=5,7,11 for every specified N" in prompt
    assert "- [X] T001 Implement code/src/utils/sieve.py" in prompt
    assert "code/src/utils/sieve.py" in prompt
    # Minimal standalone project fixtures still support a project-local template.
    (tmp_path / ".specify/templates/tasks-template.md").unlink()
    fallback = TaskerAgent().build_prompt(context, mechanical)
    assert "Stale template" in fallback[1].content


def test_contract_evidence_resolves_active_feature_without_masking_explicit_paths(tmp_path):
    from llmxive.agents.task_verifier import gather_evidence
    from llmxive.project_paths import resolve_project_path

    project = tmp_path / "PROJ-1"
    feature = project / "specs/001-study"
    contract = feature / "contracts/summary.schema.yaml"
    contract.parent.mkdir(parents=True)
    (feature / "spec.md").write_text("The active research specification")
    contract.write_text("type: object\nrequired: [N, p, total_variation]\n")
    task = "T007 Test that generated summary data conforms to contracts/summary.schema.yaml"
    assert "total_variation" in gather_evidence(project, task)
    assert "MISSING" not in gather_evidence(project, task)
    explicit = resolve_project_path(project, "projects/PROJ-1/contracts/summary.schema.yaml")
    assert explicit == project / "contracts/summary.schema.yaml"
    assert not explicit.exists()
    explicit.parent.mkdir()
    explicit.write_text("project root schema takes precedence")
    assert resolve_project_path(project, "contracts/summary.schema.yaml") == explicit
