"""
Metrics Calculation Module.
Identifies contributor pairs and calculates response time variance and mean delay.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import statistics
import logging

from models import Event, ContributorPair, EventType, Project, PairMetric
from utils.logger import get_logger

logger = get_logger(__name__)

def identify_pairs_and_calculate_metrics(project: Project) -> Tuple[List[PairMetric], Dict[str, float]]:
    """
    Identifies pairs of contributors who exchanged messages and calculates metrics.
    Returns a list of PairMetrics and a project-level summary dict.
    """
    events = sorted(project.events, key=lambda e: e.created_at)
    
    # Group events by conversation thread (parent_id or issue_id)
    # For simplicity, we group by issue/PR ID (the root event ID)
    threads: Dict[str, List[Event]] = defaultdict(list)
    for event in events:
        # If it's a comment, it belongs to its parent. If it's an issue/PR, it's its own thread.
        if event.type == EventType.COMMENT and event.parent_id:
            # Extract root ID from comment ID (e.g., "repo#123#comment-456" -> "repo#123")
            root_id = event.parent_id
        else:
            root_id = event.id
        threads[root_id].append(event)

    pair_delays: Dict[Tuple[str, str], List[float]] = defaultdict(list)

    for thread_id, thread_events in threads.items():
        # Sort thread events by time
        thread_events.sort(key=lambda e: e.created_at)
        
        # Calculate inter-arrival times between distinct authors
        for i in range(1, len(thread_events)):
            prev_event = thread_events[i-1]
            curr_event = thread_events[i]
            
            if prev_event.author == curr_event.author:
                continue # Skip self-replies
            
            # Create a canonical pair key (sorted tuple)
            pair_key = tuple(sorted([prev_event.author, curr_event.author]))
            
            delay_seconds = (curr_event.created_at - prev_event.created_at).total_seconds()
            if delay_seconds >= 0:
                pair_delays[pair_key].append(delay_seconds)

    pair_metrics = []
    total_variances = []
    total_counts = []

    for (author_a, author_b), delays in pair_delays.items():
        if not delays:
            continue
        
        mean_delay = statistics.mean(delays)
        variance = statistics.variance(delays) if len(delays) > 1 else 0.0
        count = len(delays)
        
        pair_metric = PairMetric(
            pair=ContributorPair(author_a=author_a, author_b=author_b),
            mean_delay=mean_delay,
            response_time_variance=variance,
            count=count
        )
        pair_metrics.append(pair_metric)
        
        # For weighted mean calculation at project level
        total_variances.append(variance)
        total_counts.append(count)

    # Calculate project-level weighted mean variance
    # Weighted mean variance = sum(variance_i * count_i) / sum(count_i)
    if total_counts:
        weighted_variance = sum(v * c for v, c in zip(total_variances, total_counts)) / sum(total_counts)
        project_mean_delay = statistics.mean([p.mean_delay for p in pair_metrics]) if pair_metrics else 0.0
    else:
        weighted_variance = 0.0
        project_mean_delay = 0.0

    project_metrics = {
        "mean_delay": project_mean_delay,
        "weighted_variance": weighted_variance
    }

    return pair_metrics, project_metrics

def calculate_project_level_metrics(pair_metrics: List[PairMetric]) -> Dict[str, float]:
    """
    Aggregates pair-level metrics to project level.
    Specifically calculates the weighted mean of variances.
    """
    if not pair_metrics:
        return {"mean_delay": 0.0, "weighted_variance": 0.0}
    
    total_variances = [p.response_time_variance for p in pair_metrics]
    total_counts = [p.count for p in pair_metrics]
    
    weighted_variance = sum(v * c for v, c in zip(total_variances, total_counts)) / sum(total_counts)
    mean_delay = sum(p.mean_delay for p in pair_metrics) / len(pair_metrics)
    
    return {
        "mean_delay": mean_delay,
        "weighted_variance": weighted_variance
    }
