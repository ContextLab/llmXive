import pytest
import sys
from pathlib import Path
import textstat
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.logger import setup_logger

logger = setup_logger("test_stimuli")

def test_readability_check():
    """
    Test that the readability difference (Flesch-Kincaid) between two vignettes is <= 2.0.
    This test verifies the constraint FR-001.
    """
    # Example texts (simulating generated output)
    text_a = "Imagine you are working on a collaborative project with an AI system. This system is designed to act as a Partner, working alongside you as an equal team member. It contributes ideas, challenges your assumptions, and shares responsibility for the outcome. You interact with it as you would with a human colleague, trusting its input as part of a shared goal."
    
    text_b = "Imagine you are working on a project and using an AI system as a Tool. This system is designed to assist you by performing specific tasks efficiently. It processes data, generates drafts, and provides information when requested. You control the workflow, directing the tool to execute commands and produce outputs as needed."

    fk_a = textstat.flesch_kincaid_grade(text_a)
    fk_b = textstat.flesch_kincaid_grade(text_b)
    
    diff = abs(fk_a - fk_b)
    logger.info(f"Flesch-Kincaid Grade A: {fk_a}, B: {fk_b}, Diff: {diff}")
    
    assert diff <= 2.0, f"Flesch-Kincaid difference {diff:.2f} exceeds the allowed limit of 2.0."

def test_sentiment_check():
    """
    Test that the sentiment difference (VADER compound) between two vignettes is <= 0.05.
    This test verifies the constraint FR-010.
    """
    # Example texts (simulating generated output)
    text_a = "Imagine you are working on a collaborative project with an AI system. This system is designed to act as a Partner, working alongside you as an equal team member. It contributes ideas, challenges your assumptions, and shares responsibility for the outcome. You interact with it as you would with a human colleague, trusting its input as part of a shared goal."
    
    text_b = "Imagine you are working on a project and using an AI system as a Tool. This system is designed to assist you by performing specific tasks efficiently. It processes data, generates drafts, and provides information when requested. You control the workflow, directing the tool to execute commands and produce outputs as needed."

    sentiment = SentimentIntensityAnalyzer()
    score_a = sentiment.polarity_scores(text_a)['compound']
    score_b = sentiment.polarity_scores(text_b)['compound']
    
    diff = abs(score_a - score_b)
    logger.info(f"VADER Compound A: {score_a}, B: {score_b}, Diff: {diff}")
    
    assert diff <= 0.05, f"VADER sentiment difference {diff:.2f} exceeds the allowed limit of 0.05."

def test_file_existence():
    """
    Verify that the generated vignette files exist in the expected location.
    """
    base_path = Path(__file__).parent.parent / "data" / "stimuli"
    partner_file = base_path / "vignettes_partner.csv"
    tool_file = base_path / "vignettes_tool.csv"
    
    assert partner_file.exists(), f"Partner vignette file not found: {partner_file}"
    assert tool_file.exists(), f"Tool vignette file not found: {tool_file}"

def test_csv_structure():
    """
    Verify that the generated CSV files have the correct structure.
    """
    import csv
    base_path = Path(__file__).parent.parent / "data" / "stimuli"
    
    for filename in ["vignettes_partner.csv", "vignettes_tool.csv"]:
        file_path = base_path / filename
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ["condition", "vignette_text"], f"Invalid header in {filename}: {header}"
            
            rows = list(reader)
            assert len(rows) == 1, f"Expected 1 row in {filename}, found {len(rows)}"
            condition, text = rows[0]
            assert condition in ["partner", "tool"], f"Invalid condition in {filename}: {condition}"
            assert len(text) > 50, f"Vignette text in {filename} is too short."