import pytest
import tempfile
import os
from pathlib import Path
import sys
import json

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.bias_pipeline.extractor import (
    analyze_sentiment, 
    extract_code_elements, 
    analyze_file,
    normalize_tokens
)

class TestAnalyzeSentiment:
    """Unit tests for VADER sentiment analysis function."""
    
    def test_empty_comments(self):
        """Test that empty comment list returns neutral scores."""
        result = analyze_sentiment([])
        assert result['compound'] == 0.0
        assert result['positive'] == 0.0
        assert result['negative'] == 0.0
        assert result['neutral'] == 0.0
        assert result['avg_score'] == 0.0
    
    def test_positive_comment(self):
        """Test detection of positive sentiment."""
        comments = ["This is a great feature!"]
        result = analyze_sentiment(comments)
        assert result['compound'] > 0.5  # Should be strongly positive
        assert result['positive'] > result['negative']
    
    def test_negative_comment(self):
        """Test detection of negative sentiment."""
        comments = ["This code is terrible and buggy."]
        result = analyze_sentiment(comments)
        assert result['compound'] < -0.5  # Should be strongly negative
        assert result['negative'] > result['positive']
    
    def test_neutral_comment(self):
        """Test detection of neutral sentiment."""
        comments = ["The variable x is defined here."]
        result = analyze_sentiment(comments)
        # Neutral comments should have compound score near 0
        assert abs(result['compound']) < 0.3
    
    def test_mixed_comments(self):
        """Test averaging of mixed sentiment comments."""
        comments = [
            "This is amazing!",
            "This is awful."
        ]
        result = analyze_sentiment(comments)
        # Should average out, but not necessarily exactly 0
        assert -0.5 < result['compound'] < 0.5
    
    def test_code_comment_extraction_and_sentiment(self):
        """Test end-to-end: extract comments from code and analyze sentiment."""
        code = '''
        # This is a helpful comment for users
        def calculate_sum(a, b):
            # This function adds two numbers together
            return a + b
        
        # WARNING: This code is dangerous and should not be used
        dangerous_function = lambda x: x / 0
        '''
        
        elements = extract_code_elements(code)
        assert len(elements['comments']) >= 2
        
        sentiment = analyze_sentiment(elements['comments'])
        assert 'compound' in sentiment
        assert 'positive' in sentiment
        assert 'negative' in sentiment
    
    def test_special_characters_in_comments(self):
        """Test that special characters don't break sentiment analysis."""
        comments = [
            "Check this out: $100, 50% off!!!",
            "Error: <404> not found @server"
        ]
        result = analyze_sentiment(comments)
        # Should not crash and should return valid scores
        assert isinstance(result['compound'], float)
        assert -1.0 <= result['compound'] <= 1.0

class TestSentimentThresholds:
    """Test VADER threshold behavior as per FR-003."""
    
    def test_positive_threshold(self):
        """Test that clearly positive comments exceed positive threshold."""
        # VADER considers compound >= 0.05 as positive
        comments = ["Excellent work!"]
        result = analyze_sentiment(comments)
        assert result['compound'] >= 0.05
    
    def test_negative_threshold(self):
        """Test that clearly negative comments exceed negative threshold."""
        # VADER considers compound <= -0.05 as negative
        comments = ["Terrible implementation."]
        result = analyze_sentiment(comments)
        assert result['compound'] <= -0.05
    
    def test_neutral_threshold(self):
        """Test that neutral comments fall within neutral range."""
        comments = ["Variable name is x."]
        result = analyze_sentiment(comments)
        assert -0.05 < result['compound'] < 0.05