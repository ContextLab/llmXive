from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import statistics

from models import Event, ContributorPair, EventType, Project
from utils.logger import get_logger

logger = get_logger(__name__)

def identify_pairs_and_calculate_metrics(events: List[Event]) -> List[Dict]:
    """
    Identify contributor pairs and calculate inter-arrival times,
    response_time_variance, and mean_delay.
    """
    # Group events by project and sort by timestamp
    project_events = defaultdict(list)
    for e in events:
        project_events[e.project_id].append(e)

    results = []
    for project_id, evts in project_events.items():
        evts.sort(key=lambda x: x.timestamp)
        
        # Build pairs: any two distinct authors who exchanged messages
        pair_events = defaultdict(list)
        for i in range(len(evts) - 1):
            author_a = evts[i].author
            author_b = evts[i+1].author
            if author_a != author_b:
                # Sort pair alphabetically to ensure consistent key
                pair_key = tuple(sorted([author_a, author_b]))
                pair_events[pair_key].append((evts[i], evts[i+1]))

        for pair_key, exchanges in pair_events.items():
            delays = []
            for e1, e2 in exchanges:
                delta = (e2.timestamp - e1.timestamp).total_seconds()
                if delta > 0:
                    delays.append(delta)
            
            if delays:
                mean_delay = statistics.mean(delays)
                variance = statistics.variance(delays) if len(delays) > 1 else 0.0
                results.append({
                    "project_id": project_id,
                    "pair_key": f"{pair_key[0]}-{pair_key[1]}",
                    "mean_delay": mean_delay,
                    "response_time_variance": variance
                })
    
    return results

def calculate_project_level_metrics(pair_metrics: List[Dict]) -> Dict[str, float]:
    """
    Aggregate pair-level variances to project-level using weighted mean.
    Weight is based on the number of events (proxied by mean_delay inverse or count).
    For simplicity, we use a simple weighted mean based on delay magnitude here,
    but in a full implementation, event count would be the weight.
    """
    project_weights = defaultdict(list)
    project_variances = defaultdict(list)
    
    for m in pair_metrics:
        pid = m["project_id"]
        # Weight by 1/mean_delay as a proxy for interaction frequency
        weight = 1.0 / m["mean_delay"] if m["mean_delay"] > 0 else 0.0
        project_weights[pid].append(weight)
        project_variances[pid].append(m["response_time_variance"])

    project_results = {}
    for pid in project_weights:
        weights = project_weights[pid]
        variances = project_variances[pid]
        total_weight = sum(weights)
        if total_weight > 0:
            weighted_mean = sum(w * v for w, v in zip(weights, variances)) / total_weight
        else:
            weighted_mean = 0.0
        project_results[pid] = weighted_mean

    return project_results