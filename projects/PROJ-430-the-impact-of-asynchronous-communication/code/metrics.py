"""
Metrics calculation module for asynchronous communication analysis.
Implements pair-level metric derivation and persistence.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any, Iterable
from collections import defaultdict
import statistics
import logging
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from config import get_config, ensure_directories_exist
from utils.logger import get_logger

# Configure logger
logger = get_logger(__name__)


def is_bot_actor(login: str, actor_type: Optional[str] = None) -> bool:
    """
    Determine if an actor is a bot based on login name or type.
    Bots are identified by names ending in '[bot]' or type 'Bot'.
    """
    if not login:
        return False
    if login.endswith('[bot]'):
        return True
    if actor_type and actor_type == 'Bot':
        return True
    return False


def identify_pairs_and_calculate_metrics(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify contributor pairs and calculate response time variance and mean delay.
    
    Args:
        events: List of event dictionaries with keys:
                - project_id
                - author_id (or user.login)
                - timestamp (or created_at)
                - text (optional)
                
    Returns:
        List of dictionaries with pair metrics:
        - project_id
        - pair_id (sorted tuple of author IDs)
        - response_time_variance
        - mean_delay
        - pair_count (number of interactions)
    """
    # Group events by project and pair
    # Pair is defined as any two distinct authors who have exchanged at least one message
    # We sort author IDs to create a canonical pair identifier
    
    project_pair_events = defaultdict(list)
    
    # Normalize events and group by project and pair
    for event in events:
        # Extract fields with fallbacks for different schema variations
        project_id = event.get('project_id') or event.get('repository_id')
        author = event.get('user', {}) or {}
        author_id = event.get('author_id') or author.get('id') or author.get('login')
        timestamp_str = event.get('timestamp') or event.get('created_at')
        
        if not all([project_id, author_id, timestamp_str]):
            continue
        
        # Skip bot events
        if is_bot_actor(author.get('login', ''), author.get('type')):
            continue
        
        try:
            # Parse timestamp - handle multiple formats
            if isinstance(timestamp_str, str):
                # Try ISO format first
                if 'T' in timestamp_str:
                    ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    ts = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            else:
                ts = datetime.fromtimestamp(timestamp_str)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse timestamp {timestamp_str}: {e}")
            continue
        
        # Create canonical pair ID (sorted tuple of author IDs)
        # We need to track interactions between pairs, so we'll collect all events
        # for each project and then process pairs
        
        project_pair_events[(project_id, author_id)].append({
            'timestamp': ts,
            'author_id': author_id
        })
    
    # Now process pairs: find pairs of authors who have exchanged messages
    pair_metrics = []
    
    for (project_id, author_id), author_events in project_pair_events.items():
        # Sort events by timestamp
        author_events.sort(key=lambda x: x['timestamp'])
        
        # We need to find interactions with other authors in the same project
        # Group all events by project
        project_events = defaultdict(list)
        for (proj_id, auth_id), evts in project_pair_events.items():
            if proj_id == project_id:
                project_events[auth_id].extend(evts)
        
        # For this author, find all other authors in the same project
        other_authors = [a for a in project_events.keys() if a != author_id]
        
        # Calculate metrics for each pair interaction
        for other_author in other_authors:
            # Combine events from both authors, sorted by time
            all_pair_events = sorted(
                project_events[author_id] + project_events[other_author],
                key=lambda x: x['timestamp']
            )
            
            if len(all_pair_events) < 2:
                continue
            
            # Calculate inter-arrival times (time between consecutive events)
            inter_arrival_times = []
            for i in range(1, len(all_pair_events)):
                delta = (all_pair_events[i]['timestamp'] - all_pair_events[i-1]['timestamp']).total_seconds()
                inter_arrival_times.append(delta)
            
            if not inter_arrival_times:
                continue
            
            # Calculate metrics
            mean_delay = statistics.mean(inter_arrival_times)
            
            if len(inter_arrival_times) > 1:
                response_time_variance = statistics.variance(inter_arrival_times)
            else:
                # Variance of a single value is 0
                response_time_variance = 0.0
            
            # Create canonical pair ID (sorted)
            pair_id = tuple(sorted([author_id, other_author]))
            
            pair_metrics.append({
                'project_id': project_id,
                'pair_id': str(pair_id),  # Convert to string for parquet compatibility
                'response_time_variance': response_time_variance,
                'mean_delay': mean_delay,
                'pair_count': len(inter_arrival_times)
            })
    
    # Remove duplicates (each pair might be processed twice)
    seen_pairs = set()
    unique_metrics = []
    for metric in pair_metrics:
        pair_key = (metric['project_id'], metric['pair_id'])
        if pair_key not in seen_pairs:
            seen_pairs.add(pair_key)
            unique_metrics.append(metric)
    
    return unique_metrics


def calculate_and_persist_pair_metrics(events: List[Dict[str, Any]], output_path: str) -> str:
    """
    Calculate pair-level metrics and persist to parquet file.
    
    This is the main entry point for T012.
    
    Args:
        events: List of event dictionaries (raw or normalized)
        output_path: Path to output parquet file
        
    Returns:
        Path to the created parquet file
    """
    logger.info(f"Starting metric calculation for {len(events)} events")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    ensure_directories_exist([output_dir])
    
    # Calculate metrics
    metrics = identify_pairs_and_calculate_metrics(events)
    
    if not metrics:
        logger.warning("No pair metrics calculated. Creating empty parquet file.")
        # Create empty dataframe with correct schema
        df = pd.DataFrame(columns=[
            'project_id', 'pair_id', 'response_time_variance', 
            'mean_delay', 'pair_count'
        ])
        df.to_parquet(output_path, index=False)
        return output_path
    
    # Convert to DataFrame
    df = pd.DataFrame(metrics)
    
    # Ensure correct column order and types
    df = df[[
        'project_id', 'pair_id', 'response_time_variance', 
        'mean_delay', 'pair_count'
    ]]
    
    # Fill any NaN values with 0 (shouldn't happen but safety)
    df['response_time_variance'] = df['response_time_variance'].fillna(0.0)
    df['mean_delay'] = df['mean_delay'].fillna(0.0)
    df['pair_count'] = df['pair_count'].fillna(0).astype(int)
    
    # Validate no NaN in critical columns
    if df['response_time_variance'].isna().any() or df['mean_delay'].isna().any():
        logger.error("NaN values found in critical columns after processing")
        raise ValueError("NaN values detected in response_time_variance or mean_delay")
    
    # Persist to parquet
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Successfully persisted {len(df)} pair metrics to {output_path}")
    logger.info(f"Schema: {df.columns.tolist()}")
    logger.info(f"Sample: {df.head(2).to_dict()}")
    
    return output_path


def calculate_project_level_metrics(pair_metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate pair-level metrics to project level using median variance.
    
    Args:
        pair_metrics: List of pair metric dictionaries
        
    Returns:
        List of project-level metrics
    """
    # Group by project_id
    project_pairs = defaultdict(list)
    for metric in pair_metrics:
        project_pairs[metric['project_id']].append(metric)
    
    project_metrics = []
    for project_id, pairs in project_pairs.items():
        if not pairs:
            continue
        
        # Calculate median variance (per FR-010)
        variances = [p['response_time_variance'] for p in pairs]
        median_variance = statistics.median(variances) if variances else 0.0
        
        # Mean of mean delays
        mean_delays = [p['mean_delay'] for p in pairs]
        overall_mean_delay = statistics.mean(mean_delays) if mean_delays else 0.0
        
        # Team size (unique authors in this project's pairs)
        authors = set()
        for p in pairs:
            # Parse pair_id back to get authors
            pair_str = p['pair_id']
            # Extract from string representation of tuple
            import ast
            try:
                pair_tuple = ast.literal_eval(pair_str)
                authors.update(pair_tuple)
            except:
                # Fallback: count pairs as approximation
                pass
        
        team_size = len(authors) if authors else len(pairs)
        
        project_metrics.append({
            'project_id': project_id,
            'median_variance': median_variance,
            'mean_delay': overall_mean_delay,
            'team_size': team_size,
            'pair_count': len(pairs)
        })
    
    return project_metrics


def run_metrics_pipeline(events: List[Dict[str, Any]], output_path: str) -> str:
    """
    Run the full metrics pipeline: calculate pair metrics and persist.
    
    Args:
        events: List of event dictionaries
        output_path: Output path for pair metrics parquet
        
    Returns:
        Path to output file
    """
    return calculate_and_persist_pair_metrics(events, output_path)


if __name__ == "__main__":
    # Simple test with sample data
    import sys
    
    sample_events = [
        {
            'project_id': '12345',
            'author_id': 'user1',
            'timestamp': '2023-01-01T10:00:00Z',
            'text': 'Hello'
        },
        {
            'project_id': '12345',
            'author_id': 'user2',
            'timestamp': '2023-01-01T10:05:00Z',
            'text': 'Hi there'
        },
        {
            'project_id': '12345',
            'author_id': 'user1',
            'timestamp': '2023-01-01T10:15:00Z',
            'text': 'How are you?'
        },
        {
            'project_id': '12345',
            'author_id': 'user2',
            'timestamp': '2023-01-01T10:20:00Z',
            'text': 'Good!'
        }
    ]
    
    output_file = 'data/derived/pair_metrics.parquet'
    result = calculate_and_persist_pair_metrics(sample_events, output_file)
    print(f"Metrics written to: {result}")
    
    # Verify
    df = pd.read_parquet(output_file)
    print(f"Output shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(df.head())
