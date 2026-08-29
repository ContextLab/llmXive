"""
Unit tests for the core data structures (entities.py).

These tests validate the AbstractRecord, TopicVector, and DivergenceMeasurement classes
to ensure they meet the specifications for the topic drift analysis pipeline.
"""
import unittest
import numpy as np
import pytest
from src.models.entities import AbstractRecord, TopicVector, DivergenceMeasurement


class TestAbstractRecord(unittest.TestCase):
    """Tests for the AbstractRecord data structure."""

    def test_valid_record_creation(self):
        """Test creation of a valid AbstractRecord."""
        record = AbstractRecord(
            id='test_001',
            title='Test Title',
            abstract='This is a test abstract with some content.',
            year=2023,
            source='arxiv',
            tokens=['test', 'abstract', 'content'],
            window='2020-2024'
        )
        
        self.assertEqual(record.id, 'test_001')
        self.assertEqual(record.title, 'Test Title')
        self.assertEqual(record.year, 2023)
        self.assertEqual(record.source, 'arxiv')
        self.assertEqual(len(record.tokens), 3)
        self.assertEqual(record.window, '2020-2024')
        self.assertEqual(record.token_count, 3)

    def test_record_with_empty_categories(self):
        """Test that records can be created with empty categories."""
        record = AbstractRecord(
            id='test_002',
            title='Test',
            abstract='Test abstract',
            year=2020,
            source='pubmed'
        )
        
        self.assertEqual(record.categories, [])
        self.assertEqual(record.raw_metadata, {})

    def test_invalid_empty_id(self):
        """Test that empty ID raises ValueError."""
        with self.assertRaises(ValueError):
            AbstractRecord(
                id='',
                title='Test',
                abstract='Test abstract',
                year=2020,
                source='arxiv'
            )

    def test_invalid_year_range(self):
        """Test that year outside reasonable range raises ValueError."""
        with self.assertRaises(ValueError):
            AbstractRecord(
                id='test_003',
                title='Test',
                abstract='Test abstract',
                year=1800,  # Too old
                source='arxiv'
            )

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = AbstractRecord(
            id='test_004',
            title='Serialization Test',
            abstract='Testing serialization.',
            year=2022,
            source='arxiv',
            tokens=['test', 'serialization'],
            window='2020-2024',
            categories=['cs.LG', 'stat.ML'],
            raw_metadata={'extra': 'data'}
        )
        
        data = original.to_dict()
        restored = AbstractRecord.from_dict(data)
        
        self.assertEqual(restored.id, original.id)
        self.assertEqual(restored.title, original.title)
        self.assertEqual(restored.year, original.year)
        self.assertEqual(restored.source, original.source)
        self.assertEqual(restored.tokens, original.tokens)
        self.assertEqual(restored.window, original.window)
        self.assertEqual(restored.categories, original.categories)
        self.assertEqual(restored.raw_metadata, original.raw_metadata)

    def test_unknown_source_warning(self):
        """Test that unknown source triggers a warning (but still creates record)."""
        # This should not raise, but may log a warning
        record = AbstractRecord(
            id='test_005',
            title='Test',
            abstract='Test',
            year=2020,
            source='unknown_source'
        )
        self.assertEqual(record.source, 'unknown_source')


class TestTopicVector(unittest.TestCase):
    """Tests for the TopicVector data structure."""

    def test_valid_topic_vector_creation(self):
        """Test creation of a valid TopicVector."""
        probs = np.array([0.1, 0.2, 0.3, 0.4])
        vector = TopicVector(
            window='2000-2004',
            topic_probs=probs,
            topic_ids=['topic_0', 'topic_1', 'topic_2', 'topic_3']
        )
        
        self.assertEqual(vector.window, '2000-2004')
        self.assertEqual(vector.n_topics, 4)
        self.assertTrue(vector.is_valid)
        self.assertAlmostEqual(np.sum(vector.topic_probs), 1.0)

    def test_normalization_on_creation(self):
        """Test that topic probabilities are normalized to sum to 1."""
        probs = np.array([1.0, 2.0, 3.0])  # Sum = 6.0
        vector = TopicVector(
            window='2005-2009',
            topic_probs=probs
        )
        
        self.assertAlmostEqual(np.sum(vector.topic_probs), 1.0)
        self.assertAlmostEqual(vector.topic_probs[0], 1.0/6.0)
        self.assertAlmostEqual(vector.topic_probs[1], 2.0/6.0)
        self.assertAlmostEqual(vector.topic_probs[2], 3.0/6.0)

    def test_nan_values_rejected(self):
        """Test that topic vectors with NaN values raise ValueError."""
        with self.assertRaises(ValueError):
            TopicVector(
                window='2010-2014',
                topic_probs=np.array([0.5, np.nan, 0.5])
            )

    def test_zero_sum_handling(self):
        """Test handling of zero-sum vectors (should become uniform)."""
        vector = TopicVector(
            window='2015-2019',
            topic_probs=np.array([0.0, 0.0, 0.0])
        )
        
        # Should be normalized to uniform distribution
        self.assertAlmostEqual(vector.topic_probs[0], 1.0/3.0)
        self.assertAlmostEqual(vector.topic_probs[1], 1.0/3.0)
        self.assertAlmostEqual(vector.topic_probs[2], 1.0/3.0)

    def test_get_top_k_topics(self):
        """Test retrieval of top k topics."""
        probs = np.array([0.05, 0.45, 0.10, 0.40])
        vector = TopicVector(
            window='2020-2024',
            topic_probs=probs
        )
        
        top_2 = vector.get_top_k_topics(2)
        self.assertEqual(len(top_2), 2)
        self.assertEqual(top_2[0][0], 1)  # Index of highest prob
        self.assertEqual(top_2[0][1], 0.45)
        self.assertEqual(top_2[1][0], 3)  # Index of second highest
        self.assertEqual(top_2[1][1], 0.40)

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = TopicVector(
            window='2000-2004',
            topic_probs=np.array([0.25, 0.25, 0.25, 0.25]),
            topic_ids=['A', 'B', 'C', 'D'],
            model_params={'k': 4, 'max_iter': 10}
        )
        
        data = original.to_dict()
        restored = TopicVector.from_dict(data)
        
        self.assertEqual(restored.window, original.window)
        np.testing.assert_array_almost_equal(restored.topic_probs, original.topic_probs)
        self.assertEqual(restored.topic_ids, original.topic_ids)
        self.assertEqual(restored.model_params, original.model_params)

    def test_invalid_dimensions(self):
        """Test that 2D arrays are rejected."""
        with self.assertRaises(ValueError):
            TopicVector(
                window='test',
                topic_probs=np.array([[0.5, 0.5], [0.5, 0.5]])
            )


class TestDivergenceMeasurement(unittest.TestCase):
    """Tests for the DivergenceMeasurement data structure."""

    def test_valid_measurement_creation(self):
        """Test creation of a valid DivergenceMeasurement."""
        measurement = DivergenceMeasurement(
            window_pair=('2000-2004', '2005-2009'),
            divergence_value=0.15,
            p_value=0.03,
            confidence_interval=(0.10, 0.20),
            is_significant=True,
            permutation_count=1000,
            correction_method='maxT'
        )
        
        self.assertEqual(measurement.window_pair, ('2000-2004', '2005-2009'))
        self.assertEqual(measurement.divergence_value, 0.15)
        self.assertEqual(measurement.p_value, 0.03)
        self.assertTrue(measurement.is_significant)
        self.assertTrue(measurement.is_valid)

    def test_same_window_rejected(self):
        """Test that comparing a window to itself raises ValueError."""
        with self.assertRaises(ValueError):
            DivergenceMeasurement(
                window_pair=('2000-2004', '2000-2004'),
                divergence_value=0.0
            )

    def test_negative_divergence_clamped(self):
        """Test that negative divergence values are clamped to 0."""
        measurement = DivergenceMeasurement(
            window_pair=('2000-2004', '2005-2009'),
            divergence_value=-0.1
        )
        
        self.assertEqual(measurement.divergence_value, 0.0)

    def test_invalid_p_value_range(self):
        """Test that p-values outside [0, 1] are handled (no exception, but may warn)."""
        # The class doesn't explicitly reject invalid p-values, just validates on is_valid
        measurement = DivergenceMeasurement(
            window_pair=('2000-2004', '2005-2009'),
            divergence_value=0.1,
            p_value=1.5  # Invalid
        )
        
        self.assertFalse(measurement.is_valid)

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = DivergenceMeasurement(
            window_pair=('2000-2004', '2005-2009'),
            divergence_value=0.25,
            p_value=0.01,
            confidence_interval=(0.18, 0.32),
            is_significant=True,
            permutation_count=1000,
            correction_method='maxT',
            raw_stats={'null_mean': 0.05, 'observed_rank': 1}
        )
        
        data = original.to_dict()
        restored = DivergenceMeasurement.from_dict(data)
        
        self.assertEqual(restored.window_pair, original.window_pair)
        self.assertAlmostEqual(restored.divergence_value, original.divergence_value)
        self.assertEqual(restored.p_value, original.p_value)
        self.assertEqual(restored.confidence_interval, original.confidence_interval)
        self.assertEqual(restored.is_significant, original.is_significant)
        self.assertEqual(restored.permutation_count, original.permutation_count)
        self.assertEqual(restored.correction_method, original.correction_method)
        self.assertEqual(restored.raw_stats, original.raw_stats)

    def test_window_pair_as_list_in_dict(self):
        """Test that window_pair can be serialized as list and restored as tuple."""
        measurement = DivergenceMeasurement(
            window_pair=('2000-2004', '2005-2009'),
            divergence_value=0.1
        )
        
        data = measurement.to_dict()
        self.assertIsInstance(data['window_pair'], list)
        
        restored = DivergenceMeasurement.from_dict(data)
        self.assertIsInstance(restored.window_pair, tuple)
        self.assertEqual(restored.window_pair, ('2000-2004', '2005-2009'))


if __name__ == '__main__':
    unittest.main()