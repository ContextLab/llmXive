"""
Unit tests for the hallucination detection utilities defined in
`code/detect_hallucination.py`.
The tests focus on the core string‑normalisation, synonym expansion and
matching logic that underpins the rule‑based detector.
"""

import unittest
import nltk

# Ensure the WordNet corpus is available for the synonym tests.
# This is a no‑op if the data is already present.
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)

from detect_hallucination import (
    normalize_string,
    get_synonyms,
    is_fuzzy_match,
    expand_ground_truth_entities,
    check_caption_entity_against_gt,
)


class TestDetectHallucinationUtils(unittest.TestCase):
    """Test the low‑level utility functions used by the hallucination detector."""

    def test_normalize_string(self):
        """Normalization should lower‑case and strip surrounding whitespace."""
        self.assertEqual(normalize_string("  HeLLo WoRLD  "), "hello world")
        self.assertEqual(normalize_string("\n\tTestString\n"), "teststring")

    def test_is_fuzzy_match_identical(self):
        """Identical strings must be considered a fuzzy match."""
        self.assertTrue(is_fuzzy_match("audio", "audio"))

    def test_is_fuzzy_match_similar(self):
        """Strings that are highly similar (>=80 % similarity) should match."""
        # The exact threshold is defined inside the implementation; we use a
        # pair that is known to have a very high fuzzy score.
        self.assertTrue(is_fuzzy_match("speech", "spech"))

    def test_get_synonyms_basic(self):
        """WordNet synonyms for a common word should contain at least one
        known synonym."""
        synonyms = get_synonyms("car")
        # 'automobile' is a canonical synonym for 'car' in WordNet.
        self.assertIn("automobile", synonyms)
        # The original word should also be present.
        self.assertIn("car", synonyms)

    def test_expand_ground_truth_entities(self):
        """The expansion should contain the original entities and their synonyms."""
        gt_entities = ["car", "dog"]
        expanded = expand_ground_truth_entities(gt_entities)
        # Original items must be present.
        self.assertIn("car", expanded)
        self.assertIn("dog", expanded)
        # Known synonyms should be added.
        self.assertIn("automobile", expanded)  # synonym of car
        self.assertIn("canine", expanded)      # synonym of dog (WordNet includes)

    def test_check_caption_entity_against_gt_positive(self):
        """A caption entity that matches a ground‑truth synonym should be accepted."""
        gt_set = expand_ground_truth_entities(["car"])
        # 'automobile' is a synonym of 'car' and should therefore be accepted.
        self.assertTrue(check_caption_entity_against_gt("automobile", gt_set))

    def test_check_caption_entity_against_gt_negative(self):
        """A caption entity that does not match any ground‑truth (or synonym) should be rejected."""
        gt_set = expand_ground_truth_entities(["car"])
        self.assertFalse(check_caption_entity_against_gt("bicycle", gt_set))


if __name__ == "__main__":
    unittest.main()
