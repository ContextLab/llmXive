"""
Unit tests for T014d: vector_db.py execution and output verification.
"""
import os
import sys
import tempfile
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path if needed
code_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(code_root / "code"))

from src.retrieval.vector_db import (
    load_flattened_vectors,
    compute_index_structure,
    prepare_for_serialization,
    save_index,
    main
)
from src.utils.config import get_project_root


class TestVectorDBExecution:
    """Test the full execution flow of vector_db.py"""

    @pytest.fixture
    def mock_weights_files(self, tmp_path):
        """Create mock weights files for testing"""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock A and B matrices
        A_alfworld = np.random.randn(100, 50).astype(np.float32)
        B_alfworld = np.random.randn(50, 200).astype(np.float32)
        
        A_searchqa = np.random.randn(100, 50).astype(np.float32)
        B_searchqa = np.random.randn(50, 200).astype(np.float32)
        
        # Save as npz
        np.savez(raw_dir / "alfworld_weights.npz", A=A_alfworld, B=B_alfworld)
        np.savez(raw_dir / "searchqa_weights.npz", A=A_searchqa, B=B_searchqa)
        
        return raw_dir

    def test_load_flattened_vectors(self, mock_weights_files):
        """Test loading and flattening of weights"""
        vectors, metadata = load_flattened_vectors(mock_weights_files)
        
        assert vectors is not None
        assert len(vectors.shape) == 2
        assert vectors.shape[0] == 2  # 2 sources
        
        # Check normalization
        norms = np.linalg.norm(vectors, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-6)
        
        assert "task_desc" in metadata
        assert "source" in metadata
        assert len(metadata["source"]) == 2

    def test_compute_index_structure(self, mock_weights_files):
        """Test index structure computation"""
        vectors, metadata = load_flattened_vectors(mock_weights_files)
        structure = compute_index_structure(vectors, metadata)
        
        assert "n_samples" in structure
        assert "dimension" in structure
        assert "dtype" in structure
        assert "max_norm_deviation" in structure
        assert structure["max_norm_deviation"] < 1e-5

    def test_prepare_for_serialization(self, mock_weights_files):
        """Test serialization preparation"""
        vectors, metadata = load_flattened_vectors(mock_weights_files)
        structure = compute_index_structure(vectors, metadata)
        package = prepare_for_serialization(vectors, metadata, structure)
        
        assert "vectors" in package
        assert "metadata" in package
        assert "structure" in package
        assert "version" in package
        
        # Check for NaN/Inf
        assert not np.any(np.isnan(package["vectors"]))
        assert not np.any(np.isinf(package["vectors"]))

    def test_save_index(self, mock_weights_files, tmp_path):
        """Test index saving and checksum verification"""
        vectors, metadata = load_flattened_vectors(mock_weights_files)
        structure = compute_index_structure(vectors, metadata)
        package = prepare_for_serialization(vectors, metadata, structure)
        
        output_path = tmp_path / "test_index.npz"
        result = save_index(package, output_path)
        
        assert result["exists"]
        assert output_path.exists()
        assert "checksum_sha256" in result
        assert result["n_samples"] == 2
        
        # Verify loaded data matches
        loaded = np.load(output_path)
        assert "vectors" in loaded
        assert np.allclose(loaded["vectors"], package["vectors"])

    @patch('src.utils.config.get_project_root')
    @patch('src.utils.config.get_data_path')
    @patch('src.utils.config.ensure_directories')
    def test_main_execution(self, mock_ensure_dirs, mock_get_data, mock_get_root, mock_weights_files, tmp_path):
        """Test the main() function execution flow"""
        # Setup mocks
        mock_get_root.return_value = tmp_path
        mock_get_data.return_value = tmp_path / "data"
        
        # Create necessary directories
        (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
        (tmp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
        
        # Copy mock weights to expected location
        import shutil
        shutil.copy(mock_weights_files / "alfworld_weights.npz", tmp_path / "data" / "raw" / "alfworld_weights.npz")
        shutil.copy(mock_weights_files / "searchqa_weights.npz", tmp_path / "data" / "raw" / "searchqa_weights.npz")
        
        # Run main
        result = main()
        
        assert result["status"] == "success"
        assert "output_path" in result
        assert "checksum" in result
        assert "shape" in result
        assert Path(result["output_path"]).exists()

    def test_missing_weights_file(self, tmp_path):
        """Test error handling for missing weights"""
        data_dir = tmp_path / "raw"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Only create one file, missing the other
        A = np.random.randn(10, 10)
        B = np.random.randn(10, 10)
        np.savez(data_dir / "alfworld_weights.npz", A=A, B=B)
        
        with pytest.raises(FileNotFoundError):
            load_flattened_vectors(data_dir)

    def test_invalid_weights_format(self, tmp_path):
        """Test error handling for invalid weights format"""
        data_dir = tmp_path / "raw"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create file without A or B keys
        np.savez(data_dir / "alfworld_weights.npz", X=np.random.randn(10, 10))
        np.savez(data_dir / "searchqa_weights.npz", Y=np.random.randn(10, 10))
        
        with pytest.raises(ValueError):
            load_flattened_vectors(data_dir)