"""
Contract tests for project schemas.
Validates that output artifacts conform to defined schema structures.
"""
import json
import os
import yaml
import pytest
from pathlib import Path

# Add project root to path for imports if necessary
project_root = Path(__file__).parent.parent.parent
contracts_dir = project_root / "contracts"
artifacts_dir = project_root / "artifacts"


def load_schema(schema_filename: str) -> dict:
    """Load a YAML schema definition from the contracts directory."""
    schema_path = contracts_dir / schema_filename
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def load_json_artifact(artifact_path: Path) -> dict:
    """Load a JSON artifact file."""
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact file not found: {artifact_path}")
    with open(artifact_path, "r") as f:
        return json.load(f)


def validate_structure(data: dict, schema: dict, path_prefix: str = "") -> list:
    """
    Recursively validate a dictionary against a schema definition.
    Returns a list of error messages.
    """
    errors = []
    schema_type = schema.get("type")
    schema_required = schema.get("required", [])
    schema_properties = schema.get("properties", {})

    if schema_type == "object":
        if not isinstance(data, dict):
            errors.append(f"{path_prefix}: Expected object, got {type(data).__name__}")
            return errors

        # Check required fields
        for field in schema_required:
            if field not in data:
                errors.append(f"{path_prefix}: Missing required field '{field}'")

        # Validate properties
        for key, value in data.items():
            if key in schema_properties:
                sub_schema = schema_properties[key]
                sub_path = f"{path_prefix}.{key}" if path_prefix else key
                errors.extend(validate_structure(value, sub_schema, sub_path))
            else:
                # Optional: warn on extra fields if strict mode is desired
                pass

    elif schema_type == "array":
        if not isinstance(data, list):
            errors.append(f"{path_prefix}: Expected array, got {type(data).__name__}")
            return errors
        items_schema = schema.get("items", {})
        for i, item in enumerate(data):
            sub_path = f"{path_prefix}[{i}]"
            errors.extend(validate_structure(item, items_schema, sub_path))

    elif schema_type == "string":
        if not isinstance(data, str):
            errors.append(f"{path_prefix}: Expected string, got {type(data).__name__}")

    elif schema_type == "integer":
        if not isinstance(data, int):
            errors.append(f"{path_prefix}: Expected integer, got {type(data).__name__}")

    elif schema_type == "number":
        if not isinstance(data, (int, float)):
            errors.append(f"{path_prefix}: Expected number, got {type(data).__name__}")

    elif schema_type == "boolean":
        if not isinstance(data, bool):
            errors.append(f"{path_prefix}: Expected boolean, got {type(data).__name__}")

    return errors


class TestFinalReportSchema:
    """Contract tests for the final report structure."""

    @pytest.fixture
    def report_schema(self):
        """Load the output schema definition."""
        return load_schema("output.schema.yaml")

    @pytest.fixture
    def final_report_path(self):
        """Path to the final report artifact."""
        # The reporting task (T034) generates a Markdown report, but often
        # includes a JSON summary or the report itself is validated against a schema.
        # Assuming the final report is saved as a JSON summary or the Markdown
        # structure is validated by checking the existence of required sections.
        # Per task description: Validates `contracts/output.schema.yaml` structure.
        # We will look for a JSON summary if it exists, or the Markdown file itself.
        json_path = artifacts_dir / "reports" / "final_report_summary.json"
        md_path = artifacts_dir / "reports" / "final_report.md"
        
        if json_path.exists():
            return json_path, "json"
        elif md_path.exists():
            # For markdown, we might just check file existence and basic structure
            # or load a companion JSON. Here we assume the schema expects a JSON structure
            # representing the report content.
            return md_path, "markdown"
        else:
            # If neither exists, the test will fail with FileNotFoundError in load_json_artifact
            # or we can return a dummy path to trigger the error in the test.
            return json_path, "json"

    def test_final_report_schema_validates_structure(self, report_schema, final_report_path):
        """
        Validates `contracts/output.schema.yaml` structure (tables, metrics, deviations).
        Ensures the final report artifact conforms to the defined schema.
        """
        report_path, report_type = final_report_path

        if report_type == "json":
            try:
                report_data = load_json_artifact(report_path)
            except FileNotFoundError as e:
                pytest.fail(f"Final report artifact not found: {e}")
            
            errors = validate_structure(report_data, report_schema)
            
            assert not errors, f"Report schema validation failed:\n" + "\n".join(errors)

        elif report_type == "markdown":
            # If the report is Markdown, we validate that the file exists and contains
            # sections corresponding to the schema's top-level keys (e.g., 'metrics', 'deviations').
            # This is a heuristic validation for Markdown artifacts.
            assert report_path.exists(), f"Markdown report not found: {report_path}"
            
            with open(report_path, "r") as f:
                content = f.read().lower()
            
            # Check for presence of key sections defined in schema (e.g., 'metrics', 'deviations')
            # This is a simplified check for Markdown files.
            required_sections = ["metrics", "deviations", "tables"]
            found_sections = []
            missing_sections = []
            
            for section in required_sections:
                if section in content:
                    found_sections.append(section)
                else:
                    missing_sections.append(section)
            
            # We expect at least 'metrics' and 'deviations' to be present
            assert "metrics" in found_sections, "Missing 'metrics' section in Markdown report"
            assert "deviations" in found_sections, "Missing 'deviations' section in Markdown report"
            
            # If strict JSON schema validation is required for Markdown, it would need a parser.
            # For now, we assume the schema defines the logical structure which we verify via keywords.
            if missing_sections:
                pytest.fail(f"Missing sections in Markdown report: {missing_sections}")


class TestMergedDatasetSchema:
    """Contract tests for the merged dataset schema."""

    @pytest.fixture
    def dataset_schema(self):
        """Load the dataset schema definition."""
        return load_schema("dataset.schema.yaml")

    def test_merged_dataset_schema_validates_columns(self, dataset_schema):
        """
        Validates `contracts/dataset.schema.yaml` columns (species, root_length, 
        branching_density, surface_area, phosphorus, nitrogen).
        """
        # This test ensures the schema file itself is valid and defines the expected columns.
        # It does not validate a data file, but the schema definition.
        
        assert "properties" in dataset_schema, "Schema must define properties"
        properties = dataset_schema["properties"]
        
        expected_columns = [
            "species", "root_length", "branching_density", 
            "surface_area", "phosphorus", "nitrogen"
        ]
        
        missing_columns = []
        for col in expected_columns:
            if col not in properties:
                missing_columns.append(col)
        
        assert not missing_columns, f"Dataset schema missing required columns: {missing_columns}"

        # Validate types if specified
        if "species" in properties:
            assert properties["species"].get("type") == "string", "Species column must be string"
        
        numeric_cols = ["root_length", "branching_density", "surface_area", "phosphorus", "nitrogen"]
        for col in numeric_cols:
            if col in properties:
                col_type = properties[col].get("type")
                assert col_type in ["number", "integer"], f"Column {col} must be numeric, got {col_type}"

class TestModelResultsSchema:
    """Contract tests for model results schema."""

    @pytest.fixture
    def model_schema(self):
        """Load the model results schema definition."""
        return load_schema("model_results.schema.yaml")

    def test_model_results_schema_validates_fields(self, model_schema):
        """
        Validates `contracts/model_results.schema.yaml` fields 
        (lmm.adjusted_r_squared, lmm.p_values, etc.).
        """
        assert "properties" in model_schema, "Schema must define properties"
        properties = model_schema["properties"]
        
        # Check for top-level model results sections
        required_sections = ["lmm", "random_forest"]
        missing_sections = [s for s in required_sections if s not in properties]
        
        assert not missing_sections, f"Model schema missing required sections: {missing_sections}"
        
        # Validate LMM structure
        lmm_props = properties.get("lmm", {}).get("properties", {})
        lmm_required = properties.get("lmm", {}).get("required", [])
        
        assert "adjusted_r_squared" in lmm_props, "LMM schema missing adjusted_r_squared"
        assert "p_values" in lmm_props, "LMM schema missing p_values"
        
        # Validate Random Forest structure
        rf_props = properties.get("random_forest", {}).get("properties", {})
        assert "r_squared" in rf_props, "RF schema missing r_squared"
        assert "rmse" in rf_props, "RF schema missing rmse"

class TestSensitivityAnalysisSchema:
    """Contract tests for sensitivity analysis schema."""

    @pytest.fixture
    def sensitivity_schema(self):
        """Load the sensitivity analysis schema definition."""
        return load_schema("sensitivity_analysis.schema.yaml")

    def test_sensitivity_analysis_schema_validates_fields(self, sensitivity_schema):
        """
        Validates `contracts/sensitivity_analysis.schema.yaml` fields
        (percent_deviation, literature_mean, etc.).
        """
        assert "properties" in sensitivity_schema, "Schema must define properties"
        properties = sensitivity_schema["properties"]
        
        required_fields = [
            "percent_deviation", "literature_mean", "observed_coefficient",
            "confidence_interval", "literature_overlap"
        ]
        
        missing_fields = [f for f in required_fields if f not in properties]
        
        assert not missing_fields, f"Sensitivity schema missing required fields: {missing_fields}"

class TestSpeciesCountsSchema:
    """Contract tests for species counts schema."""

    @pytest.fixture
    def counts_schema(self):
        """Load the species counts schema definition."""
        return load_schema("species_counts.schema.yaml")

    def test_species_counts_schema_validates_fields(self, counts_schema):
        """
        Validates `contracts/species_counts.schema.yaml` fields
        (total_species_input, excluded_species_count, etc.).
        """
        assert "properties" in counts_schema, "Schema must define properties"
        properties = counts_schema["properties"]
        
        required_fields = [
            "total_species_input", "excluded_species_count", 
            "excluded_species_list", "rows_excluded_by_source",
            "rows_excluded_by_missing_nutrients", "rows_excluded_by_sample_size"
        ]
        
        missing_fields = [f for f in required_fields if f not in properties]
        
        assert not missing_fields, f"Species counts schema missing required fields: {missing_fields}"

class TestMetricsSchema:
    """Contract tests for metrics schema."""

    @pytest.fixture
    def metrics_schema(self):
        """Load the metrics schema definition."""
        return load_schema("metrics.schema.yaml")

    def test_metrics_schema_validates_fields(self, metrics_schema):
        """
        Validates `contracts/metrics.schema.yaml` fields
        (pn_availability_rate, species_exclusion_ratio, etc.).
        """
        assert "properties" in metrics_schema, "Schema must define properties"
        properties = metrics_schema["properties"]
        
        # Check for key metrics defined in tasks
        expected_metrics = [
            "pn_availability_rate", "species_exclusion_ratio", 
            "sc001_original_merge_rate"
        ]
        
        missing_metrics = [m for m in expected_metrics if m not in properties]
        
        assert not missing_metrics, f"Metrics schema missing required fields: {missing_metrics}"