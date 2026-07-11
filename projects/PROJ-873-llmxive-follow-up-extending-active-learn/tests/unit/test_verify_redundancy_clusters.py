"""
Unit tests for verify_redundancy_clusters functionality.
These tests validate the logic of cluster counting and size validation
without requiring the full injection pipeline to run.
"""
import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

# Add project root to path
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from code.data_loader import RedundancyCluster
from code.verify_redundancy_clusters import validate_clusters, load_clusters_from_file

class TestValidateClusters:
    def test_all_valid_clusters(self):
        """Test with all clusters having valid sizes (3-5 items)."""
        clusters = [
            RedundancyCluster(cluster_id="c1", items=["a", "b", "c"]),
            RedundancyCluster(cluster_id="c2", items=["x", "y", "z", "w"]),
            RedundancyCluster(cluster_id="c3", items=["1", "2", "3", "4", "5"]),
        ]
        
        report = validate_clusters(clusters)
        
        assert report['total_clusters'] == 3
        assert report['valid_clusters'] == 3
        assert report['invalid_clusters_count'] == 0
        assert report['meets_min_clusters_requirement'] == False  # Only 3 clusters
        assert report['all_clusters_valid_size'] == True
        assert report['fr002_compliant'] == False  # Not enough clusters

    def test_too_few_clusters(self):
        """Test with fewer than 20 clusters, all valid size."""
        clusters = [RedundancyCluster(cluster_id=f"c{i}", items=["a", "b", "c"]) for i in range(15)]
        
        report = validate_clusters(clusters)
        
        assert report['total_clusters'] == 15
        assert report['meets_min_clusters_requirement'] == False
        assert report['all_clusters_valid_size'] == True
        assert report['fr002_compliant'] == False

    def test_invalid_cluster_sizes(self):
        """Test with some clusters having invalid sizes."""
        clusters = [
            RedundancyCluster(cluster_id="c1", items=["a", "b", "c"]),  # Valid
            RedundancyCluster(cluster_id="c2", items=["a", "b"]),       # Invalid (too small)
            RedundancyCluster(cluster_id="c3", items=["a", "b", "c", "d", "e", "f"]),  # Invalid (too large)
            RedundancyCluster(cluster_id="c4", items=["x", "y", "z"]),  # Valid
        ]
        
        report = validate_clusters(clusters)
        
        assert report['total_clusters'] == 4
        assert report['valid_clusters'] == 2
        assert report['invalid_clusters_count'] == 2
        assert report['all_clusters_valid_size'] == False

    def test_fr002_compliance_true(self):
        """Test full compliance: >= 20 clusters, all valid size."""
        clusters = [
            RedundancyCluster(cluster_id=f"c{i}", items=["a", "b", "c", "d"])
            for i in range(25)
        ]
        
        report = validate_clusters(clusters)
        
        assert report['total_clusters'] == 25
        assert report['valid_clusters'] == 25
        assert report['invalid_clusters_count'] == 0
        assert report['meets_min_clusters_requirement'] == True
        assert report['all_clusters_valid_size'] == True
        assert report['fr002_compliant'] == True

class TestLoadClustersFromFile:
    def test_load_valid_file(self):
        """Test loading a valid JSON file with clusters."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            data = {
                "clusters": [
                    {"cluster_id": "c1", "items": ["a", "b", "c"]},
                    {"cluster_id": "c2", "items": ["x", "y", "z", "w"]}
                ]
            }
            json.dump(data, f)
            temp_path = f.name
        
        try:
            clusters = load_clusters_from_file(temp_path)
            assert len(clusters) == 2
            assert clusters[0].cluster_id == "c1"
            assert len(clusters[0].items) == 3
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_clusters_from_file("/nonexistent/path/file.json")

    def test_invalid_json(self):
        """Test error handling for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            with pytest.raises(json.JSONDecodeError):
                load_clusters_from_file(temp_path)
        finally:
            os.unlink(temp_path)