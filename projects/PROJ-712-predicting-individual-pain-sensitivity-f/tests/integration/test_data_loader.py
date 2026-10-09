"""
Integration test for the EEGDataLoader and DataChunk implementation.
Ensures that streaming large binary EEG files via memory‑mapped chunks
does not cause the process to exceed the 6 GB RAM limit.
"""

import os
import tempfile

import numpy as np
import psutil
import pytest

from data_loader import EEGDataLoader


@pytest.mark.skipif(
    not hasattr(psutil, "Process"),
    reason="psutil is required for memory usage measurement"
)
def test_iterate_chunks_memory_usage(tmp_path: pathlib.Path):
    """
    Create a synthetic binary EEG file and stream it in chunks.
    Verify that the maximum resident set size (RSS) stays below 6 GB.
    """
    # Parameters for the synthetic file
    n_channels = 64
    n_samples = 200_000          # ~51 MiB for float32 data
    chunk_size = 50_000          # Samples per yielded chunk
    
    # Generate deterministic random data
    rng = np.random.default_rng(seed=42)
    data = rng.random((n_channels, n_samples), dtype=np.float32)
    
    # Write raw binary file (channel‑wise layout)
    bin_file = tmp_path / "synthetic_eeg.bin"
    data.tofile(str(bin_file))

    # Initialise loader pointing at the temporary directory
    loader = EEGDataLoader(tmp_path)

    # Process chunks and monitor memory usage
    proc = psutil.Process()
    max_rss = 0
    for chunk in loader.iterate_chunks(
        filename=bin_file.name,
        chunk_size_samples=chunk_size,
        n_channels=n_channels,
        dtype=np.float32,
    ):
        # Force materialisation of the memmap slice
        arr = chunk.get_data()
        _ = arr.sum()  # simple operation to ensure the data is accessed
        
        # Record current RSS
        current_rss = proc.memory_info().rss
        max_rss = max(max_rss, current_rss)
        
        # Clean up the chunk to release the memmap reference
        chunk.close()

    # 6 GB expressed in bytes
    six_gb = 6 * 1024 ** 3
    assert max_rss < six_gb, (
        f"Memory usage exceeded 6 GB limit: {max_rss / (1024 ** 3):.2f} GB"
    )