"""
Unit tests for the data extractor module.
"""
import pytest
from code.data.extractor import (
    extract_intervention_components,
    extract_social_skill_domain,
    extract_delivery_format,
    extract_blinding_status,
    extract_study_metadata
)

class TestExtractInterventionComponents:
    def test_detects_breathing(self):
        text = "The intervention includes daily breathing exercises."
        result = extract_intervention_components(text)
        assert "breathing" in result

    def test_detects_body_scan(self):
        text = "Participants engaged in body scan meditation."
        result = extract_intervention_components(text)
        assert "body scan" in result

    def test_detects_mindful_movement(self):
        text = "The program features mindful movement practices."
        result = extract_intervention_components(text)
        assert "mindful movement" in result

    def test_detects_mindful_eating(self):
        text = "Mindful eating techniques were taught to participants."
        result = extract_intervention_components(text)
        assert "mindful eating" in result

    def test_detects_multiple_components(self):
        text = "The intervention combines breathing exercises and body scan meditation."
        result = extract_intervention_components(text)
        assert "breathing" in result
        assert "body scan" in result

    def test_empty_text(self):
        result = extract_intervention_components(None)
        assert result == []

    def test_no_match(self):
        text = "The study focused on general health outcomes."
        result = extract_intervention_components(text)
        assert result == []

class TestExtractSocialSkillDomain:
    def test_communication_domain(self):
        text = "The study measured improvements in speech and language skills."
        result = extract_social_skill_domain(text)
        assert result == "communication"

    def test_peer_interaction_domain(self):
        text = "Participants showed improved peer interaction and group play."
        result = extract_social_skill_domain(text)
        assert result == "peer interaction"

    def test_emotional_regulation_domain(self):
        text = "The intervention targeted emotion regulation and tantrum reduction."
        result = extract_social_skill_domain(text)
        assert result == "emotional regulation"

    def test_mixed_domain(self):
        text = "The study assessed both speech skills and peer interaction abilities."
        result = extract_social_skill_domain(text)
        assert result == "mixed"

    def test_other_domain(self):
        text = "The study focused on general social skill development."
        result = extract_social_skill_domain(text)
        assert result == "other"

    def test_empty_text(self):
        result = extract_social_skill_domain(None)
        assert result == "other"

class TestExtractDeliveryFormat:
    def test_caregiver_mediated(self):
        text = "The intervention was caregiver-mediated with parent involvement."
        result = extract_delivery_format(text)
        assert result == "caregiver-mediated"

    def test_child_led(self):
        text = "The program was child-led and self-directed."
        result = extract_delivery_format(text)
        assert result == "child-led"

    def test_mixed_format(self):
        text = "The study included both caregiver-mediated and child-led components."
        result = extract_delivery_format(text)
        assert result == "mixed"

    def test_not_reported(self):
        text = "The study did not specify the delivery format."
        result = extract_delivery_format(text)
        assert result == "not-reported"

    def test_empty_text(self):
        result = extract_delivery_format(None)
        assert result == "not-reported"

class TestExtractBlindingStatus:
    def test_blinded(self):
        record = {
            "rater_type": "blinded",
            "blinded_assessment_flag": True
        }
        result = extract_blinding_status(record)
        assert result["rater_type"] == "blinded"
        assert result["blinded_assessment_flag"] is True

    def test_unblinded(self):
        record = {
            "rater_type": "unblinded",
            "blinded_assessment_flag": False
        }
        result = extract_blinding_status(record)
        assert result["rater_type"] == "unblinded"
        assert result["blinded_assessment_flag"] is False

    def test_unknown(self):
        record = {
            "rater_type": "unknown",
            "blinded_assessment_flag": False
        }
        result = extract_blinding_status(record)
        assert result["rater_type"] == "unknown"

class TestExtractStudyMetadata:
    def test_full_extraction(self):
        record = {
            "id": "test-001",
            "description": "A breathing and body scan intervention for peer interaction.",
            "abstract": "This study focuses on speech and language skills.",
            "intervention_components": ["breathing", "body scan"],
            "delivery_format": "caregiver-mediated",
            "rater_type": "blinded",
            "blinded_assessment_flag": True
        }
        result = extract_study_metadata(record)
        assert "breathing" in result["intervention_components"]
        assert "body scan" in result["intervention_components"]
        assert result["social_skill_domain"] in ["communication", "peer interaction", "mixed"]
        assert result["delivery_format"] == "caregiver-mediated"
        assert result["rater_type"] == "blinded"
        assert result["blinded_assessment_flag"] is True