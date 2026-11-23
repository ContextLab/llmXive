import unittest
import numpy as np
import pytest
from src.models.entities import AbstractRecord, TopicVector, DivergenceMeasurement

class TestAbstractRecord(unittest.TestCase):
    def test_valid_record_creation(self):
        """Test creation of a valid AbstractRecord."""
        record = AbstractRecord(
            id="test_001",
            title="Test Paper",
            text="This is a test abstract.",
            year=2020,
            source="arxiv",
            window="2020-2024"
        )
        self.assertTrue(record.validate())
        self.assertEqual(record.id, "test_001")
        self.assertEqual(record.source, "arxiv")

    def test_invalid_year(self):
        """Test validation fails for invalid year."""
        record = AbstractRecord(
            id="test_002",
            title="Test Paper",
            text="This is a test abstract.",
            year=1800,
            source="arxiv",
            window="2020-2024"
        )
        self.assertFalse(record.validate())

    def test_invalid_source(self):
        """Test validation fails for invalid source."""
        record = AbstractRecord(
            id="test_003",
            title="Test Paper",
            text="This is a test abstract.",
            year=2020,
            source="invalid_source",
            window="2020-2024"
        )
        self.assertFalse(record.validate())

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = AbstractRecord(
            id="test_004",
            title="Test Paper",
            text="This is a test abstract.",
            year=2020,
            source="pubmed",
            window="2015-2019",
            tokens=["test", "abstract"]
        )
        data = original.to_dict()
        restored = AbstractRecord.from_dict(data)
        
        self.assertEqual(restored.id, original.id)
        self.assertEqual(restored.tokens, original.tokens)
        self.assertEqual(restored.source, original.source)

class TestTopicVector(unittest.TestCase):
    def test_valid_topic_vector(self):
        """Test creation of a valid TopicVector."""
        proportions = np.array([0.1, 0.2, 0.3, 0.4])
        vector = TopicVector(
            window="2020-2024",
            topic_proportions=proportions,
            topic_words=[["word1", "word2"], ["word3", "word4"], ["word5", "word6"], ["word7", "word8"]],
            k_topics=4
        )
        self.assertTrue(vector.validate())
        self.assertTrue(np.isclose(np.sum(vector.topic_proportions), 1.0))

    def test_auto_normalization(self):
        """Test that proportions are auto-normalized."""
        proportions = np.array([1.0, 2.0, 3.0])  # Sum = 6
        vector = TopicVector(
            window="2015-2019",
            topic_proportions=proportions,
            topic_words=[["a"], ["b"], ["c"]],
            k_topics=3
        )
        self.assertTrue(np.isclose(np.sum(vector.topic_proportions), 1.0))
        self.assertTrue(np.isclose(vector.topic_proportions[0], 1/6))

    def test_invalid_k_topics(self):
        """Test validation fails for invalid k_topics."""
        with self.assertRaises(ValueError):
            TopicVector(
                window="2015-2019",
                topic_proportions=np.array([0.5, 0.5]),
                topic_words=[["a"], ["b"]],
                k_topics=0
            )

    def test_mismatched_dimensions(self):
        """Test validation fails for mismatched dimensions."""
        with self.assertRaises(ValueError):
            TopicVector(
                window="2015-2019",
                topic_proportions=np.array([0.5, 0.5, 0.5]),
                topic_words=[["a"], ["b"]],
                k_topics=2
            )

class TestDivergenceMeasurement(unittest.TestCase):
    def test_valid_measurement(self):
        """Test creation of a valid DivergenceMeasurement."""
        measurement = DivergenceMeasurement(
            window_pair=("2015-2019", "2020-2024"),
            divergence_value=0.15,
            p_value=0.03,
            is_significant=True
        )
        self.assertTrue(measurement.validate())
        self.assertTrue(measurement.is_significant)

    def test_window_pair_ordering(self):
        """Test that window pairs are automatically sorted."""
        measurement = DivergenceMeasurement(
            window_pair=("2020-2024", "2015-2019"),
            divergence_value=0.15
        )
        self.assertEqual(measurement.window_pair, ("2015-2019", "2020-2024"))

    def test_invalid_divergence_range(self):
        """Test warning for divergence outside [0, 1]."""
        measurement = DivergenceMeasurement(
            window_pair=("2015-2019", "2020-2024"),
            divergence_value=1.5
        )
        # Should still be created but with a warning logged
        self.assertTrue(measurement.validate())

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = DivergenceMeasurement(
            window_pair=("2015-2019", "2020-2024"),
            divergence_value=0.15,
            p_value=0.03,
            is_significant=True,
            confidence_interval=(0.10, 0.20)
        )
        data = original.to_dict()
        restored = DivergenceMeasurement.from_dict(data)
        
        self.assertEqual(restored.window_pair, original.window_pair)
        self.assertEqual(restored.divergence_value, original.divergence_value)
        self.assertEqual(restored.confidence_interval, original.confidence_interval)

if __name__ == "__main__":
    unittest.main()