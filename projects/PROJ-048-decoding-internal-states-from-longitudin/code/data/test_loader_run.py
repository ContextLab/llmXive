"""
Script to test the chunked loader with real data generation.
This creates a sample HDF5 file and demonstrates the loader functionality.
"""

import os
import sys
import numpy as np
import h5py
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.loader import ChunkedDataLoader, load_calldata_chunked, load_calldata_metadata
from code.utils.memory_monitor import get_memory_limit_gb, get_current_memory_usage_gb
from code.utils.logger import get_logger, log_stage_start, log_stage_end, log_memory_usage

logger = get_logger(__name__)

def create_sample_data(output_path: str, num_frames: int = 5000, num_rois: int = 200):
    """Create sample calcium imaging data for testing."""
    logger.info(f"Creating sample data: {num_frames} frames, {num_rois} ROIs")
    
    # Generate realistic-looking calcium traces
    # Base signal with some noise
    base_signal = np.random.randn(num_frames, num_rois) * 0.1
    
    # Add some spike-like events
    for roi in range(num_rois):
        num_spikes = np.random.randint(5, 20)
        spike_times = np.random.choice(num_frames, num_spikes, replace=False)
        for t in spike_times:
            # Exponential decay for spike
            decay = np.exp(-np.arange(10) / 3)
            end_idx = min(t + 10, num_frames)
            base_signal[t:end_idx, roi] += decay[:end_idx-t] * 2.0
    
    # Add baseline drift
    drift = np.linspace(0, 0.5, num_frames).reshape(-1, 1)
    base_signal += drift
    
    # Normalize to typical dF/F range
    base_signal = (base_signal - base_signal.mean(axis=0)) / base_signal.std(axis=0)
    
    # Create HDF5 file
    with h5py.File(output_path, 'w') as f:
        f.create_dataset('data', data=base_signal.astype(np.float32))
        f['data'].attrs['experiment_id'] = 'test_experiment'
        f['data'].attrs['num_rois'] = num_rois
        f['data'].attrs['num_frames'] = num_frames
        f['data'].attrs['sampling_rate_hz'] = 30.0
        f['data'].attrs['created_by'] = 'test_loader_run.py'
    
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"Created sample file: {output_path} ({file_size_mb:.2f} MB)")
    
    return output_path

def test_loader(file_path: str):
    """Test the chunked loader with the generated file."""
    logger.info(f"Testing loader with: {file_path}")
    
    # Get metadata
    logger.info("Getting metadata...")
    metadata = load_calldata_metadata(file_path)
    logger.info(f"Metadata: {metadata}")
    
    # Test chunked loading
    logger.info("Testing chunked iteration...")
    chunk_count = 0
    total_rows = 0
    chunk_sizes = []
    
    with ChunkedDataLoader(file_path, chunk_size=500) as loader:
        for i, chunk in enumerate(loader.iter_chunks()):
            chunk_count += 1
            total_rows += len(chunk)
            chunk_sizes.append(len(chunk))
            
            if i < 3 or i % 10 == 0:
                logger.info(f"Chunk {i+1}: shape={chunk.shape}, dtype={chunk.dtype}")
            
            # Log memory usage every 10 chunks
            if i % 10 == 0:
                current_mem = get_current_memory_usage_gb()
                logger.info(f"Memory usage after chunk {i+1}: {current_mem:.3f} GB")
    
    logger.info(f"Successfully processed {total_rows} rows in {chunk_count} chunks")
    logger.info(f"Chunk sizes: {chunk_sizes}")
    logger.info(f"Average chunk size: {np.mean(chunk_sizes):.1f}")
    
    # Verify all data was loaded
    assert total_rows == metadata['total_rows'], f"Row count mismatch: {total_rows} != {metadata['total_rows']}"
    logger.info("✓ All rows loaded correctly")
    
    # Test specific row loading
    logger.info("Testing specific row loading...")
    with ChunkedDataLoader(file_path) as loader:
        sample_rows = loader.load_specific_rows(slice(0, 10))
        assert sample_rows.shape == (10, metadata['dataset_shape'][1])
        logger.info(f"✓ Loaded 10 specific rows: shape={sample_rows.shape}")
    
    return True

def main():
    """Main entry point."""
    log_stage_start("loader_test", {})
    
    try:
        # Create sample data in temp directory
        temp_dir = tempfile.mkdtemp()
        sample_file = os.path.join(temp_dir, "sample_calcium_data.h5")
        
        # Create sample data (adjust size based on available memory)
        create_sample_data(sample_file, num_frames=5000, num_rois=200)
        
        # Test the loader
        success = test_loader(sample_file)
        
        if success:
            logger.info("✓ All loader tests passed!")
        else:
            logger.error("✗ Loader tests failed")
            sys.exit(1)
        
    except Exception as e:
        log_error("loader_test", str(e))
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)
    finally:
        log_stage_end("loader_test", {})

if __name__ == "__main__":
    main()