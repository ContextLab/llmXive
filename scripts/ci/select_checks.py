"""Conservative PR check selection; unknown paths always retain live coverage."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Actual imports of the external-reference and dataset-service modules include the lazy
# agents.tools.citation_fetcher import in reference_validator. A unit test walks
# that local import closure so new shared dependencies cannot silently escape.
REFERENCE_PREFIXES = (
    "src/llmxive/librarian/", "src/llmxive/claims/",
    "src/llmxive/backends/", "src/llmxive/fill/", "src/llmxive/grounding/",
    "src/llmxive/results/", "src/llmxive/verify/",
    "agents/tools/", "contracts/", "tests/fixtures/",
)
REFERENCE_FILES = {
    # Exact external-service state dependencies; execution/replan state is not
    # imported by these tests. The transitive AST closure guard enforces this.
    "src/llmxive/state/__init__.py", "src/llmxive/state/_io.py",
    "src/llmxive/state/citations.py", "src/llmxive/state/claims.py",
    "src/llmxive/state/results.py",
    "web/about.html",  # config.py reads citation overlap thresholds from this page
    "src/llmxive/agents/citation_guard.py", "src/llmxive/agents/reference_validator.py",
    "src/llmxive/config.py", "src/llmxive/types.py", "src/llmxive/credentials.py",
    "src/llmxive/contract_validate.py", "src/llmxive/agents/grounding_guard.py",
    "src/llmxive/agents/prompts.py", "src/llmxive/speckit/task_lines.py",
}
REFERENCE_TESTS = {
    "tests/real_call/test_dataset_source_services.py",
    "tests/real_call/test_citation_guard_strips_fabrication.py",
    "tests/real_call/test_reference_validator_blocks_fabrication.py",
    "tests/real_call/test_reference_validator_distinguishes_unreachable.py",
    "tests/real_call/test_resolve_reference_registrar_agnostic.py",
}
# Reviewed runtime-only live modules retain Dartmouth coverage. Unknown live
# modules still require external checks until their dependencies are classified.
RUNTIME_TESTS = {
    "tests/real_call/test_task_verifier_paths.py",
    "tests/real_call/test_paper_bootstrap.py",
}
# Reviewed task-pipeline integration modules use isolated fixtures and recording
# backends; they do not exercise/modify external-service availability probes.
# Keep all other integration paths conservative until individually classified.
RUNTIME_INTEGRATION_TESTS = {
    "tests/integration/test_task_review_contract_context.py",
    "tests/integration/test_tasker_engine_bridge.py",
    "tests/integration/test_tasker_production_cutover.py",
}
# These files route/test CI, without changing reference resolution. Their PRs
# must prove selection/collection invariants and still run Dartmouth; requiring
# registrar uptime here does not validate the changed routing behavior.
RUNTIME_PROMPTS = {
    "agents/prompts/paper_task_implementer.md",
    "agents/prompts/research_reviewer_idea_quality.md",
}

ROUTING_FILES = {
    "scripts/ci/select_checks.py", "tests/real_call/conftest.py",
    ".github/workflows/llmxive-real-call-tests.yml",
    ".github/workflows/llmxive-real-call-nightly.yml",
    ".github/workflows/audit.yml", "scripts/ci/verify-audit-corpus.py",
    ".github/workflows/repair.yml",
    ".github/workflows/prompt-eval.yml",
    "eval/promptfoo/llmxive_provider.py",
    "eval/promptfoo/assert_review_frontmatter.py",
    "eval/promptfoo/promptfooconfig.yaml",
    "scripts/verify_root_file_recovery.py",
}

def needs_references(path: str) -> bool:
    if path in REFERENCE_FILES | REFERENCE_TESTS or path.startswith(REFERENCE_PREFIXES):
        return True
    # Package initialization and test harness changes can affect every import.
    if path.endswith("/__init__.py") or path == "tests/conftest.py":
        return True
    if path in ROUTING_FILES | RUNTIME_TESTS | RUNTIME_INTEGRATION_TESTS | RUNTIME_PROMPTS:
        return False
    parts = Path(path).parts
    if (len(parts) >= 3 and parts[0] == "projects" and parts[1].startswith("PROJ-")
            and (path.endswith(".md") or (len(parts) == 3 and parts[-1] == ".gitattributes"))):
        # Registrar availability tests consume fixed service examples, not
        # project documents or project-local checkout attributes. These paths
        # still run offline and Dartmouth checks below; project code and unknown
        # configuration remain conservative.
        return False
    if path.startswith(("tests/unit/", "tests/contract/", "web/", "docs/", "notes/")):
        return False
    if path.startswith("src/llmxive/") and (ROOT / path).is_file():
        return False  # known code outside the guarded reference dependency set
    return True  # unknown paths/dependency manifests remain conservative


def select(paths: list[str]) -> dict[str, bool]:
    offline = live = references = False
    for path in paths:
        # These are audit records or human documentation, never runtime prompts.
        if path in {"README.md", "CLAUDE.md", "AGENTS.md", "LICENSE"}:
            continue
        offline = True
        reference_change = needs_references(path)
        references |= reference_change
        if reference_change:
            live = True
        if path.startswith(("tests/unit/", "tests/contract/", "web/", "docs/", "notes/")):
            continue
        live = True
    return {"offline": offline, "live": live, "references": references}


def main() -> None:
    pages = json.loads(Path(sys.argv[1]).read_text())
    if not isinstance(pages, list) or any(not isinstance(p, list) for p in pages):
        raise ValueError("expected paginated GitHub changed-file arrays")
    paths = []
    for page in pages:
        for item in page:
            paths.append(item["filename"])
            if item.get("previous_filename"):
                paths.append(item["previous_filename"])
    result = select(paths)
    # GitHub limits this endpoint to 3000 files. Never infer a safe skip from
    # an empty/truncated list; a manual dispatch also supplies this sentinel.
    if not paths or sum(map(len, pages)) >= 3000:
        result = {"offline": True, "live": True, "references": True}
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write("".join(f"{key}={str(value).lower()}\n" for key, value in result.items()))
    print(json.dumps({"changed_paths": len(paths), **result}))


if __name__ == "__main__":
    main()
