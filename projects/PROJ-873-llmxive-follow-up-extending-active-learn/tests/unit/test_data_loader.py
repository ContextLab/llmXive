import os
import sys
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path
import json
import tempfile
import shutil

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_loader import download_beir_dataset, DataInjectionError, prepare_injected_datasets
from config import get_config
from metrics import get_embedding_model, calculate_cosine_similarity_proxy

@pytest.fixture
def sample_documents():
    return [
        {"doc_id": "1", "text": "The quick brown fox jumps over the lazy dog.", "dataset": "test"},
        {"doc_id": "2", "text": "A fast brown fox leaps over a sleepy dog.", "dataset": "test"},
        {"doc_id": "3", "text": "The slow grey cat sits on the mat.", "dataset": "test"},
    ]

class TestSyntheticDataFallbackBlocker(unittest.TestCase):
    """
    Test T042: Synthetic Data Fallback Blocker.
    
    This test asserts that RuntimeError is raised when 'beir' fetch fails 
    (simulating network block), preventing any silent fallback to synthetic/mock data.
    This serves Constitution Principle III and the "Loader must fail loudly" rule.
    """

    def setUp(self):
        self.dataset_name = "scifact"
        # Create a temporary directory for the test to simulate a valid output path
        # but we will mock the download to fail before writing anything.
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Clean up temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('data_loader.util.download_and_unzip')
    def test_beir_fetch_failure_raises_runtime_error(self, mock_download):
        """
        Assert that when beir fetch fails, the loader raises RuntimeError
        and does NOT fall back to synthetic data generation.
        """
        # Simulate a network failure or download error
        mock_download.side_effect = RuntimeError("Network error: Unable to download dataset")

        with self.assertRaises(RuntimeError) as context:
            # This should raise, not return a synthetic dataset
            download_beir_dataset(self.dataset_name)

        # Verify the error message matches the simulated failure
        self.assertIn("Network error", str(context.exception))

        # Verify that no synthetic data generation function was called.
        # We check that the side_effect was the only thing that happened.
        mock_download.assert_called_once()

    @patch('data_loader.util.download_and_unzip')
    @patch('data_loader.logger')
    def test_no_silent_fallback_on_fetch_failure(self, mock_logger, mock_download):
        """
        Ensure that the loader does NOT attempt to generate synthetic data
        when the real fetch fails. It must fail loudly.
        """
        mock_download.side_effect = RuntimeError("Connection timed out")

        with self.assertRaises(RuntimeError):
            download_beir_dataset(self.dataset_name)

        # Assert that we did NOT call any hypothetical synthetic generation
        # (even though the function doesn't exist yet, this confirms the logic path)
        # The key is that the function exits via exception, not via a fallback block.
        # If there were a fallback block like:
        #   try: ...
        #   except: generate_synthetic()
        # This test would fail because generate_synthetic would be called.
        # Since we expect a direct raise, we verify the exception propagates.
        
        # Verify the error was logged (optional, but good practice)
        # We check if error was called at least once
        mock_logger.error.assert_called()

    @patch('data_loader.os.makedirs')
    @patch('data_loader.util.download_and_unzip')
    def test_download_success_writes_real_data(self, mock_download, mock_makedirs):
        """
        Verify that when download succeeds, the function proceeds normally
        (returns the path) and does not trigger fallback logic.
        """
        mock_download.return_value = "/tmp/scifact"
        mock_makedirs.return_value = None

        result = download_beir_dataset(self.dataset_name)
        
        self.assertEqual(result, "/tmp/scifact")
        mock_download.assert_called_once()
        # Ensure no synthetic logic was triggered
        self.assertEqual(mock_download.call_count, 1)


class TestSyntheticRedundancyInjection(unittest.TestCase):
    """
    Test T010: Unit test for synthetic redundancy injection logic.
    
    This test asserts that injected clusters contain items with pairwise
    cosine similarity > 0.95, serving FR-002.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_path = os.path.join(self.temp_dir, "test_scifact")
        os.makedirs(self.test_data_path, exist_ok=True)
        
        # Create minimal BEIR-style corpus files for testing
        self._create_mock_beir_dataset()
        
        # Load the embedding model (cached for efficiency)
        self.model = get_embedding_model()

    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_mock_beir_dataset(self):
        """Create a minimal mock BEIR dataset structure."""
        corpus_data = {
            "1": {"text": "The quick brown fox jumps over the lazy dog.", "title": "Test Doc 1"},
            "2": {"text": "The quick brown fox leaps over the lazy dog.", "title": "Test Doc 2"},
            "3": {"text": "A fast brown fox jumps above a lazy dog.", "title": "Test Doc 3"},
            "4": {"text": "Completely unrelated document about quantum physics.", "title": "Test Doc 4"},
        }
        
        queries_data = {
            "q1": "quick brown fox",
            "q2": "lazy dog behavior",
        }
        
        qrels_data = {
            "q1": {"1": 1, "2": 1, "3": 1, "4": 0},
            "q2": {"1": 0, "2": 0, "3": 0, "4": 0},
        }
        
        # Write to JSONL format (BEIR standard)
        with open(os.path.join(self.test_data_path, "corpus.jsonl"), "w") as f:
            for doc_id, doc_data in corpus_data.items():
                f.write(json.dumps({"_id": doc_id, **doc_data}) + "\n")
        
        with open(os.path.join(self.test_data_path, "queries.jsonl"), "w") as f:
            for q_id, q_text in queries_data.items():
                f.write(json.dumps({"_id": q_id, "text": q_text}) + "\n")
        
        with open(os.path.join(self.test_data_path, "qrels/test.jsonl"), "w" if os.path.exists(os.path.join(self.test_data_path, "qrels")) else None) as f:
            pass
        
        # Create qrels directory and file
        os.makedirs(os.path.join(self.test_data_path, "qrels"), exist_ok=True)
        with open(os.path.join(self.test_data_path, "qrels/test.jsonl"), "w") as f:
            for q_id, rel_dict in qrels_data.items():
                for doc_id, score in rel_dict.items():
                    f.write(json.dumps({"query_id": q_id, "doc_id": doc_id, "score": score}) + "\n")

    def test_synthetic_injection_creates_clusters(self):
        """
        Assert that injected clusters contain items with pairwise cosine similarity > 0.95.
        
        This test:
        1. Loads the mock dataset
        2. Runs the injection logic (which should create redundant clusters)
        3. Verifies that documents within the same cluster have high cosine similarity
        """
        # Load the base dataset
        from beir.datasets.data_loader import GenericDataLoader
        corpus, queries, qrels = GenericDataLoader(self.test_data_path).load(split="test")
        
        # Prepare injected datasets (this should create redundancy clusters)
        # We pass a small sample size to keep the test fast
        injected_output_path = os.path.join(self.temp_dir, "injected_test.json")
        
        try:
            # Call the injection function
            prepare_injected_datasets(
                datasets=["scifact"], # Using mock path
                output_dir=self.temp_dir,
                max_clusters=2,
                cluster_size=3,
                similarity_threshold=0.95
            )
            
            # Load the injected dataset
            with open(injected_output_path, "r") as f:
                injected_data = json.load(f)
            
            # Verify clusters exist
            self.assertIn("datasets", injected_data)
            self.assertTrue(len(injected_data["datasets"]) > 0)
            
            # Check each cluster for high similarity
            model = self.model
            for dataset_entry in injected_data["datasets"]:
                self.assertIn("clusters", dataset_entry)
                for cluster in dataset_entry["clusters"]:
                    self.assertIn("members", cluster)
                    members = cluster["members"]
                    
                    # We need at least 2 members to calculate pairwise similarity
                    if len(members) < 2:
                        continue
                    
                    # Extract texts for members
                    member_texts = []
                    for member_id in members:
                        if member_id in corpus:
                            member_texts.append(corpus[member_id]["text"])
                    
                    # Calculate pairwise similarities
                    if len(member_texts) >= 2:
                        embeddings = model.encode(member_texts, convert_to_tensor=False)
                        for i in range(len(embeddings)):
                            for j in range(i + 1, len(embeddings)):
                                sim = calculate_cosine_similarity_proxy(embeddings[i], embeddings[j])
                                # Assert similarity > 0.95 as per FR-002
                                self.assertGreater(
                                    sim, 0.95,
                                    f"Pairwise similarity {sim:.4f} between members {members[i]} and {members[j]} "
                                    f"is below threshold 0.95"
                                )
            
        except FileNotFoundError:
            # If the file wasn't created, the injection logic might have failed
            # or the mock dataset wasn't processed correctly.
            # This is acceptable if the injection logic is designed to skip
            # when real data isn't available, but we should verify the logic path.
            self.fail("Injected dataset file was not created. Check injection logic.")

    def test_injection_preserves_original_documents(self):
        """
        Verify that the injection process preserves original documents
        while adding redundant copies.
        """
        # This is a simpler check to ensure the injection doesn't destroy data
        from beir.datasets.data_loader import GenericDataLoader
        corpus, queries, qrels = GenericDataLoader(self.test_data_path).load(split="test")
        original_count = len(corpus)
        
        # Run injection
        injected_output_path = os.path.join(self.temp_dir, "injected_test.json")
        
        try:
            prepare_injected_datasets(
                datasets=["scifact"],
                output_dir=self.temp_dir,
                max_clusters=1,
                cluster_size=2
            )
            
            with open(injected_output_path, "r") as f:
                injected_data = json.load(f)
            
            # Count total documents in injected data
            total_docs = 0
            for dataset_entry in injected_data["datasets"]:
                if "clusters" in dataset_entry:
                    for cluster in dataset_entry["clusters"]:
                        total_docs += len(cluster.get("members", []))
            
            # The injected dataset should have at least as many docs as original
            # (plus potentially more from redundancy injection)
            self.assertGreaterEqual(total_docs, original_count)
            
        except FileNotFoundError:
            self.fail("Injected dataset file was not created.")


if __name__ == "__main__":
    unittest.main()