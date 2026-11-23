"""The feature directory has one name (PROJ-9999 canary, 2026-10-11)."""

from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from llmxive.backends.base import ChatResponse
from llmxive.speckit.feature_slug import canonicalize_feature_branch, canonicalize_feature_refs
from llmxive.speckit.implement_cmd import ImplementerAgent

REAL = "001-totient-canary"
INVENTED = "001-finite-range-residue-imbalance-eulers-totient"


@pytest.fixture
def project(tmp_path: Path) -> Path:
    proj = tmp_path / "projects" / "PROJ-901-slug"
    (proj / "specs" / REAL / "contracts").mkdir(parents=True)
    (proj / "specs" / REAL / "contracts" / "counts.schema.yaml").write_text("type: object\n", encoding="utf-8")
    return proj


def test_an_invented_slug_in_a_path_becomes_the_real_one(project: Path) -> None:
    code = f'SCHEMA = ROOT / "specs/{INVENTED}/contracts/counts.schema.yaml"\n'
    assert canonicalize_feature_refs(code, project, REAL) == (
        f'SCHEMA = ROOT / "specs/{REAL}/contracts/counts.schema.yaml"\n')


def test_a_slug_with_a_real_directory_is_left_alone(project: Path) -> None:
    """A re-specified project has both; the older reference names something real."""
    (project / "specs" / "002-second-study").mkdir()
    text = f"see specs/{REAL}/spec.md and specs/002-second-study/spec.md and specs/README.md\n"
    assert canonicalize_feature_refs(text, project, "002-second-study") == text


def test_the_spec_names_the_real_branch_everywhere(project: Path) -> None:
    spec = (f"# Feature Specification\n\n**Feature Branch**: `{INVENTED}`\n**Created**: 2026-10-11\n\n"
            f"Contracts live in `specs/{INVENTED}/contracts/`. Branch {INVENTED} is checked out.\n"
            f"An unrelated word: {INVENTED}-extra stays.\n")
    out = canonicalize_feature_branch(spec, project, REAL)
    assert f"**Feature Branch**: `{REAL}`" in out
    assert f"`specs/{REAL}/contracts/`" in out and f"Branch {REAL} is checked out." in out
    assert f"{INVENTED}-extra stays." in out
    assert out.count(INVENTED) == 1


def test_a_spec_already_naming_the_real_branch_is_unchanged(project: Path) -> None:
    spec = f"**Feature Branch**: `{REAL}`\n\nsee specs/{REAL}/plan.md\n"
    assert canonicalize_feature_branch(spec, project, REAL) == spec


def test_the_implementer_writes_code_that_finds_the_contract(project: Path) -> None:
    """End to end: the script the canary could not run, written and executed."""
    feature = project / "specs" / REAL
    tasks = feature / "tasks.md"
    tasks.write_text("- [ ] T009 Export and validate against the contract\n", encoding="utf-8")
    script = (
        "from pathlib import Path\n"
        "root = Path(__file__).resolve().parents[1]\n"
        f"schema = root / 'specs/{INVENTED}/contracts/counts.schema.yaml'\n"
        "out = root / 'data' / 'schema_seen.txt'\n"
        "out.parent.mkdir(exist_ok=True)\n"
        "out.write_text(schema.read_text())\n"
    )
    document = {"task_id": "T009", "verdict": "completed", "artifacts": [
        {"path": "code/exports.py", "execute": True, "args": [], "contents": script}]}
    ImplementerAgent().write_artifacts(
        SimpleNamespace(project_dir=project, project_id=project.name),
        {"tasks_path": str(tasks), "feature_dir": str(feature),
         "next_task_id": "T009", "all_complete": False},
        ChatResponse(text=yaml.safe_dump(document), model="test", backend="dartmouth"))
    assert f"specs/{REAL}/contracts" in (project / "code" / "exports.py").read_text(encoding="utf-8")
    assert (project / "data" / "schema_seen.txt").read_text(encoding="utf-8") == "type: object\n"
    assert "- [X] T009" in tasks.read_text(encoding="utf-8")
    assert not (project / "specs" / INVENTED).exists()
