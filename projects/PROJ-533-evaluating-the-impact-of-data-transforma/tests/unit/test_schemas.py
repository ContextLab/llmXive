"""
Unit tests for schema definitions (T015a).

These tests verify that the schema YAML files exist and contain
the expected structure and constraints as defined in the task.
"""

import os
import yaml
import pytest
from pathlib import Path


class TestImputationLogSchema:
    """Tests for data/schema/imputation_log.yaml"""

    @pytest.fixture
    def schema_path(self):
        return Path("data/schema/imputation_log.yaml")

    @pytest.fixture
    def schema(self, schema_path):
        assert schema_path.exists(), f"Schema file {schema_path} does not exist"
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)

    def test_schema_file_exists(self, schema_path):
        """Test that the imputation_log schema file exists"""
        assert schema_path.exists()

    def test_schema_has_required_keys(self, schema):
        """Test that the schema contains required top-level keys"""
        assert 'file' in schema
        assert 'format' in schema
        assert 'delimiter' in schema
        assert 'columns' in schema
        assert 'header_row' in schema

    def test_schema_file_path_correct(self, schema):
        """Test that the schema references the correct file path"""
        assert schema['file'] == 'data/imputation_log.csv'

    def test_schema_format_is_csv(self, schema):
        """Test that the format is csv"""
        assert schema['format'] == 'csv'

    def test_schema_delimiter_is_comma(self, schema):
        """Test that the delimiter is comma"""
        assert schema['delimiter'] == ','

    def test_schema_has_four_columns(self, schema):
        """Test that the schema defines exactly 4 columns"""
        assert len(schema['columns']) == 4

    def test_column_dataset_id_exists(self, schema):
        """Test that dataset_id column is defined"""
        columns = {col['name']: col for col in schema['columns']}
        assert 'dataset_id' in columns
        assert columns['dataset_id']['type'] == 'string'
        assert columns['dataset_id']['required'] is True

    def test_column_variable_exists(self, schema):
        """Test that variable column is defined"""
        columns = {col['name']: col for col in schema['columns']}
        assert 'variable' in columns
        assert columns['variable']['type'] == 'string'
        assert columns['variable']['required'] is True

    def test_column_imputation_method_exists(self, schema):
        """Test that imputation_method column is defined"""
        columns = {col['name']: col for col in schema['columns']}
        assert 'imputation_method' in columns
        assert columns['imputation_method']['type'] == 'string'
        assert columns['imputation_method']['required'] is True
        # Check allowed values constraint
        assert 'allowed_values' in columns['imputation_method']['constraints']

    def test_column_rate_exists(self, schema):
        """Test that rate column is defined"""
        columns = {col['name']: col for col in schema['columns']}
        assert 'rate' in columns
        assert columns['rate']['type'] == 'string'
        assert columns['rate']['required'] is True

    def test_header_row_matches_spec(self, schema):
        """Test that the header row matches the task specification"""
        expected_header = "dataset_id,variable,imputation_method,rate"
        assert schema['header_row'] == expected_header


class TestExclusionsSchema:
    """Tests for data/schema/exclusions.yaml"""

    @pytest.fixture
    def schema_path(self):
        return Path("data/schema/exclusions.yaml")

    @pytest.fixture
    def schema(self, schema_path):
        assert schema_path.exists(), f"Schema file {schema_path} does not exist"
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)

    def test_schema_file_exists(self, schema_path):
        """Test that the exclusions schema file exists"""
        assert schema_path.exists()

    def test_schema_has_required_keys(self, schema):
        """Test that the schema contains required top-level keys"""
        assert 'file' in schema
        assert 'format' in schema
        assert 'delimiter' in schema
        assert 'columns' in schema
        assert 'header_row' in schema

    def test_schema_file_path_correct(self, schema):
        """Test that the schema references the correct file path"""
        assert schema['file'] == 'data/exclusions.csv'

    def test_schema_format_is_csv(self, schema):
        """Test that the format is csv"""
        assert schema['format'] == 'csv'

    def test_schema_delimiter_is_comma(self, schema):
        """Test that the delimiter is comma"""
        assert schema['delimiter'] == ','

    def test_schema_has_three_columns(self, schema):
        """Test that the schema defines exactly 3 columns"""
        assert len(schema['columns']) == 3

    def test_column_dataset_id_exists(self, schema):
        """Test that dataset_id column is defined"""
        columns = {col['name']: col for col in schema['columns']}
        assert 'dataset_id' in columns
        assert columns['dataset_id']['type'] == 'string'
        assert columns['dataset_id']['required'] is True

    def test_column_reason_exists(self, schema):
        """Test that reason column is defined"""
        columns = {col['name']: col for col in schema['columns']}
        assert 'reason' in columns
        assert columns['reason']['type'] == 'string'
        assert columns['reason']['required'] is True
        # Check allowed values constraint
        assert 'allowed_values' in columns['reason']['constraints']

    def test_column_details_exists(self, schema):
        """Test that details column is defined"""
        columns = {col['name']: col for col in schema['columns']}
        assert 'details' in columns
        assert columns['details']['type'] == 'string'
        assert columns['details']['required'] is True

    def test_header_row_matches_spec(self, schema):
        """Test that the header row matches the task specification"""
        expected_header = "dataset_id,reason,details"
        assert schema['header_row'] == expected_header


class TestSchemaConstraints:
    """Tests to verify constraints are properly defined"""

    @pytest.fixture
    def imputation_schema(self):
        with open('data/schema/imputation_log.yaml', 'r') as f:
            return yaml.safe_load(f)

    @pytest.fixture
    def exclusions_schema(self):
        with open('data/schema/exclusions.yaml', 'r') as f:
            return yaml.safe_load(f)

    def test_imputation_method_has_allowed_values(self, imputation_schema):
        """Test that imputation_method has allowed values constraint"""
        columns = {col['name']: col for col in imputation_schema['columns']}
        method_col = columns['imputation_method']
        assert 'allowed_values' in method_col['constraints']
        allowed = method_col['constraints']['allowed_values']
        assert 'mean' in allowed
        assert 'median' in allowed
        assert 'mode' in allowed

    def test_reason_has_allowed_values(self, exclusions_schema):
        """Test that reason has allowed values constraint"""
        columns = {col['name']: col for col in exclusions_schema['columns']}
        reason_col = columns['reason']
        assert 'allowed_values' in reason_col['constraints']
        allowed = reason_col['constraints']['allowed_values']
        assert 'missing_rate' in allowed
        assert 'sample_size' in allowed
        assert 'normality' in allowed

    def test_rate_has_range_constraint(self, imputation_schema):
        """Test that rate has range constraint"""
        columns = {col['name']: col for col in imputation_schema['columns']}
        rate_col = columns['rate']
        assert 'constraints' in rate_col
        assert 'range' in rate_col['constraints']
        range_def = rate_col['constraints']['range']
        assert 'min' in range_def
        assert 'max' in range_def