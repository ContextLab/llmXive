"""Contract tests for the dataset loader (US1, T009).

These tests define and enforce the *contract* that the dataset
download/loading code (implemented in T011/T012 as
``code/data/download.py``) must satisfy:

* ``code/data/processed/mmlu_stem.jsonl`` records conform to the
  deterministic-benchmark schema (id, prompt, answer, choices).
* ``code/data/processed/opensci_reason.jsonl`` records conform to the
  ill-structured-prompt schema (id, prompt) and must NOT contain a
  single verifiable ground-truth answer field.
* The loader module, once implemented, exposes the expected public
  functions and fails loudly on invalid dataset identifiers.

The schema-validation contract is exercised directly on representative
record shapes; loader-integration checks are skipped (with an explicit
reason) until T011/T012 land, per the "tests written before
implementation" workflow in tasks.md.
"""

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MMLU_STEM_PATH = PROJECT_ROOT / "code" / "data" / "processed" / "mmlu_stem.jsonl"
OPENSCI_PATH = PROJECT_ROOT / "code" / "data" / "processed" / "opensci_reason.jsonl"

# ---------------------------------------------------------------------------
# Contract: record schemas
# ---------------------------------------------------------------------------

MMLU_REQUIRED_FIELDS = {"id", "prompt", "answer"}
MMLU_OPTIONAL_FIELDS = {"choices", "subject", "domain"}
OPENSCI_REQUIRED_FIELDS = {"id", "prompt"}
OPENSCI_FORBIDDEN_FIELDS = {"answer", "correct_answer", "gold_answer", "label"}


def validate_mmlu_record(record: dict) -> None:
    """Assert a single MMLU-STEM record satisfies the deterministic contract."""
    assert isinstance(record, dict), "record must be a JSON object"
    missing = MMLU_REQUIRED_FIELDS - set(record)
    assert not missing, f"missing required fields: {sorted(missing)}"
    assert isinstance(record["id"], (str, int)), "id must be str or int"
    assert isinstance(record["prompt"], str) and record["prompt"].strip(), (
        "prompt must be a non-empty string"
    )
    assert isinstance(record["answer"], str) and record["answer"], (
        "answer must be a non-empty string (the correct option letter)"
    )
    if "choices" in record:
        assert isinstance(record["choices"], list) and record["choices"], (
            "choices must be a non-empty list"
        )
        assert all(isinstance(c, str) for c in record["choices"]), (
            "choices must all be strings"
        )
        assert record["answer"] in record["choices"], (
            "answer must be one of the listed choices"
        )
    if "domain" in record:
        assert record["domain"] == "deterministic", (
            "MMLU-STEM records must carry domain='deterministic'"
        )


def validate_opensci_record(record: dict) -> None:
    """Assert a single OpenSci-Reason record satisfies the ill-structured contract."""
    assert isinstance(record, dict), "record must be a JSON object"
    missing = OPENSCI_REQUIRED_FIELDS - set(record)
    assert not missing, f"missing required fields: {sorted(missing)}"
    assert isinstance(record["id"], (str, int)), "id must be str or int"
    assert isinstance(record["prompt"], str) and record["prompt"].strip(), (
        "prompt must be a non-empty string"
    )
    forbidden = OPENSCI_FORBIDDEN_FIELDS & set(record)
    assert not forbidden, (
        "ill-structured prompts must NOT carry a single verifiable "
        f"ground-truth answer; found: {sorted(forbidden)}"
    )
    if "domain" in record:
        assert record["domain"] == "ill-structured", (
            "OpenSci-Reason records must carry domain='ill-structured'"
        )


class TestMmluStemRecordContract:
    def test_valid_record_passes(self):
        validate_mmlu_record(
            {
                "id": "mmlu-stem-0001",
                "prompt": "What is 2 + 2?",
                "choices": ["3", "4", "5", "6"],
                "answer": "4",
                "subject": "elementary_mathematics",
            }
        )

    def test_missing_required_field_fails(self):
        with pytest.raises(AssertionError, match="missing required fields"):
            validate_mmlu_record({"id": "x", "prompt": "p"})

    def test_empty_prompt_fails(self):
        with pytest.raises(AssertionError, match="non-empty string"):
            validate_mmlu_record({"id": "x", "prompt": "   ", "answer": "A"})

    def test_answer_not_in_choices_fails(self):
        with pytest.raises(AssertionError, match="one of the listed choices"):
            validate_mmlu_record(
                {"id": "x", "prompt": "p", "choices": ["A", "B"], "answer": "C"}
            )

    def test_wrong_domain_label_fails(self):
        with pytest.raises(AssertionError, match="deterministic"):
            validate_mmlu_record(
                {"id": "x", "prompt": "p", "answer": "A", "domain": "ill-structured"}
            )


class TestOpenSciRecordContract:
    def test_valid_record_passes(self):
        validate_opensci_record(
            {
                "id": "opensci-0001",
                "prompt": "Propose an experimental design to test ...",
                "domain": "ill-structured",
            }
        )

    def test_missing_required_field_fails(self):
        with pytest.raises(AssertionError, match="missing required fields"):
            validate_opensci_record({"id": "x"})

    def test_ground_truth_answer_is_forbidden(self):
        # Curation logic (T012) must REMOVE prompts with a single
        # verifiable ground-truth answer.
        with pytest.raises(AssertionError, match="ground-truth"):
            validate_opensci_record(
                {"id": "x", "prompt": "p", "answer": "42"}
            )

    def test_numeric_label_is_forbidden(self):
        with pytest.raises(AssertionError, match="ground-truth"):
            validate_opensci_record(
                {"id": "x", "prompt": "p", "label": 1}
            )

    def test_wrong_domain_label_fails(self):
        with pytest.raises(AssertionError, match="ill-structured"):
            validate_opensci_record(
                {"id": "x", "prompt": "p", "domain": "deterministic"}
            )


# ---------------------------------------------------------------------------
# Contract: on-disk JSONL files (when produced by T011/T012)
# ---------------------------------------------------------------------------

def _iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


class TestProcessedFilesContract:
    def test_mmlu_stem_jsonl_conforms(self):
        if not MMLU_STEM_PATH.exists():
            pytest.skip("code/data/processed/mmlu_stem.jsonl not yet produced (T011 pending)")
        records = list(_iter_jsonl(MMLU_STEM_PATH))
        assert records, "mmlu_stem.jsonl must not be empty"
        for rec in records:
            validate_mmlu_record(rec)

    def test_opensci_reason_jsonl_conforms(self):
        if not OPENSCI_PATH.exists():
            pytest.skip("code/data/processed/opensci_reason.jsonl not yet produced (T012 pending)")
        records = list(_iter_jsonl(OPENSCI_PATH))
        assert records, "opensci_reason.jsonl must not be empty"
        for rec in records:
            validate_opensci_record(rec)


# ---------------------------------------------------------------------------
# Contract: loader module API (implemented in T011/T012)
# ---------------------------------------------------------------------------

def _import_download_module():
    try:
        from code.data import download  # noqa: WPS433
    except ImportError:
        pytest.skip("code/data/download.py not yet implemented (T011/T012 pending)")
    return download


class TestLoaderApiContract:
    def test_module_exposes_download_functions(self):
        download = _import_download_module()
        for name in ("download_mmlu_stem", "load_opensci_reason"):
            assert hasattr(download, name), (
                f"download module must expose '{name}'"
            )

    def test_invalid_dataset_id_raises_loudly(self):
        download = _import_download_module()
        if not hasattr(download, "download_mmlu_stem"):
            pytest.skip("download_mmlu_stem not yet implemented")
        with pytest.raises(Exception):
            # A fabricated dataset id must NEVER fall back to synthetic
            # data; it must raise so the failure is visible.
            download.download_mmlu_stem(
                output_path=PROJECT_ROOT / "data" / "raw" / "_contract_invalid.jsonl",
                dataset_id="this-dataset/does-not-exist",
            )

    def test_no_synthetic_fallback_in_source(self):
        download = _import_download_module()
        source = Path(download.__file__).read_text(encoding="utf-8")
        for banned in ("generate_synthetic", "mock_", "np.random", "numpy.random"):
            assert banned not in source, (
                f"loader must not contain synthetic fallback '{banned}'"
            )