import unittest
import numpy as np
from matching import build_tfidf_vectors, find_top_matches, apply_sensitivity_analysis

class TestMatching(unittest.TestCase):

    def test_build_tfidf_vectors_excludes_pronouns(self):
        """
        Unit test for TF-IDF vector construction excluding pronouns (FR-008).
        """
        stories = [
            {'id': 1, 'text': 'I went to the store. I bought an apple.'},
            {'id': 2, 'text': 'He went to the store. He bought an apple.'}
        ]
        
        vectorizer, vectors = build_tfidf_vectors(stories, exclude_pronouns=True)
        
        # Check that vectors are not empty
        self.assertEqual(vectors.shape[0], 2)
        self.assertEqual(vectors.shape[1], 2) # 'store', 'apple' should be the main features
        
        # Verify that pronouns 'I' and 'He' are NOT in the feature names
        feature_names = vectorizer.get_feature_names_out()
        self.assertNotIn('i', feature_names)
        self.assertNotIn('he', feature_names)
        self.assertIn('apple', feature_names)
        self.assertIn('store', feature_names)

    def test_find_top_matches_tie_breaking(self):
        """
        Unit test for cosine similarity calculation and tie-breaking logic.
        """
        # Create a query vector and candidate vectors
        query = np.array([[1.0, 0.0, 0.0]])
        candidates = np.array([
            [0.8, 0.0, 0.0], # Score 0.8
            [0.8, 0.0, 0.0], # Score 0.8 (Tie)
            [0.5, 0.0, 0.0]  # Score 0.5
        ])
        
        matches = find_top_matches(query, candidates, k=2)
        
        # We expect 2 matches. Tie-breaking should pick the first two with 0.8
        # The order in argsort is stable for ties, so indices 0 and 1 should be picked
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0]['similarity'], 0.8)
        self.assertEqual(matches[1]['similarity'], 0.8)

    def test_apply_sensitivity_analysis(self):
        """
        Unit test for sensitivity analysis logic.
        """
        thresholds = [0.2, 0.5, 0.8]
        results = [
            {'similarity': 0.9},
            {'similarity': 0.6},
            {'similarity': 0.3},
            {'similarity': 0.1}
        ]
        
        analysis = apply_sensitivity_analysis(thresholds, results)
        
        self.assertEqual(len(analysis['threshold_results']), 3)
        
        # Check counts for threshold 0.2
        res_02 = analysis['threshold_results'][0]
        self.assertEqual(res_02['threshold'], 0.2)
        self.assertEqual(res_02['matched_count'], 3) # 0.9, 0.6, 0.3 > 0.2
        
        # Check counts for threshold 0.8
        res_08 = analysis['threshold_results'][2]
        self.assertEqual(res_08['threshold'], 0.8)
        self.assertEqual(res_08['matched_count'], 1) # Only 0.9 > 0.8

if __name__ == '__main__':
    unittest.main()