"""
tests/test_orchestrator.py
--------------------------

Tests for the repaired pipeline orchestrator ``code/main.py`` (T101):

* ``--help`` exits 0 and documents all flags.
* Running with no flags prints help and exits 0.
* Schema validation fails loudly on malformed artifacts.
* Missing artifacts are detected loudly.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAIN_PY = ROOT / "code" / "main.py"

sys.path.insert(0, str(ROOT / "code"))


def _run_main(*args):
    return subprocess.run(
        [sys.executable, str(MAIN_PY), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )


class TestCli:
    def test_help_exits_zero_and_documents_flags(self):
        result = _run_main("--help")
        assert result.returncode == 0, result.stderr
        for flag in (
            "--generate",
            "--compress",
            "--analyze",
            "--n-workflows",
            "--seed",
            "--depths",
        ):
            assert flag in result.stdout, f"flag {flag} missing from --help"

    def test_no_flags_prints_help_and_exits_zero(self):
        result = _run_main()
        assert result.returncode == 0, result.stderr
        assert "--generate" in result.stdout

    def test_missing_input_fails_loudly_on_compress(self, tmp_path, monkeypatch):
        # Point the orchestrator at a project root with no workflows.json.
        import main as main_mod

        monkeypatch.setattr(main_mod, "ROOT", tmp_path)
        monkeypatch.setattr(
            main_mod, "WORKFLOWS_PATH", tmp_path / "data" / "raw" / "workflows.json"
        )
        with pytest.raises(SystemExit) as excinfo:
            main_mod.step_compress(
                argparse_namespace(depths=[1, 2])
            )
        assert excinfo.value.code == 1


def argparse_namespace(**kwargs):
    import argparse

    return argparse.Namespace(**kwargs)


class TestValidation:
    def test_validate_against_schema_rejects_malformed_data(self, tmp_path):
        import main as main_mod

        schema_path = tmp_path / "schema.yaml"
        schema_path.write_text(
            (
                "type: object\n"
                "properties:\n"
                "  workflows:\n"
                "    type: array\n"
                "required:\n"
                "  - workflows\n"
            ),
            encoding="utf-8",
        )
        data_path = tmp_path / "data.json"
        data_path.write_text(json.dumps({"not_workflows": []}), encoding="utf-8")

        with pytest.raises(SystemExit) as excinfo:
            main_mod.validate_against_schema(
                data_path, schema_path, "unit-test artifact"
            )
        assert excinfo.value.code == 1

    def test_validate_against_schema_rejects_bad_json(self, tmp_path):
        import main as main_mod

        schema_path = tmp_path / "schema.yaml"
        schema_path.write_text("type: object\n", encoding="utf-8")
        data_path = tmp_path / "data.json"
        data_path.write_text("{not valid json", encoding="utf-8")

        with pytest.raises(SystemExit) as excinfo:
            main_mod.validate_against_schema(
                data_path, schema_path, "unit-test artifact"
            )
        assert excinfo.value.code == 1

    def test_validate_against_schema_missing_schema_fails(self, tmp_path):
        import main as main_mod

        data_path = tmp_path / "data.json"
        data_path.write_text("{}", encoding="utf-8")
        with pytest.raises(SystemExit) as excinfo:
            main_mod.validate_against_schema(
                data_path, tmp_path / "nope.yaml", "unit-test artifact"
            )
        assert excinfo.value.code == 1

    def test_require_file_detects_missing_and_empty(self, tmp_path):
        import main as main_mod

        missing = tmp_path / "missing.json"
        with pytest.raises(SystemExit):
            main_mod._require_file(missing, "unit test")

        empty = tmp_path / "empty.json"
        empty.write_bytes(b"")
        with pytest.raises(SystemExit):
            main_mod._require_file(empty, "unit test")

        good = tmp_path / "good.json"
        good.write_text("{}", encoding="utf-8")
        main_mod._require_file(good, "unit test")  # must not raise