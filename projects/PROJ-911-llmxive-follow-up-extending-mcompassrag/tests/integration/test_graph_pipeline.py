"""
Integration test for the full graph pipeline on sample data (US1).

This test verifies that the end-to-end graph construction and feature extraction
pipeline runs successfully on a small sample of real data (HotpotQA/Wikipedia),
producing valid graph artifacts and numerical feature vectors within the
specified time constraints.

Prerequisites:
- T004 (config.py with paths/seeds)
- T006 (data directories)
- T007/T008 (data_loader with sampling)
- T009 (contracts - skipped here as per task scope, but assumed present)
- T012 (vocabulary_builder to generate fixed_vocab.json)
- T013 (graph_builder)
- T014 (topology_extractor)
"""
import json
import os
import sys
import time
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

import pytest
import networkx as nx
import pandas as pd

# Add project root to path if running standalone
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import (
    PROJECT_ROOT,
    DATA_DIR,
    PROCESSED_DIR,
    RESULTS_DIR,
    MAX_DOCS,
    RANDOM_SEED,
)
from code.data_loader import load_hotpotqa_sample, get_disjoint_corpus_and_queries
from code.vocabulary_builder import build_fixed_vocabulary
from code.graph_builder import (
    load_fixed_vocab,
    tokenize_and_filter,
    build_co_occurrence_graph,
    build_graphs_for_corpus,
    save_graphs,
    extract_features_for_csv,
)
from code.topology_extractor import (
    load_graphs,
    calculate_topological_metrics,
    extract_topological_features,
    save_features,
)
from code.utils.hash_artifacts import calculate_sha256


# --- Configuration for the Test ---
# We use a very small sample to ensure the test runs quickly (< 300s budget)
# The task requires N <= 360, but for integration testing speed, we use a smaller N.
TEST_SAMPLE_SIZE = 10
WINDOW_SIZE = 10
MIN_TERM_DIVERSITY = 5


def setup_module(module):
    """
    Setup: Ensure data directories exist and generate necessary intermediate files
    (like fixed_vocab.json) if they don't exist, to make the test self-contained.
    """
    # Ensure directories exist
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # If fixed_vocab.json doesn't exist, we must generate it using the real data loader
    # This is a "bootstrap" step for the integration test to run without prior tasks
    # completing successfully in the same session (though in real CI, T012 would run first).
    vocab_path = Path(PROCESSED_DIR) / "fixed_vocab.json"
    if not vocab_path.exists():
        # Load a larger sample to build a robust vocabulary
        docs = load_hotpotqa_sample(n_docs=50)
        texts = [doc["title"] + " " + doc["text"] for doc in docs]
        build_fixed_vocabulary(texts, output_path=str(vocab_path), top_k=1000)


def teardown_module(module):
    """
    Teardown: Optional cleanup if we created temporary artifacts during the test.
    For this test, we write to the standard data dir, so we leave artifacts for inspection.
    """
    pass


class TestGraphPipelineIntegration:
    """Integration tests for the full Graph Compass pipeline."""

    def test_full_pipeline_execution(self):
        """
        Test that the full pipeline (Load -> Vocab -> Graph -> Features)
        executes without errors on a sample dataset.
        """
        # 1. Load Data
        # We load a small sample to keep the test fast.
        # The real pipeline uses MAX_DOCS (360), but here we use a smaller number.
        docs = load_hotpotqa_sample(n_docs=TEST_SAMPLE_SIZE)
        assert len(docs) > 0, "Failed to load any documents."

        # 2. Load/Verify Vocabulary
        vocab_path = Path(PROCESSED_DIR) / "fixed_vocab.json"
        assert vocab_path.exists(), "fixed_vocab.json not found. Ensure T012 is run or bootstrap is working."
        vocab = load_fixed_vocab(str(vocab_path))
        assert len(vocab) > 0, "Vocabulary is empty."

        # 3. Process Documents & Build Graphs
        # We simulate the pipeline steps explicitly here to ensure order.
        processed_docs = []
        graphs_data = []

        start_time = time.time()

        for i, doc in enumerate(docs):
            doc_id = doc.get("id", f"doc_{i}")
            text = doc.get("title", "") + " " + doc.get("text", "")

            # Tokenize and filter
            tokens = tokenize_and_filter(text, vocab)

            # Check for low diversity (edge case coverage)
            if len(set(tokens)) < MIN_TERM_DIVERSITY:
                # In a real run, this might trigger a warning or default graph.
                # For integration test, we still proceed to see if the graph builder handles it.
                pass

            # Build graph
            G = build_co_occurrence_graph(tokens, window_size=WINDOW_SIZE)
            
            # Store data for later feature extraction
            processed_docs.append({
                "doc_id": doc_id,
                "tokens": tokens,
                "graph": G
            })
            
            graphs_data.append({
                "doc_id": doc_id,
                "nodes": list(G.nodes()),
                "edges": list(G.edges()),
                "num_nodes": G.number_of_nodes(),
                "num_edges": G.number_of_edges()
            })

        pipeline_time = time.time() - start_time
        assert pipeline_time < 300, f"Pipeline took too long: {pipeline_time}s (limit 300s)"

        # 4. Save Graphs (Intermediate Artifact)
        graphs_output_path = Path(PROCESSED_DIR) / "test_graphs.json"
        save_graphs(graphs_data, str(graphs_output_path))
        assert graphs_output_path.exists(), "Graphs file was not saved."

        # 5. Extract Topological Metrics
        # Load graphs back to simulate the next stage of the pipeline
        loaded_graphs = load_graphs(str(graphs_output_path))
        
        metrics_data = []
        for item in loaded_graphs:
            doc_id = item["doc_id"]
            G = item["graph"]
            
            # Calculate metrics
            metrics = calculate_topological_metrics(G)
            
            # Extract features
            features = extract_topological_features(doc_id, metrics)
            metrics_data.append(features)

        # 6. Save Features (Final Artifact)
        features_output_path = Path(PROCESSED_DIR) / "test_features.csv"
        save_features(metrics_data, str(features_output_path))
        
        assert features_output_path.exists(), "Features file was not saved."

        # 7. Verify Output Schema
        df = pd.read_csv(features_output_path)
        required_columns = [
            "doc_id", "num_nodes", "num_edges", "density", 
            "average_degree", "modularity", "avg_path_length", 
            "avg_clustering", "degree_centrality_mean", "betweenness_centrality_mean"
        ]
        
        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"
        
        assert len(df) == TEST_SAMPLE_SIZE, f"Expected {TEST_SAMPLE_SIZE} rows, got {len(df)}"

        # 8. Verify Numerical Validity
        # Ensure no NaNs in key metric columns
        metric_cols = ["density", "modularity", "avg_path_length", "avg_clustering"]
        for col in metric_cols:
            if col in df.columns:
                assert not df[col].isna().any(), f"NaN found in column {col}"

        # 9. Verify Hashing (T005 requirement)
        # We can't update the global state file in a test, but we can verify the hash function works on our artifact
        hash_val = calculate_sha256(str(features_output_path))
        assert len(hash_val) == 64, "SHA256 hash length is incorrect."

        print(f"Integration test passed. Processed {TEST_SAMPLE_SIZE} docs in {pipeline_time:.2f}s.")
        print(f"Artifacts saved to: {graphs_output_path}, {features_output_path}")


    def test_low_diversity_handling(self):
        """
        Test that the pipeline handles documents with very low term diversity
        (fewer than MIN_TERM_DIVERSITY unique tokens) gracefully without crashing.
        """
        # Create a synthetic low-diversity document
        low_div_text = "the the the the the"
        vocab_path = Path(PROCESSED_DIR) / "fixed_vocab.json"
        vocab = load_fixed_vocab(str(vocab_path))
        
        tokens = tokenize_and_filter(low_div_text, vocab)
        
        # Even if filtered, it might result in very few tokens
        G = build_co_occurrence_graph(tokens, window_size=WINDOW_SIZE)
        
        # The graph might be empty or have 1 node.
        # The topology extractor must handle this.
        metrics = calculate_topological_metrics(G)
        
        # Verify we get a result (even if zeros)
        assert isinstance(metrics, dict), "Metrics should be a dictionary"
        assert "num_nodes" in metrics, "num_nodes missing from metrics"
        
        # Specifically check that we don't crash on empty graph
        if G.number_of_nodes() == 0:
            # Expected behavior for empty graph
            assert metrics.get("modularity") == 0.0 or metrics.get("modularity") is None
            assert metrics.get("avg_path_length") == 0.0

    def test_deterministic_output(self):
        """
        Verify that running the pipeline twice with the same seed produces identical outputs.
        """
        import random
        import numpy as np
        
        # Set seeds
        random.seed(RANDOM_SEED)
        np.random.seed(RANDOM_SEED)
        
        docs = load_hotpotqa_sample(n_docs=5)
        
        # Run 1
        features_path_1 = Path(PROCESSED_DIR) / "test_det_run1.csv"
        self._run_pipeline_and_save(docs, str(features_path_1))
        
        # Reset seeds
        random.seed(RANDOM_SEED)
        np.random.seed(RANDOM_SEED)
        
        # Run 2
        features_path_2 = Path(PROCESSED_DIR) / "test_det_run2.csv"
        self._run_pipeline_and_save(docs, str(features_path_2))
        
        # Compare
        df1 = pd.read_csv(features_path_1)
        df2 = pd.read_csv(features_path_2)
        
        # Compare numeric columns (allow small float diff if any, but here should be exact)
        pd.testing.assert_frame_equal(df1, df2, check_names=True)


    def _run_pipeline_and_save(self, docs: List[Dict], output_path: str):
        """Helper to run the core pipeline logic and save to a specific path."""
        vocab_path = Path(PROCESSED_DIR) / "fixed_vocab.json"
        vocab = load_fixed_vocab(str(vocab_path))
        
        graphs_data = []
        for i, doc in enumerate(docs):
            doc_id = doc.get("id", f"doc_{i}")
            text = doc.get("title", "") + " " + doc.get("text", "")
            tokens = tokenize_and_filter(text, vocab)
            G = build_co_occurrence_graph(tokens, window_size=WINDOW_SIZE)
            graphs_data.append({
                "doc_id": doc_id,
                "nodes": list(G.nodes()),
                "edges": list(G.edges()),
                "num_nodes": G.number_of_nodes(),
                "num_edges": G.number_of_edges(),
                "graph": G
            })
        
        # Extract features
        metrics_data = []
        for item in graphs_data:
            G = item["graph"]
            metrics = calculate_topological_metrics(G)
            features = extract_topological_features(item["doc_id"], metrics)
            metrics_data.append(features)
        
        save_features(metrics_data, output_path)
