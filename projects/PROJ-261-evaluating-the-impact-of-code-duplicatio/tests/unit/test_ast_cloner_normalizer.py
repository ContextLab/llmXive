"""Validate that the IdentifierNormalizer produces consistent output."""
import ast

from ast_cloner import IdentifierNormalizer, _normalised_source_from_ast


def test_identifier_normalizer_produces_same_structure():
    src1 = "def add(x, y):\n    return x + y\n"
    src2 = "def add(a, b):\n    return a + b\n"

    mod1 = ast.parse(src1)
    mod2 = ast.parse(src2)

    norm1 = _normalised_source_from_ast(mod1)
    norm2 = _normalised_source_from_ast(mod2)

    assert norm1 == norm2