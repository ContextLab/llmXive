"""The verifier is told what an image is and what it shows, not its bytes.

2026-10-11: a task requiring "visual verification of the plot" was rejected on
nine of nine attempts for "no evidence the PNG shows ...". The evidence for a
PNG was its first bytes decoded as text.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from llmxive.agents import task_verifier
from llmxive.project_toolkit.llmxive_toolkit.figures import describe, record_path

TASK = "T005 Plot the two TV series in `figures/tv.png`"


def _plot(path: Path, *, record: bool) -> None:
    import json

    fig, ax = plt.subplots()
    ax.plot([1, 10, 100], [0.5, 0.3, 0.1], label="Unconditional TV")
    ax.plot([1, 10, 100], [0.4, 0.2, 0.1], label="Conditional TV")
    ax.set_xscale("log")
    ax.legend()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=50)
    if record:
        record_path(path).write_text(json.dumps({"image": path.name, **describe(fig)}), encoding="utf-8")
    plt.close(fig)


def test_an_image_is_measured_and_its_record_quoted(tmp_path: Path) -> None:
    _plot(tmp_path / "figures/tv.png", record=True)
    evidence = task_verifier.gather_evidence(tmp_path, TASK)
    assert "image measured by the platform: PNG 320x240 px" in evidence
    assert "blank" not in evidence
    assert "as recorded in `tv.figure.json`" in evidence
    assert '"Unconditional TV"' in evidence and '"xscale": "log"' in evidence
    assert "�" not in evidence and "IHDR" not in evidence  # no decoded bytes


def test_a_blank_image_and_a_missing_record_are_said_plainly(tmp_path: Path) -> None:
    fig = plt.figure()
    (tmp_path / "figures").mkdir()
    fig.savefig(tmp_path / "figures/tv.png", dpi=50)
    plt.close(fig)
    evidence = task_verifier.gather_evidence(tmp_path, TASK)
    assert "(a blank or nearly blank image)" in evidence
    assert "no `tv.figure.json` beside it" in evidence


def test_a_file_that_is_not_an_image_is_reported_as_such(tmp_path: Path) -> None:
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures/tv.png").write_text("this is a placeholder, not a plot\n", encoding="utf-8")
    assert "image could NOT be opened as an image" in task_verifier.gather_evidence(tmp_path, TASK)
