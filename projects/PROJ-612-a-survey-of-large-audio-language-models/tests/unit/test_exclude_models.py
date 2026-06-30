"""
Unit tests for the model‑exclusion utilities defined in
`code/exclude_models.py`.
"""

import unittest

from exclude_models import (
    normalize_string,
    check_model_exclusion,
    filter_models,
)


class TestExcludeModels(unittest.TestCase):
    """Validate the behaviour of model‑exclusion helpers."""

    def test_normalize_string(self):
        """Normalization should be identical to the one used in other modules."""
        self.assertEqual(normalize_string("  MyModel_v1  "), "mymodel_v1")

    def test_check_model_exclusion_true(self):
        """A model whose name contains an exclusion keyword should be flagged."""
        model_name = "librispeech_asr_large"
        keywords = ["librispeech", "musicbench"]
        self.assertTrue(check_model_exclusion(model_name, keywords))

    def test_check_model_exclusion_false(self):
        """A model without any keyword match should not be excluded."""
        model_name = "speechbrain_generic"
        keywords = ["librispeech", "musicbench"]
        self.assertFalse(check_model_exclusion(model_name, keywords))

    def test_filter_models(self):
        """filter_models should return only the non‑excluded models."""
        models = [
            {"model_name": "librispeech_asr"},
            {"model_name": "musicbench_v2"},
            {"model_name": "generic_speech"},
        ]
        keywords = ["librispeech", "musicbench"]
        filtered = filter_models(models, keywords)
        # Only the generic model should survive the filter.
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["model_name"], "generic_speech")


if __name__ == "__main__":
    unittest.main()
