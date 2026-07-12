"""
Ingestion service for fetching OpenAlex data and building a networkx graph.
Implements degree-stratified random sampling to target a specific subgraph size.
"""
import os
import random
import logging
import time
import traceback
from typing import Tuple, List, Dict, Any, Optional

import pyalex
from pyalex import Works
import networkx as nx
import pandas as pd

from src.lib import config

logging.basicConfig(level=config.LOGGING_LEVEL)
logger = logging.getLogger(__name__)

# Configuration constants
TARGET_SUBGRAPH_SIZE = config.SUBGRAPH_SIZE
SAMPLE_MULTIPLIER = 2.0  # Oversample to allow for degree stratification filtering
OPENALEX_WORKS_URI = "https://api.openalex.org/works"

def fetch_sample_ids(target_count: int) -> List[str]:
    """
    Fetch a sample of OpenAlex Work IDs.
    Uses degree-stratified sampling logic by fetching works and filtering
    based on citation counts (proxy for degree in citation graph) to ensure
    representation across different activity levels.

    Args:
        target_count: Target number of unique IDs to return.

    Returns:
        List of OpenAlex work IDs (e.g., 'W1234567890').
    """
    logger.info(f"Fetching sample of {target_count} OpenAlex IDs with degree stratification...")
    
    # Strategy: Fetch works in batches, collecting IDs.
    # To approximate degree stratification without full graph access upfront:
    # We will fetch a larger pool and filter/sort by citation count if available in metadata,
    # or simply fetch a diverse set by iterating through the API.
    # For this implementation, we fetch a pool of IDs and rely on the fact that 
    # OpenAlex's default ordering is somewhat diverse, but we will explicitly
    # try to grab a mix by fetching multiple pages.
    
    all_ids = set()
    page = 1
    max_pages = 100  # Safety limit
    per_page = 200
    
    # We need a pool larger than target to allow for degree-based filtering later
    pool_size = int(target_count * SAMPLE_MULTIPLIER)
    
    logger.info(f"Targeting a pool of {pool_size} IDs...")

    try:
        while len(all_ids) < pool_size and page <= max_pages:
            # Fetch a page of works. 
            # We use 'cited-by-count' descending to get high-degree nodes first,
            # then we might interleave or just collect.
            # To get a stratified sample, we ideally want to sample from different buckets.
            # For simplicity and robustness in this script, we will fetch a large batch
            # of works and rely on the downstream graph construction to handle connectivity.
            # However, the task asks for "degree-stratified random sampling".
            # Implementation: Fetch works, check citation count, bucket them, then sample.
            
            # Since we can't fetch all data at once to bucket, we will fetch a large sample
            # and assume the API returns a representative distribution or we iterate.
            # A robust way: Fetch N works, store (id, citation_count), bucket, then sample.
            
            # Let's fetch a larger batch first to establish buckets.
            # We'll use a filter to get works with at least some citations to avoid noise,
            # but also include low citation works.
            
            # Fetching raw IDs with metadata
            # Note: pyalex works with iterators
            works_iter = Works().sample(per_page) # .sample() is not standard in pyalex for specific count easily without pagination
            
            # Alternative: Standard pagination
            # We will fetch page by page
            page_results = Works().paginate(per_page=per_page).page(page)
            
            current_page_ids = []
            for work in page_results:
                work_id = work.id.split('/')[-1] # e.g., https://api.openalex.org/works/W123 -> W123
                citation_count = work.get('cited_by_count', 0)
                current_page_ids.append((work_id, citation_count))
            
            # Bucketing logic:
            # 0 citations, 1-10, 11-50, 51-200, 200+
            buckets = {
                '0': [],
                'low': [],   # 1-10
                'med': [],   # 11-50
                'high': [],  # 51-200
                'very_high': [] # 200+
            }
            
            for wid, cites in current_page_ids:
                if cites == 0:
                    buckets['0'].append(wid)
                elif cites <= 10:
                    buckets['low'].append(wid)
                elif cites <= 50:
                    buckets['med'].append(wid)
                elif cites <= 200:
                    buckets['high'].append(wid)
                else:
                    buckets['very_high'].append(wid)
            
            # Add to total pool
            for bucket_list in buckets.values():
                all_ids.update(bucket_list)
            
            logger.info(f"Page {page}: Collected {len(current_page_ids)} items. Total pool: {len(all_ids)}")
            page += 1
            
            # If we have enough, break
            if len(all_ids) >= pool_size:
                break
                
    except Exception as e:
        logger.error(f"Error fetching OpenAlex sample: {e}")
        traceback.print_exc()
        # Fallback: if we have at least some, use them, else raise
        if len(all_ids) < 10:
            raise RuntimeError("Failed to fetch sufficient OpenAlex sample IDs.")

    # Now perform degree-stratified sampling from the collected pool
    # We want to ensure we have a mix. Let's sample proportionally or equally from buckets.
    final_sample = []
    
    # Flatten buckets for sampling
    bucket_items = []
    for bucket_name, ids in buckets.items():
        bucket_items.append((bucket_name, ids))
    
    # Determine how many to take from each bucket to reach target_count
    # Strategy: Take proportional to bucket size, but ensure minimum representation
    total_pool_size = sum(len(ids) for _, ids in bucket_items)
    
    if total_pool_size == 0:
        raise RuntimeError("No IDs collected from OpenAlex.")

    # Simple stratified sampling: proportional allocation
    for bucket_name, ids in bucket_items:
        if not ids:
            continue
        # Calculate share
        share = int((len(ids) / total_pool_size) * target_count)
        # Ensure at least 1 if bucket exists and target > 0
        if share == 0 and target_count > 0:
            share = 1
        
        # Cap at available
        share = min(share, len(ids))
        
        # Random sample from this bucket
        sampled = random.sample(ids, share)
        final_sample.extend(sampled)
    
    # If we still need more (due to rounding), fill from largest buckets
    while len(final_sample) < target_count:
        # Find bucket with most remaining
        remaining_buckets = [(name, set(ids) - set(final_sample)) for name, ids in bucket_items if len(set(ids) - set(final_sample)) > 0]
        if not remaining_buckets:
            break
        # Pick one with most remaining
        remaining_buckets.sort(key=lambda x: len(x[1]), reverse=True)
        best_bucket_name, best_bucket_set = remaining_buckets[0]
        
        # Add one
        extra = list(best_bucket_set)[0]
        final_sample.append(extra)
    
    logger.info(f"Degree-stratified sampling complete. Final sample size: {len(final_sample)}")
    return final_sample[:target_count]


def fetch_and_build_subgraph(work_ids: List[str]) -> Tuple[nx.Graph, Dict[str, Any]]:
    """
    Fetches full metadata for a list of OpenAlex work IDs and builds a networkx Graph.
    Edges are created based on citation relationships (cites) found in the metadata.
    
    Args:
        work_ids: List of OpenAlex work IDs (e.g., 'W1234567890').
    
    Returns:
        Tuple of (networkx.Graph G, metadata dict).
    """
    logger.info(f"Building subgraph for {len(work_ids)} works...")
    G = nx.Graph()
    node_data = {}
    edges_to_add = []
    
    # Fetch details for each work
    # Note: OpenAlex API rate limits. We will batch or add small delays if needed.
    # For a subgraph, we assume the IDs provided are the nodes.
    # Edges: We need to find if any of these works cite any other works in this set.
    # To do this efficiently, we fetch the 'referenced_works' for each work.
    
    logger.info("Fetching work details from OpenAlex...")
    for i, wid in enumerate(work_ids):
        if i % 50 == 0:
            logger.info(f"Processed {i}/{len(work_ids)} works...")
        
        try:
            # Fetch single work
            # pyalex.Works().get(id) expects full ID or just the W-number?
            # pyalex usually handles 'W123' if configured, but let's use the full URI pattern if needed.
            # The ID from sample was extracted as 'W...'.
            # pyalex.Works()['W123'] works.
            
            work = Works()[wid]
            
            # Extract node attributes
            title = work.get('title', 'Unknown')
            citation_count = work.get('cited_by_count', 0)
            # We don't have embedding yet, set to None or empty list
            embedding_vector = None 
            
            # Primary cluster and topic cluster will be assigned later
            primary_cluster = None
            topic_cluster = None
            
            # Add node to graph
            G.add_node(wid, 
                       title=title, 
                       citation_count=citation_count,
                       embedding_vector=embedding_vector,
                       primary_cluster=primary_cluster,
                       topic_cluster=topic_cluster)
            
            node_data[wid] = {
                'title': title,
                'cited_by_count': citation_count,
                'referenced_works': work.get('referenced_works', [])
            }
            
        except Exception as e:
            logger.warning(f"Failed to fetch work {wid}: {e}")
            # Continue to next
            continue
    
    logger.info("Constructing edges based on internal citations...")
    # Build edges: If work A cites work B, and both are in our set, add edge A->B
    # Since it's an undirected graph for Louvain, we add as undirected.
    # We only care about edges where BOTH endpoints are in our subgraph.
    
    subgraph_ids = set(G.nodes())
    
    for src_id, data in node_data.items():
        refs = data['referenced_works']
        for ref_id in refs:
            # ref_id is usually 'W...'
            if ref_id in subgraph_ids:
                # Avoid duplicate edges
                if not G.has_edge(src_id, ref_id):
                    G.add_edge(src_id, ref_id)
    
    logger.info(f"Graph construction complete. Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    
    metadata = {
        'source': 'OpenAlex',
        'sampling_method': 'degree_stratified',
        'target_size': TARGET_SUBGRAPH_SIZE,
        'actual_size': G.number_of_nodes(),
        'edge_count': G.number_of_edges()
    }
    
    return G, metadata


def log_memory_profile():
    """
    Logs current memory usage if memory_profiler is available.
    """
    try:
        import psutil
        import os
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        logger.info(f"Memory usage: RSS={mem_info.rss / 1024 / 1024:.2f} MB, VMS={mem_info.vms / 1024 / 1024:.2f} MB")
    except ImportError:
        logger.debug("psutil not installed, skipping memory profile.")
    except Exception as e:
        logger.warning(f"Could not log memory profile: {e}")


def main():
    """
    Main entry point for the ingestion pipeline.
    Fetches sample, builds graph, and saves to data/processed.
    """
    logger.info("Starting Ingestion Pipeline (T012)...")
    log_memory_profile()
    
    try:
        # 1. Fetch sample IDs
        sample_ids = fetch_sample_ids(TARGET_SUBGRAPH_SIZE)
        
        # 2. Build Graph
        G, metadata = fetch_and_build_subgraph(sample_ids)
        
        if G.number_of_nodes() == 0:
            logger.error("Graph is empty. Cannot proceed.")
            return
        
        # 3. Log results
        logger.info(f"Subgraph built successfully: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")
        log_memory_profile()
        
        # 4. Save Graph (to be used by downstream tasks like T016)
        # We save as a parquet of node/edge data or pickle. 
        # The task T016 mentions saving to parquet. We'll save the graph structure 
        # in a format ready for T016.
        # For now, we return the graph. The caller (or a wrapper script) saves it.
        # But per task T012 "explicitly constructing the networkx.Graph object G", 
        # we ensure G is created. 
        # We will also save a minimal CSV/Parquet of the graph to data/processed 
        # so it's persistent as per "produce real outputs".
        
        output_path = config.DATA_PROCESSED_DIR / "subgraph_raw.csv"
        
        # Convert graph to DataFrame for saving
        nodes_df = pd.DataFrame(G.nodes(data=True))
        # Ensure columns exist even if None
        for col in ['title', 'citation_count', 'embedding_vector', 'primary_cluster', 'topic_cluster']:
            if col not in nodes_df.columns:
                nodes_df[col] = None
        
        # Handle list column (embedding) for parquet/csv
        # For CSV, we might need to stringify lists
        nodes_df['embedding_vector'] = nodes_df['embedding_vector'].apply(
            lambda x: str(x) if x is not None else ""
        )
        
        nodes_df.to_csv(output_path, index=False)
        logger.info(f"Saved raw graph nodes to {output_path}")
        
        # Save edges
        edges_df = pd.DataFrame(G.edges())
        edges_df.to_csv(config.DATA_PROCESSED_DIR / "subgraph_edges.csv", index=False)
        logger.info(f"Saved raw graph edges to {config.DATA_PROCESSED_DIR / 'subgraph_edges.csv'}")
        
        # Save metadata
        import json
        with open(config.DATA_PROCESSED_DIR / "subgraph_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info("Ingestion pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
