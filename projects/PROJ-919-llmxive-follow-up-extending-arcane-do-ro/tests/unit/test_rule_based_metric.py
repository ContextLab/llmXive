"""
Unit tests for the rule-based metric adherence calculation.
"""

import pytest
from src.services.rule_based_metric import calculate_rule_based_adherence_flag, run_rule_based_evaluation


class TestRuleBasedMetric:
    
    def test_adherence_flag_true_two_keywords(self):
        """Test that adherence_flag is True when >= 2 keywords are found."""
        response = "The character began the story with a struggle against a challenge."
        prompt_phases = ["Initiation", "Confrontation"]
        
        # Keywords for Initiation: start, begin...
        # Keywords for Confrontation: conflict, challenge...
        
        adherence, count, found = calculate_rule_based_adherence_flag(
            response, 
            prompt_phases
        )
        
        assert adherence is True
        assert count >= 2
        assert "begin" in found or "start" in found
        assert "challenge" in found or "conflict" in found

    def test_adherence_flag_false_one_keyword(self):
        """Test that adherence_flag is False when only 1 keyword is found."""
        response = "The character began the story."
        prompt_phases = ["Initiation", "Confrontation"]
        
        adherence, count, found = calculate_rule_based_adherence_flag(
            response, 
            prompt_phases
        )
        
        assert adherence is False
        assert count == 1

    def test_adherence_flag_false_no_keywords(self):
        """Test that adherence_flag is False when no keywords are found."""
        response = "The sky was blue and the birds sang."
        prompt_phases = ["Initiation", "Confrontation"]
        
        adherence, count, found = calculate_rule_based_adherence_flag(
            response, 
            prompt_phases
        )
        
        assert adherence is False
        assert count == 0
        assert found == []

    def test_empty_response(self):
        """Test behavior with empty response."""
        response = ""
        prompt_phases = ["Initiation"]
        
        adherence, count, found = calculate_rule_based_adherence_flag(
            response, 
            prompt_phases
        )
        
        assert adherence is False
        assert count == 0

    def test_empty_phases(self):
        """Test behavior with empty phases list."""
        response = "The character began the story."
        prompt_phases = []
        
        adherence, count, found = calculate_rule_based_adherence_flag(
            response, 
            prompt_phases
        )
        
        assert adherence is False
        assert count == 0

    def test_run_rule_based_evaluation_integration(self):
        """Test the wrapper function run_rule_based_evaluation."""
        response = "The story started with a conflict."
        prompt_data = {
            "phases": ["Initiation", "Confrontation"],
            "other_data": "irrelevant"
        }
        
        result = run_rule_based_evaluation(response, prompt_data)
        
        assert "rule_based_adherence_flag" in result
        assert "rule_based_match_count" in result
        assert "rule_based_found_keywords" in result
        assert result["rule_based_adherence_flag"] is True
        assert result["rule_based_match_count"] >= 2