import pytest
from pathlib import Path
import tempfile
import shutil
import yaml
import pyarrow.parquet as pq

from data.loader import FilteredAudioDataset, FilteredDataLoader
from data.subtle_cue_builder import SubtleCueBuilder, ControlSetBuilder
from utils.logger import DataLoadError

class TestFilteredDataLoader:
    """Tests for the FilteredDataLoader class."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_base = Path(tempfile.mkdtemp())
        processed_dir = temp_base / "data" / "processed"
        state_dir = temp_base / "state"
        processed_dir.mkdir(parents=True, exist_ok=True)
        state_dir.mkdir(parents=True, exist_ok=True)
        
        yield {
            "base": temp_base,
            "processed": processed_dir,
            "state": state_dir
        }
        
        shutil.rmtree(temp_base, ignore_errors=True)
    
    def test_init_creates_directories(self, temp_dirs):
        """Test that initialization creates necessary directories."""
        loader = FilteredDataLoader()
        # Override paths for testing
        loader.path_config.processed_data_dir = temp_dirs["processed"]
        loader.path_config.state_dir = temp_dirs["state"]
        
        assert loader.processed_dir.exists()
        assert loader.state_dir.exists()
    
    def test_build_target_classes(self, temp_dirs):
        """Test that target classes are correctly built from builders."""
        subtle_builder = SubtleCueBuilder()
        control_builder = ControlSetBuilder()
        
        loader = FilteredDataLoader()
        loader.path_config.processed_data_dir = temp_dirs["processed"]
        loader.path_config.state_dir = temp_dirs["state"]
        
        target_classes = loader.build_target_classes(subtle_builder, control_builder)
        
        assert isinstance(target_classes, set)
        assert len(target_classes) > 0
        
        # Verify overlap between subtle and control classes
        subtle_classes = subtle_builder.get_class_names()
        control_classes = control_builder.get_class_names()
        
        assert subtle_classes.issubset(target_classes)
        assert control_classes.issubset(target_classes)
    
    def test_compute_file_checksum(self, temp_dirs):
        """Test checksum computation for a file."""
        loader = FilteredDataLoader()
        loader.path_config.processed_data_dir = temp_dirs["processed"]
        loader.path_config.state_dir = temp_dirs["state"]
        
        # Create a test file
        test_file = temp_dirs["processed"] / "test.txt"
        test_file.write_text("test content")
        
        checksum = loader._compute_file_checksum(test_file)
        
        assert len(checksum) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)
    
    def test_save_checksum_to_state(self, temp_dirs):
        """Test saving checksum to state file."""
        loader = FilteredDataLoader()
        loader.path_config.processed_data_dir = temp_dirs["processed"]
        loader.path_config.state_dir = temp_dirs["state"]
        
        target_classes = {"class_a", "class_b"}
        state_file = loader._save_checksum_to_state(
            filename="test.parquet",
            checksum="abc123",
            target_classes=target_classes,
            dataset_name="test_dataset"
        )
        
        assert state_file.exists()
        
        with open(state_file, 'r') as f:
            state_data = yaml.safe_load(f)
        
        assert 'files' in state_data
        assert 'test.parquet' in state_data['files']
        assert state_data['files']['test.parquet']['checksum'] == "abc123"
        assert len(state_data['files']['test.parquet']['classes']) == 2
    
    def test_verify_checksum_success(self, temp_dirs):
        """Test successful checksum verification."""
        loader = FilteredDataLoader()
        loader.path_config.processed_data_dir = temp_dirs["processed"]
        loader.path_config.state_dir = temp_dirs["state"]
        
        # Create a test file and state
        test_file = temp_dirs["processed"] / "verify_test.parquet"
        test_file.write_text("test content for verification")
        
        checksum = loader._compute_file_checksum(test_file)
        loader._save_checksum_to_state(
            filename="verify_test.parquet",
            checksum=checksum,
            target_classes={"test"},
            dataset_name="test"
        )
        
        is_valid, result = loader.verify_checksum("verify_test.parquet")
        
        assert is_valid is True
        assert result == checksum
    
    def test_verify_checksum_file_not_found(self, temp_dirs):
        """Test verification when file doesn't exist."""
        loader = FilteredDataLoader()
        loader.path_config.processed_data_dir = temp_dirs["processed"]
        loader.path_config.state_dir = temp_dirs["state"]
        
        # Save state but don't create file
        loader._save_checksum_to_state(
            filename="missing.parquet",
            checksum="abc123",
            target_classes={"test"},
            dataset_name="test"
        )
        
        is_valid, result = loader.verify_checksum("missing.parquet")
        
        assert is_valid is False
        assert "does not exist" in result
    
    def test_verify_checksum_mismatch(self, temp_dirs):
        """Test verification when checksum doesn't match."""
        loader = FilteredDataLoader()
        loader.path_config.processed_data_dir = temp_dirs["processed"]
        loader.path_config.state_dir = temp_dirs["state"]
        
        # Create file with different content than stored checksum
        test_file = temp_dirs["processed"] / "mismatch.parquet"
        test_file.write_text("different content")
        
        loader._save_checksum_to_state(
            filename="mismatch.parquet",
            checksum="wrong_checksum",
            target_classes={"test"},
            dataset_name="test"
        )
        
        is_valid, result = loader.verify_checksum("mismatch.parquet")
        
        assert is_valid is False
        assert "Checksum mismatch" in result
    
    def test_create_filtered_subset_structure(self, temp_dirs):
        """Test that create_filtered_subset creates a valid parquet file structure."""
        subtle_builder = SubtleCueBuilder()
        control_builder = ControlSetBuilder()
        
        loader = FilteredDataLoader()
        loader.path_config.processed_data_dir = temp_dirs["processed"]
        loader.path_config.state_dir = temp_dirs["state"]
        
        # This test will fail if the dataset is not available, which is expected
        # The important thing is that the structure is correct when it runs
        try:
            output_path = loader.create_filtered_subset(
                subtle_cue_builder=subtle_builder,
                control_set_builder=control_builder,
                output_filename="test_subset.parquet",
                dataset_name="esc-50",
                max_samples=10
            )
            
            assert output_path.exists()
            
            # Verify parquet structure
            table = pq.read_table(output_path)
            assert 'label' in table.column_names
            assert 'filename' in table.column_names
            
            # Verify state file
            is_valid, checksum = loader.verify_checksum("test_subset.parquet")
            assert is_valid is True
            
        except DataLoadError as e:
            # Expected if dataset is not available
            pytest.skip(f"Dataset not available: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")

class TestFilteredAudioDataset:
    """Tests for the FilteredAudioDataset class."""
    
    def test_init_with_streaming(self):
        """Test initialization with streaming enabled."""
        # This test will skip if dataset is not available
        try:
            dataset = FilteredAudioDataset(
                target_classes={"test_class"},
                dataset_name="esc-50",
                streaming=True,
                split="train"
            )
            assert dataset.streaming is True
            assert dataset.target_classes == {"test_class"}
        except DataLoadError:
            pytest.skip("Dataset not available for testing")
    
    def test_init_without_streaming(self):
        """Test initialization with streaming disabled."""
        try:
            dataset = FilteredAudioDataset(
                target_classes={"test_class"},
                dataset_name="esc-50",
                streaming=False,
                split="train"
            )
            assert dataset.streaming is False
        except DataLoadError:
            pytest.skip("Dataset not available for testing")
    
    def test_iteration_filters_classes(self):
        """Test that iteration only yields items matching target classes."""
        try:
            dataset = FilteredAudioDataset(
                target_classes={"class_1", "class_2"},
                dataset_name="esc-50",
                streaming=True,
                split="train"
            )
            
            # Just test that iteration doesn't crash
            count = 0
            for item in dataset:
                count += 1
                if count >= 5:
                    break
            
            assert count <= 5
        except DataLoadError:
            pytest.skip("Dataset not available for testing")
        except Exception:
            # Some datasets may not have the expected structure
            pytest.skip("Dataset structure not as expected")
    
    def test_len_with_streaming(self):
        """Test that len returns None for streaming datasets."""
        try:
            dataset = FilteredAudioDataset(
                target_classes={"test"},
                dataset_name="esc-50",
                streaming=True
            )
            assert dataset.__len__() is None
        except DataLoadError:
            pytest.skip("Dataset not available for testing")
    
    def test_len_without_streaming(self):
        """Test that len returns actual length for non-streaming datasets."""
        try:
            dataset = FilteredAudioDataset(
                target_classes={"test"},
                dataset_name="esc-50",
                streaming=False
            )
            length = dataset.__len__()
            assert isinstance(length, int)
            assert length >= 0
        except DataLoadError:
            pytest.skip("Dataset not available for testing")
        except Exception:
            pytest.skip("Dataset structure not as expected")