import pytest
from extraction import calculate_pronoun_density, calculate_narrator_distance_score
import os

def test_pronoun_density_first_person():
    text = "I went to the store. I bought milk. I was happy."
    result = calculate_pronoun_density(text)
    assert result['pronoun_density_1st'] > 0.0
    assert result['pronoun_density_3rd'] == 0.0

def test_pronoun_density_third_person():
    text = "He went to the store. He bought milk. He was happy."
    result = calculate_pronoun_density(text)
    assert result['pronoun_density_3rd'] > 0.0
    assert result['pronoun_density_1st'] == 0.0

def test_narrator_distance():
    text_1st = "I walked. I saw. I did."
    text_3rd = "He walked. He saw. He did."
    
    score_1st = calculate_narrator_distance_score(text_1st)
    score_3rd = calculate_narrator_distance_score(text_3rd)
    
    assert score_1st < score_3rd
