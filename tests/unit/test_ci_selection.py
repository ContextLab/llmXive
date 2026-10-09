"""CI selection must preserve model coverage and real PDF regression inputs."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/ci/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "path,offline,live",
    [
        ("notes/audit.md", True, False),
        ("README.md", False, False),
        ("tests/unit/test_router.py", True, False),
        ("tests/contract/test_schema.py", True, False),
        ("web/js/app.js", True, False),
        ("docs/index.html", True, False),
        ("agents/prompts/tasker.md", True, True),
        ("agents/registry.yaml", True, True),
        (".specify/templates/tasks-template.md", True, True),
        ("src/llmxive/backends/router.py", True, True),
        ("tests/real_call/conftest.py", True, True),
        ("tests/conftest.py", True, True),
        ("pyproject.toml", True, True),
        ("requirements.lock", True, True),
        (".github/workflows/llmxive-real-call-tests.yml", True, True),
        ("scripts/ci/select_checks.py", True, True),
        ("future_runtime/input.yaml", True, True),
    ],
    ids=lambda value: value.replace("/", "_") if isinstance(value, str) else None,
)
def test_conservative_selection(path, offline, live):
    assert load("select_checks").select([path]) == {"offline": offline, "live": live}


@pytest.mark.parametrize(
    "pages",
    [
        [],
        [[]],
        [[{"filename": "notes/removed.md", "previous_filename": "agents/prompts/old.md"}]],
        [[{"filename": "notes/a.md"}] * 3000],
    ],
)
def test_empty_truncated_or_runtime_rename_cannot_skip_live(pages, tmp_path):
    source = tmp_path / "files.json"
    source.write_text(json.dumps(pages))
    output = tmp_path / "output"
    import os

    subprocess.run(
        [sys.executable, str(ROOT / "scripts/ci/select_checks.py"), str(source)],
        env={**os.environ, "GITHUB_OUTPUT": str(output)},
        check=True,
    )
    assert "offline=true" in output.read_text()
    assert "live=true" in output.read_text()


def test_sparse_checkout_preserves_exact_current_pdf_sample(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for name in ["z.pdf", "a.pdf", "c.pdf", "b.pdf"]:
        path = tmp_path / "docs/papers" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
    template = tmp_path / "projects/PROJ-1/.specify/templates/tasks-template.md"
    template.parent.mkdir(parents=True)
    template.write_text("real shared template")
    dataset = tmp_path / "projects/PROJ-1/data/big.csv"
    dataset.parent.mkdir(parents=True)
    dataset.write_text("large research input")
    test = tmp_path / "tests/unit/test_audit_pdf.py"
    test.parent.mkdir(parents=True)
    test.write_text("_SAMPLE_SIZE = 3\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=CI test",
            "-c",
            "user.email=ci@example.invalid",
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "-qm",
            "fixtures",
        ],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "sparse-checkout", "set", "--no-cone", "/tests/"], cwd=tmp_path, check=True
    )
    assert not (tmp_path / "docs/papers").exists()
    result = load("prepare_test_checkout").prepare(tmp_path)
    assert result == ["docs/papers/a.pdf", "docs/papers/b.pdf", "docs/papers/c.pdf"]
    assert not (tmp_path / "docs/papers/z.pdf").exists()
    assert template.read_text() == "real shared template"
    assert not dataset.exists()
    for name in result:
        assert (tmp_path / name).read_bytes() == Path(name).name.encode()
