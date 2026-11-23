import os
import sys
import pytest
import pandas as pd
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.causal_framing import generate_causal_framing_statement, find_interaction_term, format_coefficient, format_pvalue

class TestFindInteractionTerm:
    def test_find_interaction_term_exists(self):
        df = pd.DataFrame({
            'term': ['A', 'B', 'A*B*C', 'C'],
            'p_adj': [0.1, 0.2, 0.01, 0.3]
        })
        result = find_interaction_term(df, 'A*B*C')
        assert result is not None
        assert result['p_adj'] == 0.01

    def test_find_interaction_term_missing(self):
        df = pd.DataFrame({
            'term': ['A', 'B', 'C'],
            'p_adj': [0.1, 0.2, 0.3]
        })
        result = find_interaction_term(df, 'A*B*C')
        assert result is None

class TestFormatCoefficient:
    def test_format_coefficient_positive(self):
        assert format_coefficient(0.5) == "0.50"
        assert format_coefficient(0.1234) == "0.12"

    def test_format_coefficient_negative(self):
        assert format_coefficient(-0.5) == "-0.50"
        assert format_coefficient(-0.001) == "-0.00"

class TestFormatPvalue:
    def test_format_pvalue_small(self):
        assert format_pvalue(0.001) == "0.001"
        assert format_pvalue(0.0001) == "<0.001"

    def test_format_pvalue_large(self):
        assert format_pvalue(0.5) == "0.50"

class TestGenerateCausalFramingStatement:
    def test_generate_statement_significant(self):
        interaction = pd.Series({'coef': 0.5, 'p_adj': 0.01, 'term': 'A*B*C'})
        main_effects = [
            pd.Series({'coef': 0.1, 'p_adj': 0.05, 'term': 'A'}),
            pd.Series({'coef': 0.2, 'p_adj': 0.05, 'term': 'B'})
        ]
        
        statement = generate_causal_framing_statement(interaction, main_effects)
        
        assert "A*B*C" in statement
        assert "0.50" in statement
        assert "0.01" in statement
        assert "significant" in statement.lower()

    def test_generate_statement_insignificant(self):
        interaction = pd.Series({'coef': 0.5, 'p_adj': 0.5, 'term': 'A*B*C'})
        main_effects = []
        
        statement = generate_causal_framing_statement(interaction, main_effects)
        
        assert "not significant" in statement.lower()
