"""
Unit tests for feature extraction logic.
"""
import unittest
from features import extract_features

class TestFeatureExtraction(unittest.TestCase):

    def test_modal_verb_extraction(self):
        text = "You should take this medication. It may help."
        feats = extract_features(text)
        # "should" and "may" are modal verbs
        self.assertGreater(feats['modal_verb_freq'], 0)
        self.assertEqual(feats['total_sentences'], 2)

    def test_citation_density(self):
        text = "Studies [1] show this works. (2) is also true."
        feats = extract_features(text)
        # Two citations: [1] and (2)
        self.assertGreater(feats['citation_density'], 0)

    def test_imperative_ratio(self):
        text = "Take this pill. You should rest."
        feats = extract_features(text)
        # "Take" is imperative
        self.assertGreater(feats['imperative_ratio'], 0)

    def test_empty_text(self):
        feats = extract_features("")
        self.assertEqual(feats['total_sentences'], 0)
        self.assertEqual(feats['modal_verb_freq'], 0)
        self.assertEqual(feats['imperative_ratio'], 0)

    def test_undefined_imperative_ratio(self):
        # Text with 0 sentences should return 0.0 for ratio, not error
        feats = extract_features("")
        self.assertEqual(feats['imperative_ratio'], 0.0)

if __name__ == '__main__':
    unittest.main()
