"""
Contract test for embedding output schema.

This test verifies that the embedding extraction module produces output
that conforms to the expected schema defined in the project specifications.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data.embed import process_dataset, load_model_and_processor

class TestEmbeddingSchema:
    """Tests for the embedding output schema contract."""

    def test_output_file_exists(self):
        """Test that the output file is created."""
        # This is a basic check; the actual content validation is in other tests
        # We'll create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            output_file = os.path.join(temp_dir, "output.parquet")
            os.makedirs(input_dir)

            # Create a minimal metadata file
            metadata = [
                {"file_id": "test_001", "audio_path": "test_audio.wav"}
            ]
            with open(os.path.join(input_dir, "metadata.json"), 'w') as f:
                json.dump(metadata, f)

            # Create a dummy audio file (1 second of silence)
            try:
                import soundfile as sf
                import numpy as np
                dummy_audio = np.zeros(16000, dtype=np.float32)
                sf.write(os.path.join(input_dir, "test_audio.wav"), dummy_audio, 16000)
            except ImportError:
                pytest.skip("soundfile not installed")

            # Run the extraction
            try:
                process_dataset(input_dir, output_file)
                assert os.path.exists(output_file), "Output file was not created"
            except Exception as e:
                # If model loading fails (e.g., no internet), skip the test
                if "model" in str(e).lower() or "transformers" in str(e).lower():
                    pytest.skip("Model loading failed (likely network issue)")
                else:
                    raise

    def test_output_schema_columns(self):
        """Test that the output file has the required columns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            output_file = os.path.join(temp_dir, "output.parquet")
            os.makedirs(input_dir)

            # Create a minimal metadata file
            metadata = [
                {"file_id": "test_001", "audio_path": "test_audio.wav"}
            ]
            with open(os.path.join(input_dir, "metadata.json"), 'w') as f:
                json.dump(metadata, f)

            # Create a dummy audio file
            try:
                import soundfile as sf
                import numpy as np
                dummy_audio = np.zeros(16000, dtype=np.float32)
                sf.write(os.path.join(input_dir, "test_audio.wav"), dummy_audio, 16000)
            except ImportError:
                pytest.skip("soundfile not installed")

            # Run the extraction
            try:
                process_dataset(input_dir, output_file)
            except Exception as e:
                if "model" in str(e).lower() or "transformers" in str(e).lower():
                    pytest.skip("Model loading failed (likely network issue)")
                else:
                    raise

            # Load and check schema
            df = pd.read_parquet(output_file)
            required_columns = {"file_id", "embedding"}
            assert required_columns.issubset(df.columns), f"Missing columns: {required_columns - set(df.columns)}"

    def test_embedding_dimension(self):
        """Test that embeddings have the expected dimension."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            output_file = os.path.join(temp_dir, "output.parquet")
            os.makedirs(input_dir)

            # Create a minimal metadata file
            metadata = [
                {"file_id": "test_001", "audio_path": "test_audio.wav"}
            ]
            with open(os.path.join(input_dir, "metadata.json"), 'w') as f:
                json.dump(metadata, f)

            # Create a dummy audio file
            try:
                import soundfile as sf
                import numpy as np
                dummy_audio = np.zeros(16000, dtype=np.float32)
                sf.write(os.path.join(input_dir, "test_audio.wav"), dummy_audio, 16000)
            except ImportError:
                pytest.skip("soundfile not installed")

            # Run the extraction
            try:
                process_dataset(input_dir, output_file)
            except Exception as e:
                if "model" in str(e).lower() or "transformers" in str(e).lower():
                    pytest.skip("Model loading failed (likely network issue)")
                else:
                    raise

            # Load and check embedding dimension
            df = pd.read_parquet(output_file)
            embedding = df.iloc[0]["embedding"]
            # DistilWhisper hidden state dimension is 1024
            expected_dim = 1024
            assert len(embedding) == expected_dim, f"Expected embedding dimension {expected_dim}, got {len(embedding)}"

    def test_embedding_type(self):
        """Test that embeddings are numeric arrays."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            output_file = os.path.join(temp_dir, "output.parquet")
            os.makedirs(input_dir)

            # Create a minimal metadata file
            metadata = [
                {"file_id": "test_001", "audio_path": "test_audio.wav"}
            ]
            with open(os.path.join(input_dir, "metadata.json"), 'w') as f:
                json.dump(metadata, f)

            # Create a dummy audio file
            try:
                import soundfile as sf
                import numpy as np
                dummy_audio = np.zeros(16000, dtype=np.float32)
                sf.write(os.path.join(input_dir, "test_audio.wav"), dummy_audio, 16000)
            except ImportError:
                pytest.skip("soundfile not installed")

            # Run the extraction
            try:
                process_dataset(input_dir, output_file)
            except Exception as e:
                if "model" in str(e).lower() or "transformers" in str(e).lower():
                    pytest.skip("Model loading failed (likely network issue)")
                else:
                    raise

            # Load and check embedding type
            df = pd.read_parquet(output_file)
            embedding = df.iloc[0]["embedding"]
            assert isinstance(embedding, (list, np.ndarray)), "Embedding should be a list or numpy array"
            assert all(isinstance(x, (int, float, np.floating)) for x in embedding), "Embedding elements should be numeric"
