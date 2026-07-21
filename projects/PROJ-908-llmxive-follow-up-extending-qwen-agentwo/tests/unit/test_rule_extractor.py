"""
Unit tests for the Rule Extractor module (T021).

These tests verify that the RuleExtractor correctly parses CoT traces,
generalizes facts, and produces valid ExtractedRule objects with expected
properties (confidence, support, structure).
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from code.rules.extractor import RuleExtractor, ExtractedRule


@pytest.fixture
def sample_traces():
    """Fixture providing a small set of synthetic CoT traces for testing."""
    return [
        {
            "id": "trace_001",
            "steps": [
                {"thought": "I need to move to the kitchen because it is there.", "action": "move", "result": "kitchen"},
                {"thought": "The kitchen is the location for cooking.", "action": "observe", "result": "kitchen"}
            ]
        },
        {
            "id": "trace_002",
            "steps": [
                {"thought": "I need to move to the kitchen to get the ingredients.", "action": "move", "result": "kitchen"},
                {"thought": "Now I am in the kitchen.", "action": "observe", "result": "kitchen"}
            ]
        },
        {
            "id": "trace_003",
            "steps": [
                {"thought": "I need to go to the bedroom because I am tired.", "action": "move", "result": "bedroom"},
                {"thought": "The bedroom is for sleeping.", "action": "observe", "result": "bedroom"}
            ]
        },
        {
            "id": "trace_004",
            "steps": [
                {"thought": "I need to move to the kitchen.", "action": "move", "result": "kitchen"}
            ]
        }
    ]

@pytest.fixture
def extractor():
    """Fixture providing a configured RuleExtractor instance."""
    return RuleExtractor(min_support=2, min_confidence=0.5)

def test_parse_trace_to_facts(extractor, sample_traces):
    """Test that facts are correctly extracted from trace steps."""
    trace = sample_traces[0]
    facts = extractor._parse_trace_to_facts(trace)

    assert len(facts) > 0, "Expected at least one fact from a trace"
    # Check for spatial pattern
    spatial_facts = [f for f in facts if f['type'] == 'spatial']
    assert len(spatial_facts) >= 1, "Expected to detect spatial movement"

    # Check content
    for fact in spatial_facts:
        assert 'kitchen' in fact['content'].lower()
        assert fact['trace_id'] == 'trace_001'

def test_generalize_facts(extractor, sample_traces):
    """Test that facts are correctly grouped by pattern and content."""
    all_facts = []
    for trace in sample_traces:
        all_facts.extend(extractor._parse_trace_to_facts(trace))

    grouped = extractor._generalize_facts(all_facts)

    # We expect a group for "move to kitchen"
    # The key format is "{type}_{content}"
    spatial_keys = [k for k in grouped.keys() if k.startswith('spatial_')]
    assert len(spatial_keys) > 0, "Expected to find spatial groups"

    # Check that 'kitchen' appears in a group
    kitchen_groups = [k for k in spatial_keys if 'kitchen' in k]
    assert len(kitchen_groups) > 0, "Expected to find 'kitchen' in spatial groups"

def test_abstract_content(extractor):
    """Test that specific identifiers are abstracted to variables."""
    content = "move to room_A"
    abstracted = extractor._abstract_content(content)
    assert "Variable_Location" in abstracted
    assert "room_A" not in abstracted

    content = "item_sword_01"
    abstracted = extractor._abstract_content(content)
    assert "Variable_Item" in abstracted

def test_construct_rule_body(extractor):
    """Test that logical bodies are constructed from content."""
    content = "because it is there"
    body = extractor._construct_rule_body(content)
    assert isinstance(body, list)
    assert len(body) > 0
    assert all(isinstance(literal, str) for literal in body)
    assert "condition(" in body[0]

def test_extract_rules_returns_list(extractor, sample_traces):
    """Test that extract_rules returns a list of ExtractedRule objects."""
    rules = extractor.extract_rules(sample_traces)

    assert isinstance(rules, list)
    assert len(rules) > 0, "Expected at least one rule given sufficient support"

    for rule in rules:
        assert isinstance(rule, ExtractedRule)
        assert rule.rule_id.startswith("RULE_")
        assert rule.head is not None
        assert isinstance(rule.body, list)
        assert 0.0 <= rule.confidence <= 1.0
        assert rule.support_count >= extractor.min_support
        assert len(rule.source_trace_ids) > 0

def test_rule_confidence_calculation(extractor, sample_traces):
    """Test that confidence is calculated based on unique trace coverage."""
    rules = extractor.extract_rules(sample_traces)

    # Find a rule with known support
    # In our sample, "move to kitchen" appears in trace_001, trace_002, trace_004 (3 traces)
    # "move to bedroom" appears in trace_003 (1 trace, but min_support=2 so it might be filtered out)
    kitchen_rules = [r for r in rules if 'kitchen' in r.head.lower() or any('kitchen' in b.lower() for b in r.body)]

    if kitchen_rules:
        rule = kitchen_rules[0]
        # Confidence should be high because it spans multiple traces
        assert rule.support_count >= 2
        # With 3 traces and 3 occurrences (one per trace), confidence ~ 1.0
        # If repeated in one trace, confidence drops
        assert rule.confidence > 0.5, f"Expected high confidence for kitchen rule, got {rule.confidence}"

def test_extract_rules_min_support_filter(extractor, sample_traces):
    """Test that rules with support < min_support are excluded."""
    # Create a trace that appears only once
    unique_trace = {
        "id": "trace_unique",
        "steps": [
            {"thought": "I need to go to the attic.", "action": "move", "result": "attic"}
        ]
    }
    all_traces = sample_traces + [unique_trace]

    rules = extractor.extract_rules(all_traces)

    # The "attic" rule should not appear because it only has 1 support
    attic_rules = [r for r in rules if 'attic' in r.head.lower() or any('attic' in b.lower() for b in r.body)]
    assert len(attic_rules) == 0, "Expected 'attic' rule to be filtered out by min_support"

def test_main_function_creates_file(tmp_path, sample_traces):
    """Test that the main function writes the output file correctly."""
    input_file = tmp_path / "cot_traces.json"
    output_file = tmp_path / "extracted_rules.json"

    input_file.write_text(json.dumps(sample_traces))

    from code.rules.extractor import main

    main(
        input_path=str(input_file),
        output_path=str(output_file),
        min_support=2,
        min_confidence=0.5
    )

    assert output_file.exists(), "Output file should be created"

    with open(output_file, 'r') as f:
        data = json.load(f)

    assert "metadata" in data
    assert "rules" in data
    assert data["metadata"]["total_traces_processed"] == len(sample_traces)
    assert len(data["rules"]) > 0
