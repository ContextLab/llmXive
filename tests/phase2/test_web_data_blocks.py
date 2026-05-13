"""Real-fixture tests for the new web/data/projects.json blocks (FR-003/004/006).

`agents[]` (E1), `pipeline_steps[]` (E2), and per-project `current_artifact`
(E3) — built from agents/registry.yaml + the pipeline-stage definitions + the
real project state. No mocks (Constitution III).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from llmxive.web_data import build_payload

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def payload() -> dict:
    return build_payload(REPO_ROOT)


@pytest.fixture(scope="module")
def registry() -> dict:
    return yaml.safe_load((REPO_ROOT / "agents" / "registry.yaml").read_text(encoding="utf-8"))


# --- agents[] (E1) ----------------------------------------------------------

def test_agents_block_one_per_registry_entry(payload, registry):
    reg_names = {a["name"] for a in registry["agents"]}
    block_names = {a["name"] for a in payload["agents"]}
    assert block_names == reg_names


def test_agents_prompt_paths_exist_and_urls_well_formed(payload):
    for a in payload["agents"]:
        pp = a.get("prompt_path")
        assert pp, f"agent {a['name']} has no prompt_path"
        assert (REPO_ROOT / pp).exists(), f"missing prompt file: {pp}"
        assert a["prompt_github_url"] == f"https://github.com/ContextLab/llmXive/blob/main/{pp}"
        assert a["prompt_raw_url"] == f"https://raw.githubusercontent.com/ContextLab/llmXive/main/{pp}"
        assert a["registry_github_url"].endswith("/agents/registry.yaml")
        assert isinstance(a["tools"], list)
        assert isinstance(a["inputs"], list) and isinstance(a["outputs"], list)


# --- pipeline_steps[] (E2) --------------------------------------------------

def test_pipeline_steps_well_formed(payload):
    steps = payload["pipeline_steps"]
    assert steps, "expected pipeline_steps"
    seen_keys = set()
    for s in steps:
        assert s["key"] and s["key"] not in seen_keys
        seen_keys.add(s["key"])
        assert s["lane"] in ("research", "paper")
        assert isinstance(s["order"], int)
        assert s["name"] and s["description"]
        assert isinstance(s["inputs"], list) and isinstance(s["outputs"], list)
        assert isinstance(s["agents"], list)
        assert isinstance(s["example_artifacts"], list)


def test_pipeline_step_agents_subset_of_agents_block(payload):
    agent_names = {a["name"] for a in payload["agents"]}
    for s in payload["pipeline_steps"]:
        for an in s["agents"]:
            assert an in agent_names, f"step {s['key']} references unknown agent {an}"


def test_pipeline_step_example_artifacts_reference_real_projects(payload):
    project_ids = {p["id"] for p in payload["projects"]}
    for s in payload["pipeline_steps"]:
        for ex in s["example_artifacts"]:
            assert ex["project_id"] in project_ids
            assert ex["title"]
            assert ex["github_url"].startswith("https://github.com/ContextLab/llmXive/")


def test_both_lanes_represented(payload):
    lanes = {s["lane"] for s in payload["pipeline_steps"]}
    assert lanes == {"research", "paper"}


# --- per-project current_artifact (E3) --------------------------------------

def test_current_artifact_shape(payload):
    valid_types = {"pdf", "markdown", "latex", "json", "yaml", "none"}
    for p in payload["projects"]:
        ca = p.get("current_artifact")
        assert ca is not None, f"project {p['id']} missing current_artifact"
        assert ca["type"] in valid_types, ca
        if ca["type"] == "none":
            assert ca["repo_path"] is None
            assert ca["github_url"] is None and ca["raw_url"] is None
        else:
            assert ca["repo_path"], ca
            assert (REPO_ROOT / ca["repo_path"]).exists(), f"{p['id']}: {ca['repo_path']} missing"
            assert ca["github_url"].endswith(ca["repo_path"])
            assert ca["raw_url"].endswith(ca["repo_path"])


def test_current_artifact_pdf_iff_published_pdf(payload):
    for p in payload["projects"]:
        ca = p["current_artifact"]
        has_pdf = bool((p.get("artifact_links") or {}).get("paper_pdf"))
        assert (ca["type"] == "pdf") == has_pdf, (p["id"], ca["type"], has_pdf)
