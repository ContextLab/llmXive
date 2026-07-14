"""
metrics.py - Contributor Pair identification and metric calculation.

Identifies pairs of distinct authors who have exchanged at least one message
(excluding self-replies and bot events) and calculates inter-arrival times,
response_time_variance, and mean_delay.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import statistics

from models import Event, ContributorPair, EventType, Project
from utils.logger import get_logger

logger = get_logger(__name__)


def _is_bot(author: str) -> bool:
    """Check if the author is a bot or GitHub App."""
    if not author:
        return True
    author_lower = author.lower()
    if author_lower.endswith('[bot]'):
        return True
    # Common GitHub App patterns
    if 'app' in author_lower or 'dependabot' in author_lower or 'renovate' in author_lower:
        return True
    return False


def _parse_timestamp(ts: str) -> Optional[datetime]:
    """Parse ISO format timestamp string to datetime object."""
    if not ts:
        return None
    try:
        # Handle standard ISO format
        if 'T' in ts:
            return datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return None
    except (ValueError, AttributeError):
        logger.warning(f"Failed to parse timestamp: {ts}")
        return None


def identify_pairs_and_calculate_metrics(events: List[Event]) -> List[ContributorPair]:
    """
    Identify contributor pairs and calculate response time metrics.

    A pair is defined as any two distinct authors (A, B) who have exchanged
    at least one message (A replies to B or B replies to A) within the same
    thread/issue/PR. Self-replies are excluded. Bot events are excluded.

    Args:
        events: List of Event objects containing author, timestamp, thread_id, etc.

    Returns:
        List of ContributorPair objects with calculated metrics.
    """
    logger.info(f"Starting pair identification for {len(events)} events")

    # Filter out bot events and events with missing data
    valid_events = [
        e for e in events
        if e.author and not _is_bot(e.author) and e.timestamp and e.thread_id
    ]
    logger.info(f"Filtered to {len(valid_events)} valid non-bot events")

    if not valid_events:
        logger.warning("No valid events found for pair identification")
        return []

    # Sort events by timestamp to ensure chronological order
    valid_events.sort(key=lambda x: x.timestamp)

    # Group events by thread (issue/PR)
    threads: Dict[str, List[Event]] = defaultdict(list)
    for event in valid_events:
        threads[event.thread_id].append(event)

    # Dictionary to store interactions: (author_a, author_b) -> list of (timestamp_a, timestamp_b)
    # where author_a replied to author_b
    pair_interactions: Dict[Tuple[str, str], List[datetime]] = defaultdict(list)

    for thread_id, thread_events in threads.items():
        # For each event, look at previous events in the same thread to find who it might be replying to
        # We assume a simple model: if A posts, then B posts, B is replying to A (or someone before A)
        # To be more precise, we track the "last author" in the thread
        last_author = None
        last_timestamp = None

        for event in thread_events:
            current_author = event.author
            current_timestamp = event.timestamp

            # If there's a previous author and it's not a self-reply
            if last_author and last_author != current_author:
                # Record interaction: current_author is responding to last_author
                # We store the time delta between the two events
                pair_interactions[(last_author, current_author)].append(current_timestamp)

            last_author = current_author
            last_timestamp = current_timestamp

    # Calculate metrics for each pair
    pairs: List[ContributorPair] = []

    for (author_a, author_b), timestamps in pair_interactions.items():
        if not timestamps:
            continue

        # Calculate inter-arrival times (deltas)
        # timestamps list contains the response times (when B replied to A)
        # We need to calculate the delta between the original post and the reply
        # However, our current logic only stores the reply timestamp.
        # To calculate proper response time, we need to reconstruct the sequence.

        # Re-approach: For each pair (A, B), we need a list of (A_post_time, B_reply_time)
        # Let's rebuild the interaction list properly by iterating threads again
        pass

    # Re-implementation of pair interactions with proper timestamps
    pair_deltas: Dict[Tuple[str, str], List[float]] = defaultdict(list)

    for thread_id, thread_events in threads.items():
        # Track the last post time and author for each user in this thread?
        # Simpler: Maintain a list of recent posts by non-self authors
        # For each new post, calculate delta to the most recent post by a different author

        # Sort thread events by time (already sorted globally, but let's be safe)
        thread_events.sort(key=lambda x: x.timestamp)

        # We need to find: for every post by B, what was the time since the last post by A (where A != B)
        # This is a bit complex. Let's simplify:
        # For each event by B, find the immediately preceding event by A (A != B) in this thread.
        # The delta is the response time.

        for i, event in enumerate(thread_events):
            current_author = event.author
            current_time = event.timestamp

            # Look backwards for the last event by a different author
            for j in range(i - 1, -1, -1):
                prev_event = thread_events[j]
                if prev_event.author != current_author:
                    # Found the last post by a different author
                    delta_seconds = (current_time - prev_event.timestamp).total_seconds()
                    pair_key = (prev_event.author, current_author)
                    pair_deltas[pair_key].append(delta_seconds)
                    break

    # Now calculate metrics for each pair
    for (author_a, author_b), deltas in pair_deltas.items():
        if not deltas:
            continue

        # Filter out negative or zero deltas (shouldn't happen, but safety)
        valid_deltas = [d for d in deltas if d > 0]
        if not valid_deltas:
            continue

        mean_delay = statistics.mean(valid_deltas)
        variance = statistics.variance(valid_deltas) if len(valid_deltas) > 1 else 0.0

        pair = ContributorPair(
            author_a=author_a,
            author_b=author_b,
            response_time_variance=variance,
            mean_delay=mean_delay,
            event_count=len(valid_deltas)
        )
        pairs.append(pair)
        logger.debug(f"Calculated metrics for pair ({author_a}, {author_b}): mean={mean_delay:.2f}s, var={variance:.2f}")

    logger.info(f"Identified {len(pairs)} unique contributor pairs")
    return pairs


def calculate_project_level_metrics(pairs: List[ContributorPair]) -> Dict[str, float]:
    """
    Calculate project-level aggregate metrics from contributor pairs.

    Uses weighted mean based on event count as per plan.md.

    Args:
        pairs: List of ContributorPair objects.

    Returns:
        Dictionary with project-level metrics.
    """
    if not pairs:
        return {
            'project_mean_delay': 0.0,
            'project_variance': 0.0,
            'total_pairs': 0,
            'total_events': 0
        }

    total_events = sum(p.event_count for p in pairs)
    if total_events == 0:
        return {
            'project_mean_delay': 0.0,
            'project_variance': 0.0,
            'total_pairs': len(pairs),
            'total_events': 0
        }

    # Weighted mean of mean_delay
    weighted_sum = sum(p.mean_delay * p.event_count for p in pairs)
    project_mean_delay = weighted_sum / total_events

    # Weighted variance calculation
    # Variance of the pooled data is not simply the weighted average of variances
    # But for simplicity and following "weighted mean" instruction for aggregation:
    # We calculate a weighted average of the variances as a proxy for project-level variance
    weighted_var_sum = sum(p.response_time_variance * p.event_count for p in pairs)
    project_variance = weighted_var_sum / total_events

    return {
        'project_mean_delay': project_mean_delay,
        'project_variance': project_variance,
        'total_pairs': len(pairs),
        'total_events': total_events
    }
