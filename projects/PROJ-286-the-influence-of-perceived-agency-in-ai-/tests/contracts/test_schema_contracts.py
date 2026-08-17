import pytest
import yaml
from pathlib import Path
import jsonschema

CONTRACTS_DIR = Path(__file__).parent.parent.parent / "specs" / "001-perceived-agency-trust" / "contracts"

def load_schema(schema_name: str) -> dict:
    """Load a YAML schema file."""
    schema_path = CONTRACTS_DIR / schema_name
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def test_participant_schema_exists():
    """Verify participant schema file exists and is valid YAML."""
    schema = load_schema('participant.schema.yaml')
    assert 'participant_id' in schema
    assert 'condition' in schema
    assert 'trust_item_1' in schema
    assert 'trust_item_12' in schema
    assert schema['condition']['type'] == 'string'
    assert set(schema['condition']['enum']) == {'High', 'Low', 'Control'}

def test_analysis_output_schema_exists():
    """Verify analysis output schema file exists and is valid YAML."""
    schema = load_schema('analysis_output.schema.yaml')
    assert 'anova_results' in schema
    assert 'planned_contrasts' in schema
    assert 'post_hoc_tests' in schema
    assert 'effect_sizes' in schema
    assert 'power_analysis' in schema

def test_power_analysis_schema_exists():
    """Verify power analysis schema file exists and is valid YAML."""
    schema = load_schema('power_analysis.schema.yaml')
    assert 'parameters' in schema
    assert 'results' in schema
    assert 'metadata' in schema
    assert schema['parameters']['properties']['groups']['const'] == 3

def test_trust_items_count():
    """Verify exactly 12 trust items are defined in participant schema."""
    schema = load_schema('participant.schema.yaml')
    trust_items = [k for k in schema.keys() if k.startswith('trust_item_')]
    assert len(trust_items) == 12
    for i in range(1, 13):
        assert f'trust_item_{i}' in schema

def test_schema_structure_consistency():
    """Verify all schemas have required top-level keys."""
    participant_schema = load_schema('participant.schema.yaml')
    analysis_schema = load_schema('analysis_output.schema.yaml')
    power_schema = load_schema('power_analysis.schema.yaml')

    # Check participant schema has all required fields
    required_participant_fields = ['participant_id', 'condition', 'adherence_rate',
                                  'trust_score', 'attention_check', 'perceived_agency_score']
    for field in required_participant_fields:
        assert field in participant_schema, f"Missing required field: {field}"

    # Check analysis schema has all required sections
    required_analysis_sections = ['anova_results', 'planned_contrasts', 'post_hoc_tests',
                                 'effect_sizes', 'power_analysis']
    for section in required_analysis_sections:
        assert section in analysis_schema, f"Missing required section: {section}"

    # Check power analysis schema structure
    assert 'parameters' in power_schema
    assert 'results' in power_schema
    assert 'metadata' in power_schema