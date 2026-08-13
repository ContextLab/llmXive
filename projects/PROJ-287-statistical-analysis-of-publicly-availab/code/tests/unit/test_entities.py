"""
Unit tests for the core data structures in src/models/entities.py.
"""
import unittest
import numpy as np
import pytest
from src.models.entities import AbstractRecord, TopicVector, DivergenceMeasurement


class TestAbstractRecord(unittest.TestCase):
    """Tests for the AbstractRecord dataclass."""

    def test_valid_record_creation(self):
        """Test creation of a valid AbstractRecord."""
        record = AbstractRecord(
            id="1234",
            source="arxiv",
            title="Test Title",
            abstract="This is a test abstract.",
            year=2020,
            window="2020-2024",
            tokens=["test", "abstract"]
        )
        self.assertEqual(record.id, "1234")
        self.assertEqual(record.source, "arxiv")
        self.assertEqual(record.window, "2020-2024")
        self.assertEqual(len(record.tokens), 2)

    def test_invalid_source(self):
        """Test that invalid source raises ValueError."""
        with self.assertRaises(ValueError):
            AbstractRecord(
                id="1234",
                source="invalid_source",
                title="Test",
                abstract="Text",
                year=2020,
                window="2020-2024"
            )

    def test_invalid_year(self):
        """Test that year outside range raises ValueError."""
        with self.assertRaises(ValueError):
            AbstractRecord(
                id="1234",
                source="arxiv",
                title="Test",
                abstract="Text",
                year=1999,
                window="2020-2024"
            )

    def test_empty_id(self):
        """Test that empty ID raises ValueError."""
        with self.assertRaises(ValueError):
            AbstractRecord(
                id="",
                source="arxiv",
                title="Test",
                abstract="Text",
                year=2020,
                window="2020-2024"
            )


class TestTopicVector(unittest.TestCase):
    """Tests for the TopicVector dataclass."""

    def test_valid_vector_creation(self):
        """Test creation of a valid TopicVector."""
        probs = np.array([0.5, 0.5])
        vector = TopicVector(
            window="2000-2004",
            topic_ids=[0, 1],
            probabilities=probs,
            model_params={"k": 2, "seed": 42}
        )
        self.assertEqual(vector.window, "2000-2004")
        self.assertTrue(np.isclose(np.sum(vector.probabilities), 1.0))

    def test_mismatched_lengths(self):
        """Test that mismatched lengths raise ValueError."""
        with self.assertRaises(ValueError):
            TopicVector(
                window="2000-2004",
                topic_ids=[0, 1],
                probabilities=np.array([0.5])
            )

    def test_negative_probability(self):
        """Test that negative probabilities raise ValueError."""
        with self.assertRaises(ValueError):
            TopicVector(
                window="2000-2004",
                topic_ids=[0, 1],
                probabilities=np.array([-0.1, 1.1])
            )

    def test_sum_not_one(self):
        """Test that probabilities not summing to 1.0 raise ValueError."""
        with self.assertRaises(ValueError):
            TopicVector(
                window="2000-2004",
                topic_ids=[0, 1],
                probabilities=np.array([0.4, 0.4])
            )

    def test_nan_probability(self):
        """Test that NaN probabilities raise ValueError."""
        with self.assertRaises(ValueError):
            TopicVector(
                window="2000-2004",
                topic_ids=[0, 1],
                probabilities=np.array([np.nan, 1.0])
            )

    def test_get_topic_probability(self):
        """Test retrieving a specific topic probability."""
        probs = np.array([0.3, 0.7])
        vector = TopicVector(
            window="2000-2004",
            topic_ids=[0, 1],
            probabilities=probs
        )
        self.assertEqual(vector.get_topic_probability(0), 0.3)
        self.assertEqual(vector.get_topic_probability(1), 0.7)

    def test_get_invalid_topic(self):
        """Test retrieving a non-existent topic raises KeyError."""
        probs = np.array([0.3, 0.7])
        vector = TopicVector(
            window="2000-2004",
            topic_ids=[0, 1],
            probabilities=probs
        )
        with self.assertRaises(KeyError):
            vector.get_topic_probability(2)

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = TopicVector(
            window="2000-2004",
            topic_ids=[0, 1],
            probabilities=np.array([0.2, 0.8]),
            model_params={"k": 10}
        )
        data = original.to_dict()
        restored = TopicVector.from_dict(data)
        
        self.assertEqual(restored.window, original.window)
        self.assertEqual(restored.topic_ids, original.topic_ids)
        self.assertTrue(np.allclose(restored.probabilities, original.probabilities))
        self.assertEqual(restored.model_params, original.model_params)


class TestDivergenceMeasurement(unittest.TestCase):
    """Tests for the DivergenceMeasurement dataclass."""

    def test_valid_measurement(self):
        """Test creation of a valid DivergenceMeasurement."""
        measurement = DivergenceMeasurement(
            window_1="2000-2004",
            window_2="2005-2009",
            divergence_value=0.15,
            divergence_type="JS_Divergence",
            is_significant=True,
            p_value=0.03
        )
        self.assertEqual(measurement.window_1, "2000-2004")
        self.assertEqual(measurement.divergence_value, 0.15)

    def test_same_window(self):
        """Test that same windows raise ValueError."""
        with self.assertRaises(ValueError):
            DivergenceMeasurement(
                window_1="2000-2004",
                window_2="2000-2004",
                divergence_value=0.0,
                divergence_type="JS_Divergence"
            )

    def test_negative_divergence(self):
        """Test that negative divergence raises ValueError."""
        with self.assertRaises(ValueError):
            DivergenceMeasurement(
                window_1="2000-2004",
                window_2="2005-2009",
                divergence_value=-0.1,
                divergence_type="JS_Divergence"
            )

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = DivergenceMeasurement(
            window_1="2000-2004",
            window_2="2005-2009",
            divergence_value=0.15,
            divergence_type="JS_Divergence",
            confidence_interval=(0.10, 0.20)
        )
        data = original.to_dict()
        restored = DivergenceMeasurement.from_dict(data)

        self.assertEqual(restored.window_1, original.window_1)
        self.assertEqual(restored.divergence_value, original.divergence_value)
        self.assertEqual(restored.confidence_interval, original.confidence_interval)