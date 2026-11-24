"""
Integration test for the full inference pipeline (User Story 1, T010).

Test-first contract: these tests define the required behavior of the
CPU-only inference runner to be implemented in T014
(``code/inference/runner.py``). Until T014 lands, the import below
fails loudly with an actionable message instead of silently skipping.

Covered requirements:
  - FR-002: CPU-only inference, batch_size=1, temperature=0.7
  - FR-003: up to 3 distinct candidates for ill-structured prompts,
            "incomplete" flag when fewer than 3 distinct valid responses
  - FR-006: hard max_tokens limit (2048); truncation recorded, not crash
"""
import json
import sys
from pathlib import Path

import pytest

# Make code/ importable when pytest runs from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

try:
    from inference.runner import run_inference  # noqa: F401
except ImportError as exc:  # pragma: no cover - guards TDD ordering
    pytest.fail(
        "code/inference/runner.py (T014) is not implemented yet; "
        "the inference pipeline integration test cannot run. "
        f"ImportError: {exc}"
    )

from inference.runner import run_inference


@pytest.fixture
def sample_prompts(tmp_path):
    """Small fixture of unified-format prompts (structure per T013)."""
    prompts = [
        {
            "prompt_id": "mmlu-0001",
            "prompt": "What is 2 + 2? Answer with a single integer.",
            "domain": "deterministic",
            "source": "mmlu_stem",
        },
        {
            "prompt_id": "mmlu-0002",
            "prompt": "Which planet is closest to the Sun?",
            "domain": "deterministic",
            "source": "mmlu_stem",
        },
        {
            "prompt_id": "opensci-0001",
            "prompt": "Propose an experimental design to test whether "
                      "microgravity affects bacterial antibiotic resistance.",
            "domain": "ill-structured",
            "source": "opensci_reason",
        },
        {
            "prompt_id": "opensci-0002",
            "prompt": "Suggest multiple plausible hypotheses for why a "
                      "robotic rover's spectrometer drifts over time.",
            "domain": "ill-structured",
            "source": "opensci_reason",
        },
    ]
    path = tmp_path / "unified_sample.jsonl"
    with open(path, "w", encoding="utf-8") as fh:
        for row in prompts:
            fh.write(json.dumps(row) + "\n")
    return path

def _load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def test_pipeline_produces_valid_jsonl(sample_prompts, tmp_path):
    """End-to-end: runner consumes unified JSONL and writes valid JSONL."""
    output = tmp_path / "responses.jsonl"
    result = run_inference(
        input_path=str(sample_prompts),
        output_path=str(output),
        model_name="baseline",
        temperature=0.7,
        max_tokens=2048,
        num_candidates=3,
    )
    assert output.exists(), "inference runner must write its output file"
    assert result is not None
    rows = _load_jsonl(output)
    assert len(rows) > 0, "output JSONL must not be empty"
    for row in rows:
        assert "prompt_id" in row
        assert "response" in row
        assert isinstance(row["response"], str)
        assert len(row["response"]) > 0, "responses must be non-empty text"
        assert row.get("temperature") == 0.7
        assert row.get("max_tokens") == 2048

def test_deterministic_prompts_single_response(sample_prompts, tmp_path):
    """FR-002/plan: deterministic (MMLU-STEM) prompts get 1 response."""
    output = tmp_path / "responses_det.jsonl"
    run_inference(
        input_path=str(sample_prompts),
        output_path=str(output),
        model_name="baseline",
        temperature=0.7,
        max_tokens=2048,
        num_candidates=3,
    )
    rows = _load_jsonl(output)
    det_rows = [r for r in rows if r.get("domain") == "deterministic"]
    assert det_rows, "deterministic prompts must appear in output"
    by_prompt = {}
    for r in det_rows:
        by_prompt.setdefault(r["prompt_id"], []).append(r)
    for pid, group in by_prompt.items():
        assert len(group) == 1, (
            f"deterministic prompt {pid} must generate exactly 1 "
            f"response, got {len(group)}"
        )

def test_ill_structured_prompts_up_to_3_candidates(sample_prompts, tmp_path):
    """FR-003: ill-structured prompts generate up to 3 candidates and
    are flagged 'incomplete' when fewer than 3 distinct valid responses
    are produced."""
    output = tmp_path / "responses_open.jsonl"
    run_inference(
        input_path=str(sample_prompts),
        output_path=str(output),
        model_name="baseline",
        temperature=0.7,
        max_tokens=2048,
        num_candidates=3,
    )
    rows = _load_jsonl(output)
    open_rows = [r for r in rows if r.get("domain") == "ill-structured"]
    assert open_rows, "ill-structured prompts must appear in output"
    by_prompt = {}
    for r in open_rows:
        by_prompt.setdefault(r["prompt_id"], []).append(r)
    for pid, group in by_prompt.items():
        responses = [r["response"] for r in group]
        n_valid = len([r for r in responses if r and r.strip()])
        if n_valid < 3:
            assert any(
                r.get("status") == "incomplete" for r in group
            ), (
                f"prompt {pid} produced {n_valid} < 3 valid responses and "
                "must be flagged 'incomplete' (FR-003)"
            )
        else:
            assert all(
                r.get("status") != "incomplete" for r in group
            ), f"prompt {pid} has 3 valid responses; must not be incomplete"

def test_max_tokens_enforced_no_crash(sample_prompts, tmp_path):
    """FR-006: a small max_tokens limit must not crash the pipeline;
    generation is bounded and recorded."""
    output = tmp_path / "responses_small.jsonl"
    run_inference(
        input_path=str(sample_prompts),
        output_path=str(output),
        model_name="baseline",
        temperature=0.7,
        max_tokens=16,
        num_candidates=1,
    )
    assert output.exists()
    rows = _load_jsonl(output)
    assert len(rows) > 0, "pipeline must complete even with tight token limit"

def test_cpu_only_no_cuda_dependency(sample_prompts, tmp_path):
    """FR-002: pipeline must run without CUDA; no torch.cuda calls."""
    import torch

    if not torch.cuda.is_available():
        # Expected environment: CPU-only runner; the pipeline must
        # succeed without ever touching CUDA.
        output = tmp_path / "responses_cpu.jsonl"
        run_inference(
            input_path=str(sample_prompts),
            output_path=str(output),
            model_name="baseline",
            temperature=0.7,
            max_tokens=2048,
            num_candidates=1,
        )
        assert output.exists()
    else:
        pytest.skip("CUDA available; CPU-only path not exercised")