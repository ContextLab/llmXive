"""A reply whose YAML broke is recovered, or the model is told what broke.

The fixture is a real reply (PROJ-9999 canary, 2026-10-11, gemma-4, task T010),
kept byte for byte. It is a complete runnable artifact -- ``path``, ``execute``,
``args``, ``timeout_s``, ``contents`` -- whose Python holds a Markdown paper in a
triple-quoted string written flush left. Those lines end the YAML block scalar,
so strict parsing fails. The fallback only matched ``path:`` followed DIRECTLY
by ``contents:``, recovered nothing, and the model was told it "supplied no
writable artifacts". It sent the same reply eleven times; the task cap was
exhausted and the project was kicked back to ``clarified`` with 9 of 12 tasks
done.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from llmxive.backends.base import ChatResponse
from llmxive.speckit.implement_cmd import ImplementerAgent, _regex_parse_implementer
from llmxive.speckit.yaml_extract import parse_yaml_lenient

REPLY = (Path(__file__).resolve().parents[1] / "fixtures" / "implementer"
         / "canary_markdown_in_python_reply.txt").read_text(encoding="utf-8")


def _write(tmp_path, text):
    project = tmp_path / "projects" / "PROJ-901-reply"
    feature = project / "specs" / "001-study"
    feature.mkdir(parents=True)
    tasks = feature / "tasks.md"
    tasks.write_text("- [ ] T010 Write the methods-results paper\n", encoding="utf-8")
    ImplementerAgent().write_artifacts(
        SimpleNamespace(project_dir=project, project_id=project.name),
        {"tasks_path": str(tasks), "feature_dir": str(feature),
         "next_task_id": "T010", "all_complete": False},
        ChatResponse(text=text, model="test", backend="dartmouth"))
    log = project / "code" / ".tasks" / "T010.artifact-write.log"
    return project, tasks, (log.read_text(encoding="utf-8") if log.is_file() else "")


def test_the_real_reply_is_not_valid_yaml() -> None:
    """The premise: if this ever parses, the fixture no longer tests the fallback."""
    with pytest.raises(yaml.YAMLError):
        parse_yaml_lenient(REPLY)


def test_the_fallback_recovers_the_artifact_and_its_execution_fields() -> None:
    doc = _regex_parse_implementer(REPLY)
    assert doc is not None and (doc["task_id"], doc["verdict"]) == ("T010", "completed")
    (artifact,) = doc["artifacts"]
    assert artifact["path"] == "code/totient_census/generate_paper.py"
    assert (artifact["execute"], artifact["args"], artifact["timeout_s"]) == (True, [], 300)
    lines = artifact["contents"].splitlines()
    assert lines[0] == "import pandas as pd"
    assert "from llmxive_toolkit import paths, get_logger" in lines
    # The flush-left Markdown that broke the YAML is content, kept as written.
    assert "## 1. Methodology" in lines and "## References" in lines
    assert lines[-1] == "    generate_writeup()"


def test_the_model_is_told_the_real_defect_not_that_it_sent_nothing(tmp_path) -> None:
    """The recovered Python has an f-string error of its own. That is what the
    model must hear: a line number it can fix, not a message it cannot act on."""
    project, tasks, log = _write(tmp_path, REPLY)
    assert "supplied no writable artifacts" not in log
    assert "SyntaxError" in log and "generate_paper.py" in log
    assert not (project / "code" / "totient_census" / "generate_paper.py").exists()
    assert "- [ ] T010" in tasks.read_text(encoding="utf-8"), "an unwritten task is not complete"


def test_a_recovered_artifact_that_is_sound_is_written_and_run(tmp_path) -> None:
    reply = (
        "```yaml\n"
        "task_id: T010\n"
        "verdict: completed\n"
        "artifacts:\n"
        "  - path: code/make_note.py\n"
        "    execute: true\n"
        "    args: []\n"
        "    timeout_s: 120\n"
        "    contents: |\n"
        "      from pathlib import Path\n"
        "      TEXT = \"\"\"# Note\n"
        "\n"
        "flush-left body: with a colon\n"
        "\"\"\"\n"
        "      Path('data').mkdir(exist_ok=True)\n"
        "      Path('data/note.md').write_text(TEXT)\n"
        "```\n"
    )
    with pytest.raises(yaml.YAMLError):
        parse_yaml_lenient(reply)
    project, tasks, log = _write(tmp_path, reply)
    assert log == "", log
    assert (project / "data" / "note.md").read_text(encoding="utf-8") == "# Note\n\nflush-left body: with a colon\n"
    assert "- [X] T010" in tasks.read_text(encoding="utf-8")


def test_when_nothing_can_be_recovered_the_yaml_error_is_reported(tmp_path) -> None:
    reply = (
        "task_id: T010\n"
        "verdict: completed\n"
        "artifacts:\n"
        "  - file: code/x.py\n"
        "    contents: |\n"
        "      print('x')\n"
        "broken: [unclosed\n"
    )
    _project, tasks, log = _write(tmp_path, reply)
    assert "supplied no writable artifacts" in log
    assert "not valid YAML" in log and "EVERY line must be indented" in log
    assert "- [ ] T010" in tasks.read_text(encoding="utf-8")


def test_a_valid_reply_with_no_artifacts_keeps_the_plain_message(tmp_path) -> None:
    _project, _tasks, log = _write(tmp_path, "task_id: T010\nverdict: completed\nartifacts: []\n")
    assert "supplied no writable artifacts" in log and "not valid YAML" not in log
