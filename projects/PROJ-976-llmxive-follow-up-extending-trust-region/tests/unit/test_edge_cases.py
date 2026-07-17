"""
Unit tests for edge cases in lexical and syntactic metrics.
"""
import pytest
import math
import numpy as np

from code.metrics.lexical import distinct_n_ratio, ngram_entropy
from code.metrics.syntactic import parse_tree_depth, parse_tree_depth_variance


class TestEmptyStringLexical:
    """Tests for handling empty strings in lexical metrics."""

    def test_empty_string_distinct_n_ratio(self):
        """
        distinct_n_ratio should return 0.0 for empty input to avoid division by zero.
        """
        # distinct_n_ratio(n=4)
        result = distinct_n_ratio([], n=4)
        assert result == 0.0

    def test_empty_string_ngram_entropy(self):
        """
        ngram_entropy should return 0.0 for empty input.
        """
        # ngram_entropy(n=4)
        result = ngram_entropy([], n=4)
        assert result == 0.0


class TestEmptyStringSyntactic:
    """Tests for handling empty strings in syntactic metrics."""

    def test_empty_string_parse_tree_depth(self):
        """
        parse_tree_depth should return 0 for empty input.
        """
        result = parse_tree_depth("")
        assert result == 0

    def test_empty_string_parse_tree_depth_variance(self):
        """
        parse_tree_depth_variance should return 0.0 (or NaN depending on definition)
        for empty input. We expect 0.0 as there is no variance in an empty set.
        """
        # Input is a list of strings
        result = parse_tree_depth_variance([])
        # If the list is empty, variance is undefined; we return 0.0 to be safe
        assert result == 0.0

    def test_list_with_one_empty_string(self):
        """
        Test a list containing a single empty string.
        """
        # parse_tree_depth("") -> 0
        # variance of [0] -> 0
        result = parse_tree_depth_variance([""])
        assert result == 0.0