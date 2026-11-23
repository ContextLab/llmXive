"""
Unit tests for alternative cue definition logic in sensitivity analysis.

Tests the structural definitions of "Cue Intensity" as specified in T027:
- Conjunctive: High Emoji AND High Punctuation
- Disjunctive: High Emoji OR High Punctuation
- Threshold-based: Weighted sum exceeding a threshold

These tests verify the logic before the full sensitivity analysis engine (T028) is implemented.
"""

import pytest
import json
from pathlib import Path
import sys

# Add the code directory to the path for imports
# Note: In a real execution environment, this would be handled by PYTHONPATH or setup.py
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import get_processed_data_dir

# Helper functions to simulate the logic that will be in 05_sensitivity_analysis.py
# These are the "alternative cue definition logic" functions being tested

def calculate_emoji_intensity(text: str) -> float:
    """Calculate emoji intensity based on emoji count."""
    emoji_chars = set('😀😁😂🤣😃😄😅😆😉😊😋😎😍😘🥰😗😙😚☺️🙂🤗🤩🤔🤨😐😑😶🙄😏😣😥😮🤐😯😪😫😴😌😛😜😝🤤😒😓😔😕🙃🤑😲☹️🙁😖😞😟😤😢😭😦😧😨😩🤯😬😰😱🥵🥶😳🤪😵😡😠🤬😷🤒🤕🤢🤮🤧😇🤠🤡🥳🥴🥺🤥🤫🤭🧐🤓😈👿🤠👹👺🤖💩👻💀☠️👽👾🤟🤘🤙👋🤚🖐️✋🖖👌🤏👍👎✊🤛🤜👊🤞✌️🤟🤘👈👉👆🖕👇☝️👏🙌👐🤲🤝🙏✍️💅🤳💪🦾🦿🦵🦶👂🦻👃🧠🫀🫁🦷🦴👀👁️👅👄👶🧒👦👧🧑👱👨🧔👨🏻👨🏼👨🏽👨🏾👨🏿👩👩🏻👩🏼👩🏽👩🏾👩🏿🧑🏻🧑🏼🧑🏽🧑🏾🧑🏿👱🏻👱🏼👱🏽👱🏾👱🏿👨‍🦱👨‍🦱🏻👨‍🦱🏼👨‍🦱🏽👨‍🦱🏾👨‍🦱🏿👩‍🦱👩‍🦱🏻👩‍🦱🏼👩‍🦱🏽👩‍🦱🏾👩‍🦱🏿🧑‍🦱🧑‍🦱🏻🧑‍🦱🏼🧑‍🦱🏽🧑‍🦱🏾🧑‍🦱🏿👨‍🦰👨‍🦰🏻👨‍🦰🏼👨‍🦰🏽👨‍🦰🏾👨‍🦰🏿👩‍🦰👩‍🦰🏻👩‍🦰🏼👩‍🦰🏽👩‍🦰🏾👩‍🦰🏿🧑‍🦰🧑‍🦰🏻🧑‍🦰🏼🧑‍🦰🏽🧑‍🦰🏾🧑‍🦰🏿👨‍🦳👨‍🦳🏻👨‍🦳🏼👨‍🦳🏽👨‍🦳🏾👨‍🦳🏿👩‍🦳👩‍🦳🏻👩‍🦳🏼👩‍🦳🏽👩‍🦳🏾👩‍🦳🏿🧑‍🦳🧑‍🦳🏻🧑‍🦳🏼🧑‍🦳🏽🧑‍🦳🏾🧑‍🦳🏿👨‍🦲👨‍🦲🏻👨‍🦲🏼👨‍🦲🏽👨‍🦲🏾👨‍🦲🏿👩‍🦲👩‍🦲🏻👩‍🦲🏼👩‍🦲🏽👩‍🦲🏾👩‍🦲🏿🧑‍🦲🧑‍🦲🏻🧑‍🦲🏼🧑‍🦲🏽🧑‍🦲🏾🧑‍🦲🏿👱🏻‍♀️👱🏼‍♀️👱🏽‍♀️👱🏾‍♀️👱🏿‍♀️👱🏻‍♂️👱🏼‍♂️👱🏽‍♂️👱🏾‍♂️👱🏿‍♂️🧔🏻🧔🏼🧔🏽🧔🏾🧔🏿🧔🏻‍♀️🧔🏼‍♀️🧔🏽‍♀️🧔🏾‍♀️🧔🏿‍♀️🧔🏻‍♂️🧔🏼‍♂️🧔🏽‍♂️🧔🏾‍♂️🧔🏿‍♂️👵👵🏻👵🏼👵🏽👵🏾👵🏿👴👴🏻👴🏼👴🏽👴🏾👴🏿👲👲🏻👲🏼👲🏽👲🏾👲🏿👳👳🏻👳🏼👳🏽👳🏾👳🏿👳🏻‍♀️👳🏼‍♀️👳🏽‍♀️👳🏾‍♀️👳🏿‍♀️👳🏻‍♂️👳🏼‍♂️👳🏽‍♂️👳🏾‍♂️👳🏿‍♂️🧕🧕🏻🧕🏼🧕🏽🧕🏾🧕🏿🧕🏻‍♀️🧕🏼‍♀️🧕🏽‍♀️🧕🏾‍♀️🧕🏿‍♀️🧕🏻‍♂️🧕🏼‍♂️🧕🏽‍♂️🧕🏾‍♂️🧕🏿‍♂️👮👮🏻👮🏼👮🏽👮🏾👮🏿👮🏻‍♀️👮🏼‍♀️👮🏽‍♀️👮🏾‍♀️👮🏿‍♀️👮🏻‍♂️👮🏼‍♂️👮🏽‍♂️👮🏾‍♂️👮🏿‍♂️👷👷🏻👷🏼👷🏽👷🏾👷🏿👷🏻‍♀️👷🏼‍♀️👷🏽‍♀️👷🏾‍♀️👷🏿‍♀️👷🏻‍♂️👷🏼‍♂️👷🏽‍♂️👷🏾‍♂️👷🏿‍♂️💂💂🏻💂🏼💂🏽💂🏾💂🏿💂🏻‍♀️💂🏼‍♀️💂🏽‍♀️💂🏾‍♀️💂🏿‍♀️💂🏻‍♂️💂🏼‍♂️💂🏽‍♂️💂🏾‍♂️💂🏿‍♂️🕵️🕵️🏻🕵️🏼🕵️🏽🕵️🏾🕵️🏿🕵️🏻‍♀️🕵️🏼‍♀️🕵️🏽‍♀️🕵️🏾‍♀️🕵️🏿‍♀️🕵️🏻‍♂️🕵️🏼‍♂️🕵️🏽‍♂️🕵️🏾‍♂️🕵️🏿‍♂️👩‍⚕️👩‍⚕️🏻👩‍⚕️🏼👩‍⚕️🏽👩‍⚕️🏾👩‍⚕️🏿👨‍⚕️👨‍⚕️🏻👨‍⚕️🏼👨‍⚕️🏽👨‍⚕️🏾👨‍⚕️🏿🧑‍⚕️🧑‍⚕️🏻🧑‍⚕️🏼🧑‍⚕️🏽🧑‍⚕️🏾🧑‍⚕️🏿👩‍🌾👩‍🌾🏻👩‍🌾🏼👩‍🌾🏽👩‍🌾🏾👩‍🌾🏿👨‍🌾👨‍🌾🏻👨‍🌾🏼👨‍🌾🏽👨‍🌾🏾👨‍🌾🏿🧑‍🌾🧑‍🌾🏻🧑‍🌾🏼🧑‍🌾🏽🧑‍🌾🏾🧑‍🌾🏿👩‍🍳👩‍🍳🏻👩‍🍳🏼👩‍🍳🏽👩‍🍳🏾👩‍🍳🏿👨‍🍳👨‍🍳🏻👨‍🍳🏼👨‍🍳🏽👨‍🍳🏾👨‍🍳🏿🧑‍🍳🧑‍🍳🏻🧑‍🍳🏼🧑‍🍳🏽🧑‍🍳🏾🧑‍🍳🏿👩‍🎓👩‍🎓🏻👩‍🎓🏼👩‍🎓🏽👩‍🎓🏾👩‍🎓🏿👨‍🎓👨‍🎓🏻👨‍🎓🏼👨‍🎓🏽👨‍🎓🏾👨‍🎓🏿🧑‍🎓🧑‍🎓🏻🧑‍🎓🏼🧑‍🎓🏽🧑‍🎓🏾🧑‍🎓🏿👩‍🎤👩‍🎤🏻👩‍🎤🏼👩‍🎤🏽👩‍🎤🏾👩‍🎤🏿👨‍🎤👨‍🎤🏻👨‍🎤🏼👨‍🎤🏽👨‍🎤🏾👨‍🎤🏿🧑‍🎤🧑‍🎤🏻🧑‍🎤🏼🧑‍🎤🏽🧑‍🎤🏾🧑‍🎤🏿👩‍🏫👩‍🏫🏻👩‍🏫🏼👩‍🏫🏽👩‍🏫🏾👩‍🏫🏿👨‍🏫👨‍🏫🏻👨‍🏫🏼👨‍🏫🏽👨‍🏫🏾👨‍🏫🏿🧑‍🏫🧑‍🏫🏻🧑‍🏫🏼🧑‍🏫🏽🧑‍🏫🏾🧑‍🏫🏿👩‍🏭👩‍🏭🏻👩‍🏭🏼👩‍🏭🏽👩‍🏭🏾👩‍🏭🏿👨‍🏭👨‍🏭🏻👨‍🏭🏼👨‍🏭🏽👨‍🏭🏾👨‍🏭🏿🧑‍🏭🧑‍🏭🏻🧑‍🏭🏼🧑‍🏭🏽🧑‍🏭🏾🧑‍🏭🏿👩‍💼👩‍💼🏻👩‍💼🏼👩‍💼🏽👩‍💼🏾👩‍💼🏿👨‍💼👨‍💼🏻👨‍💼🏼👨‍💼🏽👨‍💼🏾👨‍💼🏿🧑‍💼🧑‍💼🏻🧑‍💼🏼🧑‍💼🏽🧑‍💼🏾🧑‍💼🏿👩‍🔧👩‍🔧🏻👩‍🔧🏼👩‍🔧🏽👩‍🔧🏾👩‍🔧🏿👨‍🔧👨‍🔧🏻👨‍🔧🏼👨‍🔧🏽👨‍🔧🏾👨‍🔧🏿🧑‍🔧🧑‍🔧🏻🧑‍🔧🏼🧑‍🔧🏽🧑‍🔧🏾🧑‍🔧🏿👩‍🔬👩‍🔬🏻👩‍🔬🏼👩‍🔬🏽👩‍🔬🏾👩‍🔬🏿👨‍🔬👨‍🔬🏻👨‍🔬🏼👨‍🔬🏽👨‍🔬🏾👨‍🔬🏿🧑‍🔬🧑‍🔬🏻🧑‍🔬🏼🧑‍🔬🏽🧑‍🔬🏾🧑‍🔬🏿👩‍💻👩‍💻🏻👩‍💻🏼👩‍💻🏽👩‍💻🏾👩‍💻🏿👨‍💻👨‍💻🏻👨‍💻🏼👨‍💻🏽👨‍💻🏾👨‍💻🏿🧑‍💻🧑‍💻🏻🧑‍💻🏼🧑‍💻🏽🧑‍💻🏾🧑‍💻🏿👩‍🎨👩‍🎨🏻👩‍🎨🏼👩‍🎨🏽👩‍🎨🏾👩‍🎨🏿👨‍🎨👨‍🎨🏻👨‍🎨🏼👨‍🎨🏽👨‍🎨🏾👨‍🎨🏿🧑‍🎨🧑‍🎨🏻🧑‍🎨🏼🧑‍🎨🏽🧑‍🎨🏾🧑‍🎨🏿👩‍🚀👩‍🚀🏻👩‍🚀🏼👩‍🚀🏽👩‍🚀🏾👩‍🚀🏿👨‍🚀👨‍🚀🏻👨‍🚀🏼👨‍🚀🏽👨‍🚀🏾👨‍🚀🏿🧑‍🚀🧑‍🚀🏻🧑‍🚀🏼🧑‍🚀🏽🧑‍🚀🏾🧑‍🚀🏿👩‍🚒👩‍🚒🏻👩‍🚒🏼👩‍🚒🏽👩‍🚒🏾👩‍🚒🏿👨‍🚒👨‍🚒🏻👨‍🚒🏼👨‍🚒🏽👨‍🚒🏾👨‍🚒🏿🧑‍🚒🧑‍🚒🏻🧑‍🚒🏼🧑‍🚒🏽🧑‍🚒🏾🧑‍🚒🏿👮👮🏻👮🏼👮🏽👮🏾👮🏿👮🏻‍♀️👮🏼‍♀️👮🏽‍♀️👮🏾‍♀️👮🏿‍♀️👮🏻‍♂️👮🏼‍♂️👮🏽‍♂️👮🏾‍♂️👮🏿‍♂️🕵️🕵️🏻🕵️🏼🕵️🏽🕵️🏾🕵️🏿🕵️🏻‍♀️🕵️🏼‍♀️🕵️🏽‍♀️🕵️🏾‍♀️🕵️🏿‍♀️🕵️🏻‍♂️🕵️🏼‍♂️🕵️🏽‍♂️🕵️🏾‍♂️🕵️🏿‍♂️💂💂🏻💂🏼💂🏽💂🏾💂🏿💂🏻‍♀️💂🏼‍♀️💂🏽‍♀️💂🏾‍♀️💂🏿‍♀️💂🏻‍♂️💂🏼‍♂️💂🏽‍♂️💂🏾‍♂️💂🏿‍♂️👷👷🏻👷🏼👷🏽👷🏾👷🏿👷🏻‍♀️👷🏼‍♀️👷🏽‍♀️👷🏾‍♀️👷🏿‍♀️👷🏻‍♂️👷🏼‍♂️👷🏽‍♂️👷🏾‍♂️👷🏿‍♂️🤴🤴🏻🤴🏼🤴🏽🤴🏾🤴🏿👸👸🏻👸🏼👸🏽👸🏾👸🏿👳👳🏻👳🏼👳🏽👳🏾👳🏿👳🏻‍♀️👳🏼‍♀️👳🏽‍♀️👳🏾‍♀️👳🏿‍♀️👳🏻‍♂️👳🏼‍♂️👳🏽‍♂️👳🏾‍♂️👳🏿‍♂️👲👲🏻👲🏼👲🏽👲🏾👲🏿🧕🧕🏻🧕🏼🧕🏽🧕🏾🧕🏿🧕🏻‍♀️🧕🏼‍♀️🧕🏽‍♀️🧕🏾‍♀️🧕🏿‍♀️🧕🏻‍♂️🧕🏼‍♂️🧕🏽‍♂️🧕🏾‍♂️🧕🏿‍♂️👮👮🏻👮🏼👮🏽👮🏾👮🏿👮🏻‍♀️👮🏼‍♀️👮🏽‍♀️👮🏾‍♀️👮🏿‍♀️👮🏻‍♂️👮🏼‍♂️👮🏽‍♂️👮🏾‍♂️👮🏿‍♂️🕵️🕵️🏻🕵️🏼🕵️🏽🕵️🏾🕵️🏿🕵️🏻‍♀️🕵️🏼‍♀️🕵️🏽‍♀️🕵️🏾‍♀️🕵️🏿‍♀️🕵️🏻‍♂️🕵️🏼‍♂️🕵️🏽‍♂️🕵️🏾‍♂️🕵️🏿‍♂️💂💂🏻💂🏼💂🏽💂🏾💂🏿💂🏻‍♀️💂🏼‍♀️💂🏽‍♀️💂🏾‍♀️💂🏿‍♀️💂🏻‍♂️💂🏼‍♂️💂🏽‍♂️💂🏾‍♂️💂🏿‍♂️👷👷🏻👷🏼👷🏽👷🏾👷🏿👷🏻‍♀️👷🏼‍♀️👷🏽‍♀️👷🏾‍♀️👷🏿‍♀️👷🏻‍♂️👷🏼‍♂️👷🏽‍♂️👷🏾‍♂️👷🏿‍♂️🤴🤴🏻🤴🏼🤴🏽🤴🏾🤴🏿👸👸🏻👸🏼👸🏽👸🏾👸🏿👳👳🏻👳🏼👳🏽👳🏾👳🏿👳🏻‍♀️👳🏼‍♀️👳🏽‍♀️👳🏾‍♀️👳🏿‍♀️👳🏻‍♂️👳🏼‍♂️👳🏽‍♂️👳🏾‍♂️👳🏿‍♂️👲👲🏻👲🏼👲🏽👲🏾👲🏿🧕🧕🏻🧕🏼🧕🏽🧕🏾🧕🏿🧕🏻‍♀️🧕🏼‍♀️🧕🏽‍♀️🧕🏾‍♀️🧕🏿‍♀️🧕🏻‍♂️🧕🏼‍♂️🧕🏽‍♂️🧕🏾‍♂️🧕🏿‍♂️')
    count = sum(1 for char in text if char in emoji_chars)
    # Normalize to 0-1 range (assuming max 5 emojis is "high")
    return min(count / 5.0, 1.0)

def calculate_punctuation_intensity(text: str) -> float:
    """Calculate punctuation intensity based on exclamation/question marks."""
    punct_chars = set('!?!?')
    count = sum(1 for char in text if char in punct_chars)
    # Normalize to 0-1 range (assuming max 5 punctuation marks is "high")
    return min(count / 5.0, 1.0)

def conjunctive_definition(emoji_intensity: float, punct_intensity: float, threshold: float = 0.5) -> bool:
    """
    Conjunctive definition: High Emoji AND High Punctuation.
    Returns True if both intensities exceed the threshold.
    """
    return emoji_intensity > threshold and punct_intensity > threshold

def disjunctive_definition(emoji_intensity: float, punct_intensity: float, threshold: float = 0.5) -> bool:
    """
    Disjunctive definition: High Emoji OR High Punctuation.
    Returns True if at least one intensity exceeds the threshold.
    """
    return emoji_intensity > threshold or punct_intensity > threshold

def threshold_based_definition(emoji_intensity: float, punct_intensity: float, 
                             emoji_weight: float = 0.4, punct_weight: float = 0.6,
                             threshold: float = 0.5) -> bool:
    """
    Threshold-based definition: Weighted sum of intensities exceeds threshold.
    Formula: (emoji_weight * emoji_intensity) + (punct_weight * punct_intensity) > threshold
    """
    weighted_sum = (emoji_weight * emoji_intensity) + (punct_weight * punct_intensity)
    return weighted_sum > threshold

class TestConjunctiveDefinition:
    """Tests for the conjunctive (AND) cue definition logic."""

    def test_both_high_returns_true(self):
        """Both high emoji and high punctuation should return True."""
        result = conjunctive_definition(0.8, 0.9, threshold=0.5)
        assert result is True

    def test_one_high_returns_false(self):
        """If only one is high, should return False."""
        result1 = conjunctive_definition(0.8, 0.3, threshold=0.5)
        result2 = conjunctive_definition(0.3, 0.9, threshold=0.5)
        assert result1 is False
        assert result2 is False

    def test_both_low_returns_false(self):
        """If both are low, should return False."""
        result = conjunctive_definition(0.2, 0.3, threshold=0.5)
        assert result is False

    def test_exact_threshold_boundary(self):
        """At exactly the threshold, should return False (strictly greater)."""
        result = conjunctive_definition(0.5, 0.5, threshold=0.5)
        assert result is False

class TestDisjunctiveDefinition:
    """Tests for the disjunctive (OR) cue definition logic."""

    def test_both_high_returns_true(self):
        """Both high should return True."""
        result = disjunctive_definition(0.8, 0.9, threshold=0.5)
        assert result is True

    def test_one_high_returns_true(self):
        """If at least one is high, should return True."""
        result1 = disjunctive_definition(0.8, 0.3, threshold=0.5)
        result2 = disjunctive_definition(0.3, 0.9, threshold=0.5)
        assert result1 is True
        assert result2 is True

    def test_both_low_returns_false(self):
        """If both are low, should return False."""
        result = disjunctive_definition(0.2, 0.3, threshold=0.5)
        assert result is False

    def test_exact_threshold_boundary(self):
        """At exactly the threshold, should return False (strictly greater)."""
        result = disjunctive_definition(0.5, 0.5, threshold=0.5)
        assert result is False

class TestThresholdBasedDefinition:
    """Tests for the threshold-based (weighted sum) cue definition logic."""

    def test_high_weighted_sum_returns_true(self):
        """High weighted sum should return True."""
        # 0.4 * 0.8 + 0.6 * 0.9 = 0.32 + 0.54 = 0.86 > 0.5
        result = threshold_based_definition(0.8, 0.9, emoji_weight=0.4, punct_weight=0.6, threshold=0.5)
        assert result is True

    def test_low_weighted_sum_returns_false(self):
        """Low weighted sum should return False."""
        # 0.4 * 0.2 + 0.6 * 0.3 = 0.08 + 0.18 = 0.26 < 0.5
        result = threshold_based_definition(0.2, 0.3, emoji_weight=0.4, punct_weight=0.6, threshold=0.5)
        assert result is False

    def test_mixed_values_boundary(self):
        """Test boundary case where weighted sum is exactly at threshold."""
        # 0.4 * 0.5 + 0.6 * 0.5 = 0.2 + 0.3 = 0.5 (exactly at threshold)
        result = threshold_based_definition(0.5, 0.5, emoji_weight=0.4, punct_weight=0.6, threshold=0.5)
        assert result is False  # Strictly greater than

    def test_custom_weights(self):
        """Test with different weight configurations."""
        # Emphasize emoji: 0.8 * 0.9 + 0.2 * 0.3 = 0.72 + 0.06 = 0.78 > 0.5
        result = threshold_based_definition(0.9, 0.3, emoji_weight=0.8, punct_weight=0.2, threshold=0.5)
        assert result is True

        # Emphasize punctuation: 0.2 * 0.3 + 0.8 * 0.9 = 0.06 + 0.72 = 0.78 > 0.5
        result = threshold_based_definition(0.3, 0.9, emoji_weight=0.2, punct_weight=0.8, threshold=0.5)
        assert result is True

class TestIntegrationWithRealDataFormats:
    """Tests that verify the logic works with data formats expected from T013/T014."""

    def test_conjunctive_with_typical_high_intensity_message(self):
        """Test with a message that has both emojis and punctuation."""
        text = "That sounds amazing!!!"
        emoji_int = calculate_emoji_intensity(text)
        punct_int = calculate_punctuation_intensity(text)
        
        # Should be high on punctuation, low on emoji (no emojis in text)
        assert punct_int > 0.5
        assert emoji_int <= 0.5
        
        # Conjunctive should be False (only one is high)
        result = conjunctive_definition(emoji_int, punct_int)
        assert result is False

    def test_disjunctive_with_typical_high_intensity_message(self):
        """Test with a message that has both emojis and punctuation."""
        text = "That sounds amazing!!!"
        emoji_int = calculate_emoji_intensity(text)
        punct_int = calculate_punctuation_intensity(text)
        
        # Disjunctive should be True (at least one is high)
        result = disjunctive_definition(emoji_int, punct_int)
        assert result is True

    def test_threshold_with_balanced_message(self):
        """Test with a message that has balanced emoji and punctuation."""
        text = "Great! 😀"
        emoji_int = calculate_emoji_intensity(text)
        punct_int = calculate_punctuation_intensity(text)
        
        # Both should be moderate
        weighted_sum = (0.4 * emoji_int) + (0.6 * punct_int)
        
        # Check if it exceeds threshold
        result = threshold_based_definition(emoji_int, punct_int)
        
        # The result should match the weighted sum logic
        expected = weighted_sum > 0.5
        assert result == expected

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_text(self):
        """Empty text should result in zero intensity."""
        emoji_int = calculate_emoji_intensity("")
        punct_int = calculate_punctuation_intensity("")
        
        assert emoji_int == 0.0
        assert punct_int == 0.0
        
        # All definitions should return False
        assert conjunctive_definition(emoji_int, punct_int) is False
        assert disjunctive_definition(emoji_int, punct_int) is False
        assert threshold_based_definition(emoji_int, punct_int) is False

    def test_very_long_text(self):
        """Very long text should not cause errors."""
        long_text = "Wow! " * 100 + "😀" * 100
        emoji_int = calculate_emoji_intensity(long_text)
        punct_int = calculate_punctuation_intensity(long_text)
        
        # Both should be capped at 1.0
        assert emoji_int == 1.0
        assert punct_int == 1.0

    def test_threshold_zero(self):
        """Threshold of 0 should make everything True (except exactly 0)."""
        # With threshold=0, any positive intensity should return True
        result_conj = conjunctive_definition(0.1, 0.1, threshold=0.0)
        result_disj = disjunctive_definition(0.1, 0.1, threshold=0.0)
        result_thresh = threshold_based_definition(0.1, 0.1, threshold=0.0)
        
        assert result_conj is True
        assert result_disj is True
        assert result_thresh is True

    def test_threshold_one(self):
        """Threshold of 1 should make everything False (since max is 1.0)."""
        result_conj = conjunctive_definition(1.0, 1.0, threshold=1.0)
        result_disj = disjunctive_definition(1.0, 1.0, threshold=1.0)
        result_thresh = threshold_based_definition(1.0, 1.0, threshold=1.0)
        
        assert result_conj is False
        assert result_disj is False
        assert result_thresh is False