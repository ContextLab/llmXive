"""
Unit tests for the data extractor module.

Tests regex pattern matching for mindfulness components, delivery formats,
and social skill domains.
"""

import pytest
from code.data.extractor import (
    extract_mindfulness_components,
    extract_delivery_format,
    extract_social_skill_domains,
    extract_study_metadata
)
from code.data.models import MindfulnessComponent, DeliveryFormat, SocialSkillDomain

class TestMindfulnessComponentExtraction:
    def test_breathing_pattern(self):
        text = "The intervention included breathing exercises and meditation."
        components = extract_mindfulness_components(text)
        assert MindfulnessComponent.BREATHING in components
        assert MindfulnessComponent.MEDITATION in components

    def test_body_scan_pattern(self):
        text = "Participants practiced body scan meditation daily."
        components = extract_mindfulness_components(text)
        assert MindfulnessComponent.BODY_SCAN in components

    def test_yoga_pattern(self):
        text = "The program incorporated yoga and mindful movement."
        components = extract_mindfulness_components(text)
        assert MindfulnessComponent.YOGA in components
        assert MindfulnessComponent.MINDFUL_MOVEMENT in components

    def test_loving_kindness_pattern(self):
        text = "Loving kindness meditation was a key component."
        components = extract_mindfulness_components(text)
        assert MindfulnessComponent.LOVING_KINDNESS in components

    def test_generic_fallback(self):
        text = "This mindfulness program was effective."
        components = extract_mindfulness_components(text)
        assert MindfulnessComponent.GENERIC in components

    def test_no_components(self):
        text = "This is a control group with no mindfulness intervention."
        components = extract_mindfulness_components(text)
        assert len(components) == 0

class TestDeliveryFormatExtraction:
    def test_individual_format(self):
        text = "The intervention was delivered on a one-on-one basis."
        formats = extract_delivery_format(text)
        assert DeliveryFormat.INDIVIDUAL in formats

    def test_group_format(self):
        text = "Participants attended group sessions twice weekly."
        formats = extract_delivery_format(text)
        assert DeliveryFormat.GROUP in formats

    def test_online_format(self):
        text = "The program was delivered via an online platform."
        formats = extract_delivery_format(text)
        assert DeliveryFormat.ONLINE in formats

    def test_hybrid_format(self):
        text = "A hybrid model combining in-person and virtual sessions."
        formats = extract_delivery_format(text)
        assert DeliveryFormat.HYBRID in formats

class TestSocialSkillDomainExtraction:
    def test_communication_domain(self):
        text = "The study measured improvements in communication skills."
        domains = extract_social_skill_domains(text)
        assert SocialSkillDomain.COMMUNICATION in domains

    def test_empathy_domain(self):
        text = "Participants showed increased empathetic responses."
        domains = extract_social_skill_domains(text)
        assert SocialSkillDomain.EMPATHY in domains

    def test_peer_relationships_domain(self):
        text = "Peer relationships were assessed through observation."
        domains = extract_social_skill_domains(text)
        assert SocialSkillDomain.PEER_RELATIONSHIPS in domains

    def test_emotional_regulation_domain(self):
        text = "Emotional regulation was a primary outcome measure."
        domains = extract_social_skill_domains(text)
        assert SocialSkillDomain.EMOTIONAL_REGULATION in domains

class TestStudyMetadataExtraction:
    def test_complete_study_extraction(self):
        study_data = {
            "nct_id": "NCT01234567",
            "title": "Mindfulness for ASD",
            "abstract": "This study examines mindfulness effects on social skills.",
            "intervention_description": "Breathing exercises and group sessions.",
            "age_criteria": "6 to 12 years",
            "source": "ClinicalTrials.gov"
        }
        
        study = extract_study_metadata(study_data)
        
        assert study is not None
        assert study.nct_id == "NCT01234567"
        assert study.title == "Mindfulness for ASD"
        assert MindfulnessComponent.BREATHING in study.mindfulness_components
        assert DeliveryFormat.GROUP in study.delivery_formats
        assert study.min_age == 6
        assert study.max_age == 12

    def test_missing_fields(self):
        study_data = {
            "nct_id": "NCT01234567",
            "title": "Incomplete Study",
            # Missing other fields
        }
        
        study = extract_study_metadata(study_data)
        
        assert study is not None
        assert study.nct_id == "NCT01234567"
        assert study.mindfulness_components == []
        assert study.delivery_formats == []

    def test_invalid_data(self):
        study_data = {}
        study = extract_study_metadata(study_data)
        
        assert study is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])