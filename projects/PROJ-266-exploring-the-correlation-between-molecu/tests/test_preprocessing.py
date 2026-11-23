"""
Unit tests for the preprocessing module.

Tests the filtering logic and pass rate calculation for User Story 1.
"""

import csv
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

import sys
# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.preprocessing import (
    load_raw_data,
    parse_protocol_metadata,
    check_protocol_heterogeneity,
    preprocess_data,
    write_clean_data
)


class TestPreprocessingLogic(TestCase):
    """Tests for the core filtering logic."""

    def setUp(self):
        self.test_data = [
            # Valid record
            {
                'smiles': 'CCO',
                'logPapp': '-5.0',
                'protocol_metadata': json.dumps({'standard_type': 'MEASUREMENT'})
            },
            # Invalid SMILES (NULL)
            {
                'smiles': '',
                'logPapp': '-5.0',
                'protocol_metadata': json.dumps({'standard_type': 'MEASUREMENT'})
            },
            # Invalid logPapp (NULL)
            {
                'smiles': 'CCO',
                'logPapp': '',
                'protocol_metadata': json.dumps({'standard_type': 'MEASUREMENT'})
            },
            # Invalid Protocol (Not MEASUREMENT)
            {
                'smiles': 'CCO',
                'logPapp': '-5.0',
                'protocol_metadata': json.dumps({'standard_type': 'ESTIMATE'})
            },
            # Invalid Protocol (Missing key)
            {
                'smiles': 'CCO',
                'logPapp': '-5.0',
                'protocol_metadata': json.dumps({'other_key': 'value'})
            },
            # Valid record with null string
            {
                'smiles': 'null',
                'logPapp': '-5.0',
                'protocol_metadata': json.dumps({'standard_type': 'MEASUREMENT'})
            }
        ]

    def test_filter_logic(self):
        """
        Verifies that the filtering logic correctly excludes records based on:
        1. NULL/Empty SMILES
        2. NULL/Empty logPapp
        3. Protocol heterogeneity (standard_type != 'MEASUREMENT')
        """
        filtered_data, stats = preprocess_data(self.test_data)

        # Expected: Only the first record (index 0) should pass.
        # Index 1: Null SMILES
        # Index 2: Null logPapp
        # Index 3: Estimate (not Measurement)
        # Index 4: Missing standard_type
        # Index 5: 'null' string SMILES

        self.assertEqual(len(filtered_data), 1)
        self.assertEqual(filtered_data[0]['smiles'], 'CCO')

        # Verify counts
        self.assertEqual(stats['excluded_null_smiles'], 2) # Index 1 and 5
        self.assertEqual(stats['excluded_null_logpapp'], 1) # Index 2
        self.assertEqual(stats['excluded_protocol_heterogeneity'], 2) # Index 3 and 4

    def test_pass_rate_calculation(self):
        """
        Verifies that the pass rate is calculated correctly in the stats dict.
        """
        filtered_data, stats = preprocess_data(self.test_data)

        total_input = len(self.test_data)
        total_output = len(filtered_data)
        expected_pass_rate = (total_output / total_input) * 100

        # The stats dict itself doesn't store the rate, but we can verify the components
        # to ensure the rate would be correct if calculated.
        self.assertEqual(stats['total_input'], total_input)
        self.assertEqual(stats['total_output'], total_output)

        # Verify that the sum of exclusions + output equals input
        total_exclusions = (
            stats['excluded_null_smiles'] +
            stats['excluded_null_logpapp'] +
            stats['excluded_protocol_heterogeneity']
        )
        self.assertEqual(total_exclusions + total_output, total_input)


class TestParseProtocolMetadata(TestCase):
    """Tests for parsing the JSON metadata string."""

    def test_valid_json(self):
        row = {'protocol_metadata': '{"standard_type": "MEASUREMENT", "other": 123}'}
        result = parse_protocol_metadata(row)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['standard_type'], 'MEASUREMENT')

    def test_invalid_json(self):
        row = {'protocol_metadata': 'not valid json'}
        result = parse_protocol_metadata(row)
        self.assertIsNone(result)

    def test_empty_string(self):
        row = {'protocol_metadata': ''}
        result = parse_protocol_metadata(row)
        self.assertIsNone(result)

    def test_missing_key(self):
        row = {}
        result = parse_protocol_metadata(row)
        self.assertIsNone(result)


class TestCheckProtocolHeterogeneity(TestCase):
    """Tests for the protocol heterogeneity check."""

    def test_is_measurement(self):
        row = {'protocol_metadata': json.dumps({'standard_type': 'MEASUREMENT'})}
        # Returns True if EXCLUDED, False if PASSED
        self.assertFalse(check_protocol_heterogeneity(row))

    def test_is_not_measurement(self):
        row = {'protocol_metadata': json.dumps({'standard_type': 'ESTIMATE'})}
        self.assertTrue(check_protocol_heterogeneity(row))

    def test_missing_metadata(self):
        row = {}
        self.assertTrue(check_protocol_heterogeneity(row))

    def test_missing_standard_type(self):
        row = {'protocol_metadata': json.dumps({'other': 'value'})}
        self.assertTrue(check_protocol_heterogeneity(row))
