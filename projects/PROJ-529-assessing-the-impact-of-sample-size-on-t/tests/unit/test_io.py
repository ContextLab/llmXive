"""
Unit tests for the chunked data processing framework (T006).
Tests memory safety and correct chunking behavior.
"""
import pytest
import pandas as pd
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from code.utils.io import ChunkedDataReader, process_large_dataset, validate_chunked_structure, get_file_metadata

class TestChunkedDataReader:
    """Tests for the ChunkedDataReader class."""

    def test_init_valid_file(self):
        """Test initialization with a valid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("a,b\n1,2\n")
            temp_path = f.name
        
        try:
            reader = ChunkedDataReader(temp_path)
            assert reader.filepath == Path(temp_path)
            assert reader.chunk_size == 10000
        finally:
            os.unlink(temp_path)

    def test_init_nonexistent_file(self):
        """Test initialization with a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            ChunkedDataReader("/nonexistent/path/file.csv")

    def test_init_invalid_chunk_size(self):
        """Test initialization with invalid chunk size raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("a,b\n1,2\n")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                ChunkedDataReader(temp_path, chunk_size=0)
        finally:
            os.unlink(temp_path)

    def test_read_csv_chunks(self):
        """Test reading CSV file in chunks."""
        # Create test data
        data = "id,value\n"
        for i in range(25):
            data += f"{i},{i*2}\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(data)
            temp_path = f.name
        
        try:
            reader = ChunkedDataReader(temp_path, chunk_size=10)
            chunks = list(reader.read_csv_chunks())
            
            assert len(chunks) == 3  # 25 rows / 10 = 3 chunks (10, 10, 5)
            assert len(chunks[0]) == 10
            assert len(chunks[1]) == 10
            assert len(chunks[2]) == 5
            
            # Check data integrity
            assert chunks[0].iloc[0]['id'] == 0
            assert chunks[0].iloc[0]['value'] == 0
            assert chunks[2].iloc[-1]['id'] == 24
        finally:
            os.unlink(temp_path)

    def test_read_csv_wrong_extension(self):
        """Test reading CSV method on non-CSV file raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("a,b\n1,2\n")
            temp_path = f.name
        
        try:
            reader = ChunkedDataReader(temp_path)
            with pytest.raises(ValueError):
                list(reader.read_csv_chunks())
        finally:
            os.unlink(temp_path)

    def test_read_jsonl_chunks(self):
        """Test reading JSONL file in chunks."""
        # Create test data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for i in range(25):
                f.write(json.dumps({"id": i, "value": i*2}) + "\n")
            temp_path = f.name
        
        try:
            reader = ChunkedDataReader(temp_path, chunk_size=10)
            chunks = list(reader.read_jsonl_chunks())
            
            assert len(chunks) == 3
            assert len(chunks[0]) == 10
            assert len(chunks[2]) == 5
            
            assert chunks[0][0]['id'] == 0
            assert chunks[2][-1]['id'] == 24
        finally:
            os.unlink(temp_path)

    def test_read_jsonl_malformed_line(self):
        """Test handling of malformed JSON lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": 1, "value": 2}\n')
            f.write('{"id": 2, "value": 4}\n')
            f.write('not valid json\n')
            f.write('{"id": 3, "value": 6}\n')
            temp_path = f.name
        
        try:
            reader = ChunkedDataReader(temp_path, chunk_size=10)
            chunks = list(reader.read_jsonl_chunks())
            
            # Should skip the malformed line and still get valid data
            assert len(chunks) == 1
            assert len(chunks[0]) == 3
        finally:
            os.unlink(temp_path)

class TestProcessLargeDataset:
    """Tests for the process_large_dataset function."""

    def test_process_csv(self):
        """Test processing a CSV file."""
        data = "id,value\n"
        for i in range(50):
            data += f"{i},{i}\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(data)
            temp_path = f.name
        
        output_path = temp_path + "_out.csv"
        
        try:
            def sum_processor(chunk):
                if isinstance(chunk, pd.DataFrame):
                    return chunk['value'].sum()
                return 0
            
            results = process_large_dataset(temp_path, sum_processor, chunk_size=10, output_filepath=output_path)
            
            assert len(results) == 5  # 5 chunks
            assert sum(results) == sum(range(50))
            
            # Check output file was created
            assert os.path.exists(output_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_process_jsonl(self):
        """Test processing a JSONL file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for i in range(30):
                f.write(json.dumps({"id": i, "value": i}) + "\n")
            temp_path = f.name
        
        output_path = temp_path + "_out.csv"
        
        try:
            def sum_processor(chunk):
                return sum(item['value'] for item in chunk)
            
            results = process_large_dataset(temp_path, sum_processor, chunk_size=10, output_filepath=output_path)
            
            assert len(results) == 3
            assert sum(results) == sum(range(30))
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_unsupported_extension(self):
        """Test that unsupported file extension raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("data")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                process_large_dataset(temp_path, lambda x: x)
        finally:
            os.unlink(temp_path)

class TestValidateChunkedStructure:
    """Tests for the validate_chunked_structure function."""

    def test_valid_csv(self):
        """Test validation of a valid CSV file."""
        data = "a,b,c\n1,2,3\n4,5,6\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(data)
            temp_path = f.name
        
        try:
            stats = validate_chunked_structure(temp_path)
            assert stats['valid'] is True
            assert stats['total_rows'] == 2
            assert 'a' in stats['columns']
        finally:
            os.unlink(temp_path)

    def test_malformed_jsonl(self):
        """Test validation of a JSONL file with errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"a": 1}\n')
            f.write('bad json\n')
            f.write('{"a": 2}\n')
            temp_path = f.name
        
        try:
            stats = validate_chunked_structure(temp_path)
            # Should be valid because malformed lines are skipped
            assert stats['total_rows'] == 2
        finally:
            os.unlink(temp_path)

class TestGetFileMetadata:
    """Tests for the get_file_metadata function."""

    def test_file_exists(self):
        """Test metadata retrieval for existing file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("data")
            temp_path = f.name
        
        try:
            meta = get_file_metadata(temp_path)
            assert meta['exists'] is True
            assert meta['size_bytes'] > 0
            assert meta['extension'] == '.csv'
        finally:
            os.unlink(temp_path)

    def test_file_not_exists(self):
        """Test metadata retrieval for nonexistent file."""
        meta = get_file_metadata("/nonexistent/file.csv")
        assert meta['exists'] is False
        assert 'error' in meta
