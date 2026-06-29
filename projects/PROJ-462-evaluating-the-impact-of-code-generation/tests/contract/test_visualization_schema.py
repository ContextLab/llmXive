"""
Contract test for visualization schema.

Validates that visualization output conforms to the schema defined in:
specs/001-code-generation-performance-outcomes/contracts/visualization.schema.yaml

This test ensures the VisualizationOutput entity has the correct structure:
- plot_type: string (e.g., 'boxplot', 'violin', 'interaction')
- stratification_variable: string (e.g., 'experience_level')
- interaction_lines: boolean or list
- file_path: string (path to generated visualization)

Run with: pytest tests/contract/test_visualization_schema.py -v
"""

import json
import os
import sys
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Add code directory to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / 'code'
SPECS_DIR = PROJECT_ROOT / 'specs' / '001-code-generation-performance-outcomes'

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import yaml

# Schema path (from T006)
VISUALIZATION_SCHEMA_PATH = SPECS_DIR / 'contracts' / 'visualization.schema.yaml'

# Required fields from VisualizationOutput entity
REQUIRED_FIELDS = ['plot_type', 'stratification_variable', 'interaction_lines', 'file_path']
VALID_PLOT_TYPES = ['boxplot', 'violin', 'interaction', 'bar', 'line', 'scatter']

def load_visualization_schema() -> Dict[str, Any]:
    """Load the visualization schema from YAML file."""
    if not VISUALIZATION_SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Visualization schema not found at {VISUALIZATION_SCHEMA_PATH}")
    
    with open(VISUALIZATION_SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def validate_visualization_output(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate visualization output against schema.
    
    Returns list of validation errors (empty if valid).
    """
    errors = []
    
    # Check all required fields present
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Validate plot_type
    if 'plot_type' in data:
        if not isinstance(data['plot_type'], str):
            errors.append("plot_type must be a string")
        elif data['plot_type'] not in VALID_PLOT_TYPES:
            errors.append(f"plot_type must be one of {VALID_PLOT_TYPES}, got: {data['plot_type']}")
    
    # Validate stratification_variable
    if 'stratification_variable' in data:
        if not isinstance(data['stratification_variable'], str):
            errors.append("stratification_variable must be a string")
        elif not data['stratification_variable']:
            errors.append("stratification_variable cannot be empty")
    
    # Validate interaction_lines
    if 'interaction_lines' in data:
        if not isinstance(data['interaction_lines'], (bool, list)):
            errors.append("interaction_lines must be a boolean or list")
    
    # Validate file_path
    if 'file_path' in data:
        if not isinstance(data['file_path'], str):
            errors.append("file_path must be a string")
        elif not data['file_path']:
            errors.append("file_path cannot be empty")
        elif not data['file_path'].endswith(('.png', '.pdf', '.svg', '.jpg')):
            errors.append("file_path must end with a valid image extension (.png, .pdf, .svg, .jpg)")
    
    return errors


class TestVisualizationSchema:
    """Contract tests for visualization schema validation."""

    @pytest.fixture(scope='class')
    def schema(self):
        """Load visualization schema once for all tests."""
        return load_visualization_schema()

    def test_schema_exists(self):
        """Test that the visualization schema file exists."""
        assert VISUALIZATION_SCHEMA_PATH.exists(), \
            f"Visualization schema file must exist at {VISUALIZATION_SCHEMA_PATH}"
    
    def test_schema_is_valid_yaml(self, schema):
        """Test that the schema file is valid YAML."""
        assert schema is not None, "Schema must not be None"
        assert isinstance(schema, dict), "Schema must be a dictionary"
    
    def test_schema_has_required_structure(self, schema):
        """Test that the schema has the expected structure."""
        # Schema should have entity definition
        assert 'entity' in schema or 'VisualizationOutput' in str(schema), \
            "Schema should define VisualizationOutput entity"
    
    def test_schema_has_required_fields(self, schema):
        """Test that schema defines all required fields."""
        schema_str = yaml.dump(schema)
        for field in REQUIRED_FIELDS:
            assert field in schema_str, \
                f"Schema must define field: {field}"
    
    def test_valid_visualization_output(self, schema):
        """Test validation of a valid visualization output."""
        valid_output = {
            'plot_type': 'boxplot',
            'stratification_variable': 'experience_level',
            'interaction_lines': True,
            'file_path': 'data/output/productivity_by_experience.png'
        }
        
        errors = validate_visualization_output(valid_output, schema)
        assert len(errors) == 0, f"Valid output should have no errors, got: {errors}"
    
    def test_valid_interaction_plot_with_lines(self, schema):
        """Test validation of interaction plot with line configuration."""
        valid_output = {
            'plot_type': 'interaction',
            'stratification_variable': 'experience_level',
            'interaction_lines': ['tool_usage', 'defect_rate'],
            'file_path': 'data/output/interaction_plot.pdf'
        }
        
        errors = validate_visualization_output(valid_output, schema)
        assert len(errors) == 0, f"Valid interaction output should have no errors, got: {errors}"
    
    def test_missing_plot_type(self, schema):
        """Test validation fails when plot_type is missing."""
        invalid_output = {
            'stratification_variable': 'experience_level',
            'interaction_lines': True,
            'file_path': 'data/output/test.png'
        }
        
        errors = validate_visualization_output(invalid_output, schema)
        assert any('plot_type' in e for e in errors), \
            "Should report missing plot_type"
    
    def test_missing_stratification_variable(self, schema):
        """Test validation fails when stratification_variable is missing."""
        invalid_output = {
            'plot_type': 'boxplot',
            'interaction_lines': True,
            'file_path': 'data/output/test.png'
        }
        
        errors = validate_visualization_output(invalid_output, schema)
        assert any('stratification_variable' in e for e in errors), \
            "Should report missing stratification_variable"
    
    def test_missing_interaction_lines(self, schema):
        """Test validation fails when interaction_lines is missing."""
        invalid_output = {
            'plot_type': 'boxplot',
            'stratification_variable': 'experience_level',
            'file_path': 'data/output/test.png'
        }
        
        errors = validate_visualization_output(invalid_output, schema)
        assert any('interaction_lines' in e for e in errors), \
            "Should report missing interaction_lines"
    
    def test_missing_file_path(self, schema):
        """Test validation fails when file_path is missing."""
        invalid_output = {
            'plot_type': 'boxplot',
            'stratification_variable': 'experience_level',
            'interaction_lines': True
        }
        
        errors = validate_visualization_output(invalid_output, schema)
        assert any('file_path' in e for e in errors), \
            "Should report missing file_path"
    
    def test_invalid_plot_type(self, schema):
        """Test validation fails for invalid plot_type."""
        invalid_output = {
            'plot_type': 'invalid_plot',
            'stratification_variable': 'experience_level',
            'interaction_lines': True,
            'file_path': 'data/output/test.png'
        }
        
        errors = validate_visualization_output(invalid_output, schema)
        assert any('plot_type' in e for e in errors), \
            "Should report invalid plot_type"
    
    def test_empty_file_path(self, schema):
        """Test validation fails for empty file_path."""
        invalid_output = {
            'plot_type': 'boxplot',
            'stratification_variable': 'experience_level',
            'interaction_lines': True,
            'file_path': ''
        }
        
        errors = validate_visualization_output(invalid_output, schema)
        assert any('file_path' in e for e in errors), \
            "Should report empty file_path"
    
    def test_invalid_file_extension(self, schema):
        """Test validation fails for invalid file extension."""
        invalid_output = {
            'plot_type': 'boxplot',
            'stratification_variable': 'experience_level',
            'interaction_lines': True,
            'file_path': 'data/output/test.txt'
        }
        
        errors = validate_visualization_output(invalid_output, schema)
        assert any('file_path' in e for e in errors), \
            "Should report invalid file extension"
    
    def test_all_valid_plot_types(self, schema):
        """Test each valid plot type passes validation."""
        for plot_type in VALID_PLOT_TYPES:
            valid_output = {
                'plot_type': plot_type,
                'stratification_variable': 'experience_level',
                'interaction_lines': False,
                'file_path': 'data/output/test.png'
            }
            
            errors = validate_visualization_output(valid_output, schema)
            assert len(errors) == 0, \
                f"Plot type '{plot_type}' should be valid, got errors: {errors}"
    
    def test_interaction_lines_as_boolean(self, schema):
        """Test interaction_lines accepts boolean values."""
        for value in [True, False]:
            valid_output = {
                'plot_type': 'boxplot',
                'stratification_variable': 'experience_level',
                'interaction_lines': value,
                'file_path': 'data/output/test.png'
            }
            
            errors = validate_visualization_output(valid_output, schema)
            assert len(errors) == 0, \
                f"interaction_lines as {value} should be valid, got errors: {errors}"
    
    def test_interaction_lines_as_list(self, schema):
        """Test interaction_lines accepts list values."""
        valid_output = {
            'plot_type': 'interaction',
            'stratification_variable': 'experience_level',
            'interaction_lines': ['variable1', 'variable2'],
            'file_path': 'data/output/test.png'
        }
        
        errors = validate_visualization_output(valid_output, schema)
        assert len(errors) == 0, \
            f"interaction_lines as list should be valid, got errors: {errors}"
    
    def test_schema_completeness(self, schema):
        """Test that schema defines all required entity fields."""
        schema_content = yaml.dump(schema)
        
        # Check for VisualizationOutput entity mention
        assert 'VisualizationOutput' in schema_content or \
               'entity' in schema_content.lower(), \
               "Schema should define VisualizationOutput entity"
        
        # Check for all required fields
        for field in REQUIRED_FIELDS:
            assert field in schema_content, \
                f"Schema must include field: {field}"
    
    def test_schema_type_definitions(self, schema):
        """Test that schema includes type information for fields."""
        schema_content = yaml.dump(schema)
        
        # Should have type definitions
        type_indicators = ['type:', 'string', 'boolean', 'list', 'array']
        found_types = [t for t in type_indicators if t in schema_content.lower()]
        
        assert len(found_types) > 0, \
            "Schema should include type definitions for fields"
    
    def test_schema_has_description(self, schema):
        """Test that schema includes descriptive information."""
        schema_content = yaml.dump(schema)
        
        # Should have some descriptive content
        desc_indicators = ['description', 'comment', 'note', 'entity', 'field']
        found_desc = [d for d in desc_indicators if d in schema_content.lower()]
        
        assert len(found_desc) > 0, \
            "Schema should include descriptive information"

class TestVisualizationOutputIntegration:
    """Integration tests for visualization output validation."""

    def test_full_validation_workflow(self):
        """Test complete validation workflow with schema loading."""
        # Load schema
        schema = load_visualization_schema()
        
        # Create valid output
        output = {
            'plot_type': 'boxplot',
            'stratification_variable': 'experience_level',
            'interaction_lines': True,
            'file_path': 'data/output/productivity_productivity.png'
        }
        
        # Validate
        errors = validate_visualization_output(output, schema)
        
        # Should pass
        assert len(errors) == 0, f"Integration test failed: {errors}"
    
    def test_multiple_outputs_validation(self):
        """Test validation of multiple visualization outputs."""
        schema = load_visualization_schema()
        
        outputs = [
            {
                'plot_type': 'boxplot',
                'stratification_variable': 'experience_level',
                'interaction_lines': True,
                'file_path': 'data/output/boxplot.png'
            },
            {
                'plot_type': 'interaction',
                'stratification_variable': 'tool_usage',
                'interaction_lines': ['task_time', 'defect_rate'],
                'file_path': 'data/output/interaction.pdf'
            },
            {
                'plot_type': 'violin',
                'stratification_variable': 'project_type',
                'interaction_lines': False,
                'file_path': 'data/output/violin.svg'
            }
        ]
        
        for i, output in enumerate(outputs):
            errors = validate_visualization_output(output, schema)
            assert len(errors) == 0, \
                f"Output {i} failed validation: {errors}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
