"""
Unit tests for metrics.py - Contributor Pair identification and metric calculation.
"""
import unittest
from datetime import datetime, timedelta
from models import Event, ContributorPair
from metrics import identify_pairs_and_calculate_metrics, calculate_project_level_metrics, _is_bot, _parse_timestamp


class TestIsBot(unittest.TestCase):
    def test_bot_name(self):
        self.assertTrue(_is_bot("user[bot]"))
        self.assertTrue(_is_bot("dependabot[bot]"))

    def test_github_app(self):
        self.assertTrue(_is_bot("GitHub App"))
        self.assertTrue(_is_bot("renovate-app"))

    def test_normal_user(self):
        self.assertFalse(_is_bot("alice"))
        self.assertFalse(_is_bot("Bob"))

    def test_empty(self):
        self.assertTrue(_is_bot(""))
        self.assertTrue(_is_bot(None))


class TestParseTimestamp(unittest.TestCase):
    def test_valid_iso(self):
        ts = "2023-10-01T12:00:00"
        result = _parse_timestamp(ts)
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2023)

    def test_valid_iso_z(self):
        ts = "2023-10-01T12:00:00Z"
        result = _parse_timestamp(ts)
        self.assertIsNotNone(result)

    def test_invalid(self):
        self.assertIsNone(_parse_timestamp("invalid"))
        self.assertIsNone(_parse_timestamp(""))


class TestIdentifyPairsAndCalculateMetrics(unittest.TestCase):
    def test_simple_pair(self):
        """Test basic pair identification: A posts, B replies."""
        base_time = datetime(2023, 1, 1, 12, 0, 0)
        events = [
            Event(
                project_id="proj-1",
                thread_id="thread-1",
                author="Alice",
                timestamp=base_time,
                event_type="comment"
            ),
            Event(
                project_id="proj-1",
                thread_id="thread-1",
                author="Bob",
                timestamp=base_time + timedelta(seconds=100),
                event_type="comment"
            )
        ]

        pairs = identify_pairs_and_calculate_metrics(events)
        self.assertEqual(len(pairs), 1)
        pair = pairs[0]
        self.assertEqual(pair.author_a, "Alice")
        self.assertEqual(pair.author_b, "Bob")
        self.assertAlmostEqual(pair.mean_delay, 100.0, places=1)
        self.assertEqual(pair.event_count, 1)

    def test_self_reply_excluded(self):
        """Test that self-replies are excluded."""
        base_time = datetime(2023, 1, 1, 12, 0, 0)
        events = [
            Event(
                project_id="proj-1",
                thread_id="thread-1",
                author="Alice",
                timestamp=base_time,
                event_type="comment"
            ),
            Event(
                project_id="proj-1",
                thread_id="thread-1",
                author="Alice",
                timestamp=base_time + timedelta(seconds=100),
                event_type="comment"
            )
        ]

        pairs = identify_pairs_and_calculate_metrics(events)
        self.assertEqual(len(pairs), 0)

    def test_bot_excluded(self):
        """Test that bot events are excluded."""
        base_time = datetime(2023, 1, 1, 12, 0, 0)
        events = [
            Event(
                project_id="proj-1",
                thread_id="thread-1",
                author="Alice",
                timestamp=base_time,
                event_type="comment"
            ),
            Event(
                project_id="proj-1",
                thread_id="thread-1",
                author="bot-user[bot]",
                timestamp=base_time + timedelta(seconds=100),
                event_type="comment"
            )
        ]

        pairs = identify_pairs_and_calculate_metrics(events)
        self.assertEqual(len(pairs), 0)

    def test_multiple_interactions(self):
        """Test multiple exchanges between two users."""
        base_time = datetime(2023, 1, 1, 12, 0, 0)
        events = [
            Event(project_id="p1", thread_id="t1", author="A", timestamp=base_time, event_type="comment"),
            Event(project_id="p1", thread_id="t1", author="B", timestamp=base_time + timedelta(seconds=10), event_type="comment"),
            Event(project_id="p1", thread_id="t1", author="A", timestamp=base_time + timedelta(seconds=20), event_type="comment"),
            Event(project_id="p1", thread_id="t1", author="B", timestamp=base_time + timedelta(seconds=35), event_type="comment"),
        ]
        # A->B (10s), B->A (10s), A->B (15s)
        # Pairs: (A, B) with deltas [10, 15], (B, A) with deltas [10]

        pairs = identify_pairs_and_calculate_metrics(events)
        self.assertEqual(len(pairs), 2)

        # Find (A, B)
        pair_ab = next((p for p in pairs if p.author_a == "A" and p.author_b == "B"), None)
        self.assertIsNotNone(pair_ab)
        self.assertAlmostEqual(pair_ab.mean_delay, 12.5, places=1) # (10+15)/2
        self.assertEqual(pair_ab.event_count, 2)

        # Find (B, A)
        pair_ba = next((p for p in pairs if p.author_a == "B" and p.author_b == "A"), None)
        self.assertIsNotNone(pair_ba)
        self.assertAlmostEqual(pair_ba.mean_delay, 10.0, places=1)
        self.assertEqual(pair_ba.event_count, 1)

    def test_empty_events(self):
        pairs = identify_pairs_and_calculate_metrics([])
        self.assertEqual(len(pairs), 0)


class TestCalculateProjectLevelMetrics(unittest.TestCase):
    def test_empty_pairs(self):
        metrics = calculate_project_level_metrics([])
        self.assertEqual(metrics['project_mean_delay'], 0.0)
        self.assertEqual(metrics['total_pairs'], 0)

    def test_single_pair(self):
        pairs = [
            ContributorPair(author_a="A", author_b="B", response_time_variance=10.0, mean_delay=100.0, event_count=10)
        ]
        metrics = calculate_project_level_metrics(pairs)
        self.assertAlmostEqual(metrics['project_mean_delay'], 100.0, places=1)
        self.assertEqual(metrics['total_pairs'], 1)
        self.assertEqual(metrics['total_events'], 10)

    def test_weighted_mean(self):
        # Pair 1: mean=100, count=2
        # Pair 2: mean=200, count=2
        # Weighted mean should be 150
        pairs = [
            ContributorPair(author_a="A", author_b="B", response_time_variance=0.0, mean_delay=100.0, event_count=2),
            ContributorPair(author_a="C", author_b="D", response_time_variance=0.0, mean_delay=200.0, event_count=2),
        ]
        metrics = calculate_project_level_metrics(pairs)
        self.assertAlmostEqual(metrics['project_mean_delay'], 150.0, places=1)

    def test_weighted_mean_unbalanced(self):
        # Pair 1: mean=100, count=1
        # Pair 2: mean=200, count=9
        # Weighted mean = (100*1 + 200*9) / 10 = 190
        pairs = [
            ContributorPair(author_a="A", author_b="B", response_time_variance=0.0, mean_delay=100.0, event_count=1),
            ContributorPair(author_a="C", author_b="D", response_time_variance=0.0, mean_delay=200.0, event_count=9),
        ]
        metrics = calculate_project_level_metrics(pairs)
        self.assertAlmostEqual(metrics['project_mean_delay'], 190.0, places=1)


if __name__ == '__main__':
    unittest.main()
