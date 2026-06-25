"""
Unit tests for data_loader module.

Tests verify:
- Streaming mode is enabled
- Output file is created at correct path
- CSV format is valid
- Error handling for missing content fields
"""

import csv
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

# Import module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'projects' / 'PROJ-261-evaluating-the-impact-of-code-duplication' / 'code'))

from data_loader import stream_code_dataset, save_streamed_data


class TestStreamCodeDataset:
    """Tests for stream_code_dataset function."""

    @patch('data_loader.load_dataset')
    def test_streaming_enabled(self, mock_load_dataset):
        """Verify streaming=True is passed to load_dataset."""
        # Setup mock
        mock_dataset = MagicMock()
        mock_dataset.__getitem__ = MagicMock(return_value=iter([
            {'content': 'def hello(): pass', 'language': 'python', 'path': 'test.py'}
        ]))
        mock_dataset.__contains__ = MagicMock(return_value=True)
        mock_dataset.keys = MagicMock(return_value=['train'])
        mock_load_dataset.return_value = mock_dataset

        # Call function
        samples = list(stream_code_dataset(
            dataset_name="codeparrot/github-code",
            streaming=True
        ))

        # Verify streaming=True was passed
        mock_load_dataset.assert_called_once()
        call_kwargs = mock_load_dataset.call_args
        assert call_kwargs.kwargs.get('streaming') is True

    @patch('data_loader.load_dataset')
    def test_yields_valid_samples(self, mock_load_dataset):
        """Verify function yields samples with content field."""
        # Setup mock
        mock_dataset = MagicMock()
        mock_dataset.__getitem__ = MagicMock(return_value=iter([
            {'content': 'def a(): pass', 'language': 'python', 'path': 'a.py'},
            {'content': 'def b(): pass', 'language': 'python', 'path': 'b.py'}
        ]))
        mock_dataset.__contains__ = MagicMock(return_value=True)
        mock_dataset.keys = MagicMock(return_value=['train'])
        mock_load_dataset.return_value = mock_dataset

        # Call function
        samples = list(stream_code_dataset(
            dataset_name="codeparrot/github-code",
            streaming=True
        ))

        # Verify samples yielded
        assert len(samples) == 2
        assert all('content' in s for s in samples)
        assert all(s['content'] for s in samples)

    @patch('data_loader.load_dataset')
    def test_respects_max_samples(self, mock_load_dataset):
        """Verify max_samples parameter limits output."""
        # Setup mock
        mock_dataset = MagicMock()
        mock_dataset.__getitem__ = MagicMock(return_value=iter([
            {'content': f'def {i}(): pass', 'language': 'python', 'path': f'{i}.py'}
            for i in range(10)
        ]))
        mock_dataset.__contains__ = MagicMock(return_value=True)
        mock_dataset.keys = MagicMock(return_value=['train'])
        mock_load_dataset.return_value = mock_dataset

        # Call with max_samples=3
        samples = list(stream_code_dataset(
            dataset_name="codeparrot/github-code",
            streaming=True,
            max_samples=3
        ))

        # Verify only 3 samples returned
        assert len(samples) == 3

    @patch('data_loader.load_dataset')
    def test_skips_samples_without_content(self, mock_load_dataset):
        """Verify samples missing content field are skipped."""
        # Setup mock
        mock_dataset = MagicMock()
        mock_dataset.__getitem__ = MagicMock(return_value=iter([
            {'content': 'valid code', 'path': 'valid.py'},
            {'path': 'invalid.py'},  # Missing content
            {'content': 'more valid', 'path': 'valid2.py'}
        ]))
        mock_dataset.__contains__ = MagicMock(return_value=True)
        mock_dataset.keys = MagicMock(return_value=['train'])
        mock_load_dataset.return_value = mock_dataset

        # Call function
        samples = list(stream_code_dataset(
            dataset_name="codeparrot/github-code",
            streaming=True
        ))

        # Verify only valid samples returned
        assert len(samples) == 2
        assert all('content' in s for s in samples)


class TestSaveStreamedData:
    """Tests for save_streamed_data function."""

    def test_streaming_must_be_true(self):
        """Verify streaming=False raises RuntimeError per T018 requirements."""
        with pytest.raises(RuntimeError, match="streaming must be True"):
            save_streamed_data(
                output_path="/tmp/test.csv",
                streaming=False
            )

    @patch('data_loader.stream_code_dataset')
    def test_creates_output_directory(self, mock_stream):
        """Verify output directory is created if it doesn't exist."""
        mock_stream.return_value = iter([
            {'content': 'test code', 'language': 'python'}
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "subdir", "output.csv")

            # Should not raise - creates directory
            sample_count = save_streamed_data(
                output_path=output_path,
                streaming=True,
                max_samples=1
            )

            # Verify file was created
            assert os.path.exists(output_path)
            assert sample_count == 1

    @patch('data_loader.stream_code_dataset')
    def test_writes_valid_csv(self, mock_stream):
        """Verify output is valid CSV format."""
        mock_stream.return_value = iter([
            {'content': 'def test(): pass', 'language': 'python', 'path': 'test.py'},
            {'content': 'def foo(): return 1', 'language': 'python', 'path': 'foo.py'}
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.csv")

            save_streamed_data(
                output_path=output_path,
                streaming=True,
                max_samples=2
            )

            # Verify CSV is valid and readable
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert 'content' in rows[0]
            assert rows[0]['content'] == 'def test(): pass'

    @patch('data_loader.stream_code_dataset')
    def test_respects_max_bytes(self, mock_stream):
        """Verify max_bytes parameter limits total output size."""
        # Create samples with known sizes
        small_content = 'x = 1'
        mock_stream.return_value = iter([
            {'content': small_content, 'path': f'{i}.py'}
            for i in range(100)
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.csv")

            # Set max_bytes to allow only a few samples
            sample_count = save_streamed_data(
                output_path=output_path,
                streaming=True,
                max_bytes=100  # Very small limit
            )

            # Verify some samples were written (but not all)
            assert 0 < sample_count < 100

    @patch('data_loader.stream_code_dataset')
    def test_deletes_partial_file_on_error(self, mock_stream):
        """Verify partial output file is deleted on error."""
        def failing_stream(*args, **kwargs):
            yield {'content': 'test', 'path': 'test.py'}
            raise RuntimeError("Simulated network error")

        mock_stream.side_effect = failing_stream

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.csv")

            with pytest.raises(RuntimeError, match="Simulated network error"):
                save_streamed_data(
                    output_path=output_path,
                    streaming=True
                )

            # Verify file was deleted
            assert not os.path.exists(output_path)
