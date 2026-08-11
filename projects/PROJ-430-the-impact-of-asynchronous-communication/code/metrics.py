from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict
import statistics
import logging
import json
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
from pathlib import Path

from models import Event, ContributorPair, EventType, Project, PairMetric
from config import get_config, ensure_directories_exist
from utils.logger import get_logger

logger = get_logger(__name__)

def is_bot_actor(actor: str) -> bool:
    """Check if an actor is a bot based on name or type."""
    if not actor:
        return True
    if actor.endswith('[bot]'):
        return True
    # Common bot patterns
    bot_patterns = ['bot', 'dependabot', 'renovate']
    return any(pattern in actor.lower() for pattern in bot_patterns)

def identify_pairs_and_calculate_metrics(events: List[Dict[str, Any]], output_path: str) -> None:
    """
    Identify contributor pairs, calculate inter-arrival times, variance, and mean delay.
    Persists results to parquet file.
    
    Args:
        events: List of event dictionaries from data ingestion
        output_path: Path to write the output parquet file
    """
    logger.info(f"Starting metric calculation for {len(events)} events")
    ensure_directories_exist(Path(output_path))

    # Filter out bot events and self-replies
    valid_events = []
    for event in events:
        actor = event.get('user', {}).get('login', '') or event.get('actor', '')
        if not is_bot_actor(actor):
            valid_events.append(event)
        else:
            logger.debug(f"Filtered bot event: {actor}")

    logger.info(f"Processed {len(valid_events)} non-bot events")

    # Group events by project and thread (issue/PR)
    project_threads: Dict[str, Dict[str, List[Event]]] = defaultdict(lambda: defaultdict(list))
    
    for event in valid_events:
        project_id = event.get('repository', {}).get('full_name', 'unknown')
        thread_id = event.get('thread_id') or event.get('issue', {}).get('number')
        if not thread_id:
            # For comments without explicit thread, use event ID or generate one
            thread_id = event.get('id', 'unknown')
        
        # Parse timestamp
        timestamp_str = event.get('created_at') or event.get('timestamp')
        if not timestamp_str:
            continue
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            continue

        actor = event.get('user', {}).get('login', '') or event.get('actor', '')
        event_type = event.get('type', 'comment')
        
        project_threads[project_id][thread_id].append({
            'timestamp': timestamp,
            'actor': actor,
            'event_type': event_type,
            'event_id': event.get('id')
        })

    # Calculate pair metrics
    pair_metrics: Dict[Tuple[str, str, str], Dict[str, Any]] = defaultdict(
        lambda: {'delays': [], 'count': 0}
    )

    for project_id, threads in project_threads.items():
        for thread_id, thread_events in threads.items():
            # Sort events by timestamp
            thread_events.sort(key=lambda x: x['timestamp'])
            
            # Identify pairs: any two distinct authors who exchanged messages
            for i in range(1, len(thread_events)):
                current = thread_events[i]
                previous = thread_events[i-1]
                
                if current['actor'] == previous['actor']:
                    continue  # Skip self-replies
                
                # Create pair ID (ordered alphabetically to avoid duplicates)
                actors = sorted([current['actor'], previous['actor']])
                pair_id = f"{actors[0]}_{actors[1]}"
                pair_key = (project_id, pair_id, thread_id)
                
                # Calculate inter-arrival time in seconds
                delay = (current['timestamp'] - previous['timestamp']).total_seconds()
                if delay >= 0:
                    pair_metrics[pair_key]['delays'].append(delay)
                    pair_metrics[pair_key]['count'] += 1

    # Aggregate to pair-level metrics
    results = []
    for (project_id, pair_id, thread_id), data in pair_metrics.items():
        delays = data['delays']
        count = data['count']
        
        if len(delays) < 2:
            # Cannot calculate variance with less than 2 data points
            mean_delay = sum(delays) / len(delays) if delays else 0.0
            variance = 0.0
        else:
            mean_delay = statistics.mean(delays)
            variance = statistics.variance(delays)
        
        results.append({
            'project_id': project_id,
            'pair_id': pair_id,
            'thread_id': thread_id,
            'response_time_variance': variance,
            'mean_delay': mean_delay,
            'pair_count': count
        })

    logger.info(f"Calculated metrics for {len(results)} pairs")

    # Create DataFrame and write to parquet
    if results:
        df = pd.DataFrame(results)
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        ensure_directories_exist(output_dir)
        
        # Write to parquet
        df.to_parquet(output_path, index=False)
        logger.info(f"Wrote metrics to {output_path}")
    else:
        # Create empty DataFrame with correct schema
        df = pd.DataFrame(columns=[
            'project_id', 'pair_id', 'thread_id', 
            'response_time_variance', 'mean_delay', 'pair_count'
        ])
        output_dir = Path(output_path).parent
        ensure_directories_exist(output_dir)
        df.to_parquet(output_path, index=False)
        logger.warning(f"No pair metrics found. Created empty file at {output_path}")

def calculate_project_level_metrics(input_path: str, output_path: str) -> None:
    """
    Aggregate pair-level metrics to project-level using median variance.
    
    Args:
        input_path: Path to pair metrics parquet file
        output_path: Path to write project-level metrics CSV
    """
    logger.info(f"Calculating project-level metrics from {input_path}")
    ensure_directories_exist(Path(output_path))

    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}")
        return

    df = pd.read_parquet(input_path)
    
    if df.empty:
        logger.warning("Input data is empty. Creating empty project metrics.")
        empty_df = pd.DataFrame(columns=['project_id', 'median_variance', 'mean_delay', 'pair_count'])
        empty_df.to_csv(output_path, index=False)
        return

    # Aggregate by project
    project_metrics = df.groupby('project_id').agg(
        median_variance=('response_time_variance', 'median'),
        mean_delay=('mean_delay', 'mean'),
        pair_count=('pair_count', 'sum')
    ).reset_index()

    # Write to CSV
    project_metrics.to_csv(output_path, index=False)
    logger.info(f"Wrote project metrics to {output_path}")

def run_metrics_pipeline(events_path: str, output_path: str, project_metrics_path: Optional[str] = None) -> None:
    """
    Run the full metrics pipeline: calculate pair metrics and optionally project metrics.
    
    Args:
        events_path: Path to raw events JSON file
        output_path: Path to write pair metrics parquet
        project_metrics_path: Optional path to write project metrics CSV
    """
    # Load events
    with open(events_path, 'r', encoding='utf-8') as f:
        events = json.load(f)
    
    logger.info(f"Loaded {len(events)} events from {events_path}")
    
    # Calculate pair metrics
    identify_pairs_and_calculate_metrics(events, output_path)
    
    # Calculate project metrics if path provided
    if project_metrics_path:
        calculate_project_level_metrics(output_path, project_metrics_path)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate and persist pair metrics")
    parser.add_argument("--events", required=True, help="Path to events JSON file")
    parser.add_argument("--output", required=True, help="Path to output parquet file")
    parser.add_argument("--project-metrics", help="Optional path to project metrics CSV")
    
    args = parser.parse_args()
    
    run_metrics_pipeline(args.events, args.output, args.project_metrics)
