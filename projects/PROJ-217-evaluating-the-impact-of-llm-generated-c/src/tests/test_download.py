"""Tests for the column-tolerant mapping and docstring validation
in src.data.download (T001)."""

import pandas as pd
import pytest

from src.data.download import _is_valid_docstring, _map_columns


class TestMapColumns:
    def test_maps_canonical_schema(self):
        df = pd.DataFrame(
            {
                "code": ["def a(): pass", "def b(): pass"],
                "docstring": ["Does a.", "Does b."],
                "extra": [1, 2],
            }
        )
        out = _map_columns(df)
        assert list(out.columns) == ["code", "docstring"]
        assert out["code"].iloc[0] == "def a(): pass"
        assert out["docstring"].iloc[1] == "Does b."

    def test_maps_codesearchnet_schema(self):
        df = pd.DataFrame(
            {
                "func_name": ["a", "b"],
                "func_code_string": ["def a(): pass", "def b(): pass"],
                "func_documentation_string": ["Does a.", "Does b."],
                "language": ["python", "python"],
            }
        )
        out = _map_columns(df)
        assert list(out.columns) == ["code", "docstring"]
        assert out["code"].iloc[0] == "def a(): pass"
        assert out["docstring"].iloc[1] == "Does b."

    def test_raises_on_unknown_columns(self):
        df = pd.DataFrame({"foo": [1], "bar": [2]})
        with pytest.raises(RuntimeError, match="Unexpected column set"):
            _map_columns(df)

    def test_partial_schema_raises(self):
        df = pd.DataFrame({"code": ["x"], "other": ["y"]})
        with pytest.raises(RuntimeError):
            _map_columns(df)


class TestIsValidDocstring:
    @pytest.mark.parametrize(
        "doc",
        [
            "Returns the sum of two numbers.",
            "Parse the config file and return a dict.",
        ],
    )
    def test_valid(self, doc):
        assert _is_valid_docstring(doc) is True

    @pytest.mark.parametrize(
        "doc",
        [
            "",
            "   ",
            None,
            123,
            "TODO",
            "todo",
            '"""TODO"""',
            "FIXME",
        ],
    )
    def test_invalid_boilerplate_or_empty(self, doc):
        assert _is_valid_docstring(doc) is False

    @pytest.mark.parametrize("doc", ["int", "List[int]", "Dict[str, int]", "int, str"])
    def test_invalid_bare_type_signature(self, doc):
        assert _is_valid_docstring(doc) is False