"""Contract test (T035): every schema validates a known-good fixture object."""

from __future__ import annotations

from llmxive.contract_validate import list_contracts, validate


GOOD: dict[str, object] = {
    "agent-registry": {
        "version": "0.1.0",
        "backends": [
            {
                "name": "dartmouth",
                "kind": "openai_compatible",
                "auth_env_vars": ["DARTMOUTH_CHAT_API_KEY"],
                "is_paid": False,
            }
        ],
        "agents": [],
    },
    "citation": {
        "cite_id": "c-001",
        "artifact_path": "projects/PROJ-001-x/idea/main.md",
        "artifact_hash": "0" * 64,
        "kind": "url",
        "value": "https://example.com",
        "verification_status": "pending",
    },
    "project-state": {
        "id": "PROJ-001-example",
        "title": "Example",
        "field": "example",
        "current_stage": "brainstormed",
        "points_research": {},
        "points_paper": {},
        "created_at": "2026-04-28T00:00:00Z",
        "updated_at": "2026-04-28T00:00:00Z",
        "artifact_hashes": {},
    },
    "review-record": {
        "reviewer_name": "research_reviewer",
        "reviewer_kind": "llm",
        "artifact_path": "projects/PROJ-001-x/code/main.py",
        "artifact_hash": "a" * 64,
        "score": 0.5,
        "verdict": "accept",
        "feedback": "looks good",
        "reviewed_at": "2026-04-28T00:00:00Z",
        "prompt_version": "1.0.0",
        "model_name": "test-model",
        "backend": "dartmouth",
    },
    "run-log-entry": {
        "run_id": "11111111-1111-1111-1111-111111111111",
        "entry_id": "22222222-2222-2222-2222-222222222222",
        "agent_name": "specifier",
        "project_id": "PROJ-001-example",
        "task_id": "33333333-3333-3333-3333-333333333333",
        "inputs": [],
        "outputs": [],
        "backend": "dartmouth",
        "model_name": "test-model",
        "prompt_version": "1.0.0",
        "started_at": "2026-04-28T00:00:00Z",
        "ended_at": "2026-04-28T00:00:01Z",
        "outcome": "success",
        "cost_estimate_usd": 0.0,
    },
    "web-data": {
        "generated_at": "2026-04-28T00:00:00Z",
        "schema_version": "1.0.0",
        "projects": [],
    },
}


def test_every_schema_validates_a_known_good_fixture() -> None:
    contracts = list_contracts()
    assert set(contracts) == set(GOOD.keys()), (
        f"contracts/ vs fixtures mismatch: {set(contracts) ^ set(GOOD.keys())}"
    )
    for name, obj in GOOD.items():
        validate(name, obj)
