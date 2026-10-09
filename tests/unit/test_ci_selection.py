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
    selected = load("select_checks").select([path])
    assert selected["offline"] == offline
    assert selected["live"] == live


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


@pytest.mark.parametrize("path,required", [
    ("src/llmxive/librarian/verify.py", True),
    ("agents/tools/citation_fetcher.py", True),
    ("src/llmxive/state/_io.py", True),
    ("src/llmxive/state/citations.py", True),
    ("src/llmxive/state/claims.py", True),
    ("src/llmxive/state/results.py", True),
    ("src/llmxive/state/execution_status.py", False),
    ("src/llmxive/state/unverifiable.py", False),
    ("src/llmxive/state/future_unknown_module.py", True),
    ("agents/prompts/paper_task_implementer.md", False),
    ("agents/prompts/research_reviewer_idea_quality.md", False),
    (".github/workflows/prompt-eval.yml", False),
    ("eval/promptfoo/llmxive_provider.py", False),
    ("eval/promptfoo/assert_review_frontmatter.py", False),
    ("eval/promptfoo/promptfooconfig.yaml", False),
    ("eval/promptfoo/future_unknown_provider.py", True),
    ("agents/prompts/future_unknown_prompt.md", True),
    ("src/llmxive/config.py", True),
    ("contracts/citation.schema.json", True),
    ("tests/real_call/test_resolve_reference_registrar_agnostic.py", True),
    ("web/about.html", True),
    ("pyproject.toml", True),
    ("requirements.lock", True),
    ("tests/conftest.py", True),
    ("src/llmxive/future_unknown_module.py", True),
    ("future_runtime/input.yaml", True),
    ("src/llmxive/speckit/paper_implement_cmd.py", False),
    ("src/llmxive/backends/router.py", True),
    ("scripts/ci/select_checks.py", False),
    ("scripts/ci/verify-audit-corpus.py", False),
    (".github/workflows/audit.yml", False),
    (".github/workflows/llmxive-real-call-tests.yml", False),
    ("tests/unit/test_ci_selection.py", False),
], ids=lambda value: value.replace("/", "_") if isinstance(value, str) else None)
def test_external_references_follow_changed_dependencies(path, required):
    assert load("select_checks").select([path])["references"] is required


def test_known_runtime_verifier_keeps_live_checks_but_unknown_modules_stay_conservative():
    select = load("select_checks").select
    assert select(["tests/real_call/test_task_verifier_paths.py"]) == {
        "offline": True, "live": True, "references": False,
    }
    assert select(["tests/real_call/test_future_module.py"]) == {
        "offline": True, "live": True, "references": True,
    }


@pytest.mark.parametrize("path", [
    "projects/PROJ-715/specs/001-study/API_analysis.case-preserved.md",
    "projects/PROJ-715/specs/001-study/README.md",
    "projects/PROJ-008/.gitattributes",
    ".github/workflows/repair.yml",
])
def test_project_documentation_and_repair_routing_keep_runtime_coverage(path):
    assert load("select_checks").select([path]) == {
        "offline": True, "live": True, "references": False,
    }


PRODUCTION_ROUTING = [
    ".github/workflows/maintenance.yml", ".github/workflows/submission-intake.yml",
    ".github/workflows/paper-compile.yml", ".github/workflows/reprocess.yml",
    ".github/workflows/pages.yml", "scripts/ci/reprocess_queue.py",
]


@pytest.mark.parametrize("path", PRODUCTION_ROUTING)
def test_production_queue_and_checkout_routing_keeps_dartmouth(path):
    assert load("select_checks").select([path]) == {
        "offline": True, "live": True, "references": False,
    }


@pytest.mark.parametrize("reference_input", [
    "src/llmxive/librarian/verify.py", "pyproject.toml",
    "tests/real_call/test_resolve_reference_registrar_agnostic.py",
])
def test_mixed_production_routing_and_reference_edits_retain_all_checks(reference_input):
    assert load("select_checks").select([*PRODUCTION_ROUTING, reference_input]) == {
        "offline": True, "live": True, "references": True,
    }


@pytest.mark.parametrize("path", [
    "projects/PROJ-715/code/main.py", "projects/PROJ-715/requirements.txt",
    "projects/PROJ-715/config.yaml", "projects/PROJ-715/contracts/result.schema.json",
    "tests/fixtures/reference.md", "projects/unclassified/README.md",
    ".github/workflows/future.yml",
    "scripts/ci/future_queue.py",
])
def test_unknown_project_and_platform_inputs_keep_external_coverage(path):
    assert load("select_checks").select([path]) == {
        "offline": True, "live": True, "references": True,
    }


def test_reference_local_import_closure_stays_in_selected_paths():
    """Includes function-local imports and package initialization, not just top-level imports."""
    import ast

    selection = load("select_checks")
    modules = {}
    for directory in (ROOT / "src/llmxive", ROOT / "agents/tools"):
        for path in directory.rglob("*.py"):
            relative = path.relative_to(ROOT / "src" if path.is_relative_to(ROOT / "src") else ROOT)
            name = ".".join(relative.with_suffix("").parts)
            if name.endswith(".__init__"):
                name = name.removesuffix(".__init__")
            modules[name] = path
    pending = [ROOT / p for p in selection.REFERENCE_TESTS]
    visited = set()
    while pending:
        path = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        assert selection.needs_references(path.relative_to(ROOT).as_posix()), path
        # A reviewed runtime-only prompt must not become an input to an
        # external-service dependency without being reclassified.
        literals = {node.value for node in ast.walk(ast.parse(path.read_text()))
                    if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        assert not (literals & selection.RUNTIME_PROMPTS)
        assert not (literals & set(PRODUCTION_ROUTING))
        name = next((n for n, p in modules.items() if p == path), "")
        package = name if path.name == "__init__.py" else name.rpartition(".")[0]
        for node in ast.walk(ast.parse(path.read_text())):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    base = importlib.util.resolve_name("." * node.level + base, package)
                names = [base, *(base + "." + alias.name for alias in node.names)]
            for imported in names:
                parts = imported.split(".")
                for i in range(1, len(parts) + 1):
                    local = modules.get(".".join(parts[:i]))
                    if local is not None:
                        pending.append(local)
    assert ROOT / "agents/tools/citation_fetcher.py" in visited
    assert ROOT / "src/llmxive/librarian/verify.py" in visited


def test_fast_collection_is_exact_partition_and_nightly_keeps_references():
    import shlex

    import yaml

    def collect(marker):
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/real_call", "--collect-only", "-q", "-m", marker],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        return {line for line in result.stdout.splitlines() if line.startswith("tests/real_call/") and "::" in line}

    workflow = yaml.safe_load((ROOT / ".github/workflows/llmxive-real-call-tests.yml").read_text())

    def workflow_marker(job):
        command = next(step["run"] for step in workflow["jobs"][job]["steps"]
                       if step.get("run", "").startswith("pytest tests/real_call"))
        args = shlex.split(command)
        return args[args.index("-m") + 1]

    all_fast = collect("not slow")
    runtime = collect(workflow_marker("dartmouth"))
    references = collect(workflow_marker("references"))
    assert runtime and references and not (runtime & references)
    assert runtime | references == all_fast
    assert any("test_dartmouth_real_chat[configured-primary]" in node for node in runtime)
    assert any("test_resolve_reference_present_for_every_service[zenodo" in node for node in references)
    assert {node.split("::")[0] for node in references} == load("select_checks").REFERENCE_TESTS
    runtime_modules = load("select_checks").RUNTIME_TESTS
    assert runtime_modules <= {node.split("::")[0] for node in runtime}
    assert runtime_modules.isdisjoint({node.split("::")[0] for node in references})
    assert any(step.get("run") == "pytest tests/contract -v"
               for step in workflow["jobs"]["dartmouth"]["steps"])
    assert "references" in workflow["jobs"]["real-call"]["needs"]
    nightly = yaml.safe_load((ROOT / ".github/workflows/llmxive-real-call-nightly.yml").read_text())
    commands = [step.get("run", "") for job in nightly["jobs"].values() for step in job["steps"]]
    assert "pytest tests/real_call -v" in commands  # no exclusion of the new marker


@pytest.mark.parametrize("pages", [[], [[]], [[{"filename": "notes/x"}] * 3000],
    [[{"filename": "notes/renamed.md", "previous_filename": "src/llmxive/librarian/verify.py"}]]])
def test_ambiguous_lists_and_reference_renames_keep_external_gate(pages, tmp_path):
    import os

    source = tmp_path / "files.json"
    source.write_text(json.dumps(pages))
    output = tmp_path / "output"
    subprocess.run([sys.executable, str(ROOT / "scripts/ci/select_checks.py"), str(source)],
                   env={**os.environ, "GITHUB_OUTPUT": str(output)}, check=True)
    assert "references=true" in output.read_text()


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


def test_paper_bootstrap_live_test_keeps_dartmouth_without_external_services():
    assert load("select_checks").select(["tests/real_call/test_paper_bootstrap.py"]) == {
        "offline": True, "live": True, "references": False,
    }


@pytest.mark.parametrize('path', [
    'tests/integration/test_task_review_contract_context.py',
    'tests/integration/test_tasker_engine_bridge.py',
    'tests/integration/test_tasker_production_cutover.py',
])
def test_reviewed_task_integration_modules_keep_offline_and_dartmouth(path):
    selector = load('select_checks')
    assert selector.select([path]) == {'offline': True, 'live': True, 'references': False}
    for guarded in ('tests/integration/test_unknown_future.py', 'tests/conftest.py',
                    'tests/real_call/test_resolve_reference_registrar_agnostic.py',
                    'src/llmxive/agents/reference_validator.py'):
        assert selector.select([path, guarded]) == {'offline': True, 'live': True, 'references': True}
