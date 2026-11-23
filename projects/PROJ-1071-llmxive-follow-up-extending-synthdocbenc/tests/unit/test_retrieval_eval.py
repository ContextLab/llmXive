import os
import sys
import json
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from retrieval_eval import (
    generate_search_queries,
    construct_ground_truth_retrieval_set,
    load_index_metadata,
    save_perf_metrics,
    GROUND_TRUTH_PATH
)
from models.document import Document, MiddleThirdMetadata, Page

class TestRetrievalEval(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_raw_dir = os.path.join(self.temp_dir, "data", "raw")
        self.data_derived_dir = os.path.join(self.temp_dir, "data", "derived")
        os.makedirs(self.data_raw_dir, exist_ok=True)
        os.makedirs(self.data_derived_dir, exist_ok=True)
        
        # Mock metadata for testing
        self.mock_metadata = {
            "middle_third_metadata": {
                "doc_001": {
                    "pages": [
                        {
                            "page_id": 5,
                            "text_snippet": "This is the middle content of page 5."
                        },
                        {
                            "page_id": 6,
                            "text_snippet": "This is the middle content of page 6."
                        }
                    ]
                }
            }
        }
        
        # Create a mock document
        self.mock_doc = Document(
            id="doc_001",
            title="Test Doc",
            pages=[
                Page(page_id=1, text="First page"),
                Page(page_id=5, text="Middle page 5"),
                Page(page_id=6, text="Middle page 6"),
                Page(page_id=10, text="Last page")
            ],
            middle_third_metadata=MiddleThirdMetadata(pages=[
                {"page_id": 5, "text_snippet": "This is the middle content of page 5."},
                {"page_id": 6, "text_snippet": "This is the middle content of page 6."}
            ])
        )

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch('retrieval_eval.METADATA_PATH')
    def test_load_index_metadata_success(self, mock_path):
        """Test loading valid index metadata."""
        mock_path.return_value = os.path.join(self.temp_dir, "index_metadata.json")
        with open(mock_path.return_value, 'w') as f:
            json.dump(self.mock_metadata, f)
        
        result = load_index_metadata()
        self.assertEqual(result, self.mock_metadata)

    def test_generate_search_queries(self):
        """Test query generation from middle-third metadata."""
        queries = generate_search_queries([self.mock_doc], self.mock_metadata)
        
        self.assertEqual(len(queries), 2)
        self.assertEqual(queries[0]["question_id"], "doc_001_page_5")
        self.assertEqual(queries[0]["target_snippet_id"], "doc_001_5")
        self.assertEqual(queries[0]["ground_truth_page_id"], 5)
        
        self.assertIn("Question about content on page 5", queries[0]["query_text"])

    def test_construct_ground_truth_retrieval_set(self):
        """Test construction of the ground truth artifact."""
        queries = [
            {
                "question_id": "q1",
                "ground_truth_page_id": 5,
                "target_snippet_id": "doc_1_5",
                "doc_id": "doc_1"
            }
        ]
        
        ground_truth = construct_ground_truth_retrieval_set(queries)
        
        self.assertIn("q1", ground_truth)
        self.assertEqual(ground_truth["q1"]["correct_page_id"], 5)
        self.assertEqual(ground_truth["q1"]["correct_snippet_id"], "doc_1_5")

    def test_save_perf_metrics(self):
        """Test saving performance metrics."""
        metrics = {"test_key": "test_value", "time": 1.5}
        test_path = os.path.join(self.temp_dir, "perf_metrics_test.json")
        
        with patch('retrieval_eval.PERF_METRICS_PATH', test_path):
            save_perf_metrics(metrics)
        
        self.assertTrue(os.path.exists(test_path))
        with open(test_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data["retrieval_eval"]["test_key"], "test_value")

    def test_empty_documents(self):
        """Test behavior with empty document list."""
        queries = generate_search_queries([], self.mock_metadata)
        self.assertEqual(len(queries), 0)

    def test_missing_metadata(self):
        """Test behavior when metadata is missing for a document."""
        bad_metadata = {"middle_third_metadata": {}}
        queries = generate_search_queries([self.mock_doc], bad_metadata)
        self.assertEqual(len(queries), 0)

if __name__ == "__main__":
    unittest.main()