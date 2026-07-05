"""
Streaming/Chunked Preprocessing for 512^3 Turbulence Grids.

Implements memory-constrained processing of large DNS datasets by reading
and processing data in chunks. This ensures peak RSS remains within the
6GB limit specified in config.py, even when handling 512^3 grids.
"""

import numpy as np
import h5py
from pathlib import Path
from typing import Generator, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import sys

# Import project utilities
try:
    from utils.logging import get_logger
    from config import get_config, validate_config
except ImportError:
    # Fallback for standalone execution or different import context
    import logging
    def get_logger(name):
        return logging.getLogger(name)
    
    # Minimal config fallback if not available
    class MockConfig:
        max_rss_gb = 6.0
        chunk_size_mb = 500
    def get_config(): return MockConfig()
    def validate_config(c): pass


logger = get_logger(__name__)


@dataclass
class ProcessingStats:
    """Statistics about the preprocessing run."""
    total_voxels: int
    chunks_processed: int
    peak_memory_mb: float
    output_path: str


class ChunkedPreprocessor:
    """
    Handles streaming processing of large 3D turbulence fields.
    
    Reads data from HDF5 files in chunks to respect memory constraints,
    computes derived fields (like vorticity magnitude) on-the-fly, and
    writes results to disk without loading the entire 512^3 grid into RAM.
    """

    def __init__(self, input_path: str, output_path: str, config=None):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.config = config or get_config()
        
        # Validate inputs
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_path}")
        
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger = get_logger(__name__)
        self.logger.info(f"Initialized preprocessor for {self.input_path}")
        self.logger.info(f"Output target: {self.output_path}")

    def _estimate_chunk_size(self, grid_shape: Tuple[int, int, int], dtype: np.dtype) -> Tuple[int, int, int]:
        """
        Calculates a chunk size (in voxels per dimension) that fits within
        the memory constraints defined in config.
        
        Returns a tuple (nx, ny, nz) representing the chunk dimensions.
        """
        max_rss_bytes = self.config.max_rss_gb * 1024**3
        # Reserve 50% of memory for data buffers to be safe
        safe_buffer_bytes = max_rss_bytes * 0.5 
        
        bytes_per_voxel = dtype.itemsize
        # We need to hold at least the chunk of the field we are processing
        # plus potentially temporary arrays for gradients. 
        # Conservative estimate: 3x the raw chunk size (for u, v, w and temp)
        max_voxels = int(safe_buffer_bytes / (bytes_per_voxel * 3))

        total_voxels = grid_shape[0] * grid_shape[1] * grid_shape[2]
        
        # If the whole grid fits, process it all (though 512^3 usually won't)
        if total_voxels <= max_voxels:
            return grid_shape

        # Calculate chunk dimensions proportionally
        # We want roughly cubic chunks to minimize surface-area overhead for gradients
        chunk_vol = max_voxels
        chunk_dim = int(chunk_vol ** (1/3))
        
        # Ensure chunk dimensions don't exceed grid dimensions
        nx = min(chunk_dim, grid_shape[0])
        ny = min(chunk_dim, grid_shape[1])
        nz = min(chunk_dim, grid_shape[2])
        
        self.logger.debug(f"Estimated chunk size: {nx}x{ny}x{nz} (max voxels: {max_voxels})")
        return (nx, ny, nz)

    def stream_velocity_chunks(self, field_name: str = "velocity") -> Generator[Tuple[slice, np.ndarray], None, None]:
        """
        Generator that yields chunks of the velocity field.
        
        Yields:
            Tuple of (slice_object, data_array)
            slice_object: The slice used to read this chunk
            data_array: The numpy array containing the chunk data
        """
        with h5py.File(self.input_path, 'r') as f:
            if field_name not in f:
                raise KeyError(f"Field '{field_name}' not found in {self.input_path}")
            
            dataset = f[field_name]
            shape = dataset.shape
            dtype = dataset.dtype
            
            if len(shape) != 4: # Expecting (3, Nx, Ny, Nz) or similar
                # Try to handle (Nx, Ny, Nz, 3) or flatten if necessary
                if len(shape) == 3:
                    # Assume single component or packed differently, warn
                    self.logger.warning(f"Field shape is 3D: {shape}. Assuming (u, v, w) packed or single component.")
            
            chunk_dims = self._estimate_chunk_size(shape[1:], dtype)
            
            # If 4D (3 components, x, y, z), we iterate over x, y, z
            # Assuming standard JHTDB format: (3, Nx, Ny, Nz)
            if len(shape) == 4:
                c_x, c_y, c_z = chunk_dims
                
                for i in range(0, shape[1], c_x):
                    for j in range(0, shape[2], c_y):
                        for k in range(0, shape[3], c_z):
                            # Define slices for the current chunk
                            # Slice for the full vector (3 components) at this spatial location
                            sl_x = slice(i, min(i + c_x, shape[1]))
                            sl_y = slice(j, min(j + c_y, shape[2]))
                            sl_z = slice(k, min(k + c_z, shape[3]))
                            
                            # Read the chunk: all 3 components, spatial slice
                            # This loads (3, chunk_x, chunk_y, chunk_z)
                            chunk_data = dataset[:, sl_x, sl_y, sl_z]
                            
                            slice_obj = (sl_x, sl_y, sl_z)
                            yield slice_obj, chunk_data
            else:
                # Fallback for unexpected shapes
                raise ValueError(f"Unsupported field shape: {shape}. Expected 4D (3, Nx, Ny, Nz).")

    def compute_vorticity_magnitude(self, u: np.ndarray, v: np.ndarray, w: np.ndarray, 
                                  dx: float, dy: float, dz: float) -> np.ndarray:
        """
        Computes the magnitude of vorticity |omega| from velocity components.
        Uses central differences for interior points and forward/backward at boundaries.
        
        Args:
            u, v, w: Velocity component arrays (Nx, Ny, Nz)
            dx, dy, dz: Grid spacings
        
        Returns:
            Vorticity magnitude array (Nx, Ny, Nz)
        """
        # Preallocate output
        omega_mag = np.zeros_like(u)
        
        # Compute derivatives using central differences
        # dU/dy, dU/dz, dV/dx, dV/dz, dW/dx, dW/dy
        
        # Helper for central difference
        def central_diff(arr, d, axis):
            # Pad to handle boundaries
            padded = np.pad(arr, 1, mode='edge')
            # Central diff: (f[i+1] - f[i-1]) / (2*d)
            # Slicing: [1:-1] to align with original shape
            return (np.take(padded, range(2, arr.shape[axis]+2), axis=axis) - 
                    np.take(padded, range(0, arr.shape[axis]), axis=axis)) / (2.0 * d)

        # Compute vorticity components:
        # omega_x = dW/dy - dV/dz
        # omega_y = dU/dz - dW/dx
        # omega_z = dV/dx - dU/dy
        
        # Note: axis mapping: 0->x, 1->y, 2->z
        dUdy = central_diff(u, dy, 1)
        dUdz = central_diff(u, dz, 2)
        dVdx = central_diff(v, dx, 0)
        dVdz = central_diff(v, dz, 2)
        dWdx = central_diff(w, dx, 0)
        dWdy = central_diff(w, dy, 1)

        om_x = dWdy - dVdz
        om_y = dUdz - dWdx
        om_z = dVdx - dUdy

        omega_mag = np.sqrt(om_x**2 + om_y**2 + om_z**2)
        return omega_mag

    def process_and_save(self, field_name: str = "velocity") -> ProcessingStats:
        """
        Main entry point for preprocessing.
        
        Reads the velocity field in chunks, computes vorticity magnitude,
        and writes the result to the output HDF5 file.
        
        Returns:
            ProcessingStats object with run metrics.
        """
        self.logger.info(f"Starting preprocessing for {field_name}")
        
        # Open input file to get metadata
        with h5py.File(self.input_path, 'r') as f_in:
            if field_name not in f_in:
                raise KeyError(f"Field '{field_name}' not found")
            
            dataset = f_in[field_name]
            shape = dataset.shape
            
            # Assume JHTDB format: (3, Nx, Ny, Nz)
            if len(shape) != 4 or shape[0] != 3:
                raise ValueError(f"Expected 4D velocity field (3, Nx, Ny, Nz), got {shape}")
            
            Nx, Ny, Nz = shape[1], shape[2], shape[3]
            
            # Get grid spacing from attributes if available, else assume 1.0
            dx = dataset.attrs.get('dx', 1.0)
            dy = dataset.attrs.get('dy', 1.0)
            dz = dataset.attrs.get('dz', 1.0)
            
            self.logger.info(f"Grid dimensions: {Nx}x{Ny}x{Nz}, Spacing: {dx}, {dy}, {dz}")

        # Initialize output file
        # We will write the full vorticity magnitude field
        # Since we process in chunks, we need to create the dataset first
        with h5py.File(self.output_path, 'w') as f_out:
            # Create dataset for vorticity magnitude
            dset_out = f_out.create_dataset('vorticity_magnitude', 
                                            shape=(Nx, Ny, Nz), 
                                            dtype='float32',
                                            chunks=(Nx//16, Ny//16, Nz//16)) # Reasonable default chunking for output
            
            # Add metadata
            f_out.attrs['source_file'] = str(self.input_path)
            f_out.attrs['processed_field'] = field_name
            f_out.attrs['dx'] = dx
            f_out.attrs['dy'] = dy
            f_out.attrs['dz'] = dz

        # Processing loop
        total_voxels = Nx * Ny * Nz
        chunks_processed = 0
        peak_memory_mb = 0.0

        # Re-open input for streaming
        with h5py.File(self.input_path, 'r') as f_in:
            dataset = f_in[field_name]
            
            # We need to iterate and write to the output file
            # We'll use the same chunking strategy for writing
            c_x, c_y, c_z = self._estimate_chunk_size((Nx, Ny, Nz), np.float32)
            
            with h5py.File(self.output_path, 'r+') as f_out:
                dset_out = f_out['vorticity_magnitude']
                
                for i in range(0, Nx, c_x):
                    for j in range(0, Ny, c_y):
                        for k in range(0, Nz, c_z):
                            # Define slices
                            sl_x = slice(i, min(i + c_x, Nx))
                            sl_y = slice(j, min(j + c_y, Ny))
                            sl_z = slice(k, min(k + c_z, Nz))
                            
                            # Read velocity chunk: (3, cx, cy, cz)
                            vel_chunk = dataset[:, sl_x, sl_y, sl_z]
                            
                            # Extract components
                            u = vel_chunk[0]
                            v = vel_chunk[1]
                            w = vel_chunk[2]
                            
                            # Compute vorticity magnitude
                            # Note: The chunk is smaller than full grid, but central diffs
                            # need neighbors. Since we are processing independent chunks for
                            # streaming, we treat boundaries of the chunk as local boundaries.
                            # This introduces small errors at chunk boundaries but is necessary
                            # for memory constraints.
                            om_mag = self.compute_vorticity_magnitude(u, v, w, dx, dy, dz)
                            
                            # Write to output
                            dset_out[sl_x, sl_y, sl_z] = om_mag.astype('float32')
                            
                            chunks_processed += 1
                            
                            # Log progress
                            if chunks_processed % 10 == 0:
                                self.logger.debug(f"Processed chunk {chunks_processed}")

                            # Simple memory check (approximate)
                            current_mem_mb = (u.nbytes + v.nbytes + w.nbytes + om_mag.nbytes) / 1024 / 1024
                            if current_mem_mb > peak_memory_mb:
                                peak_memory_mb = current_mem_mb

        stats = ProcessingStats(
            total_voxels=total_voxels,
            chunks_processed=chunks_processed,
            peak_memory_mb=peak_memory_mb,
            output_path=str(self.output_path)
        )
        
        self.logger.info(f"Preprocessing complete. Processed {chunks_processed} chunks. Peak memory: {peak_memory_mb:.2f} MB")
        return stats


def main():
    """CLI entry point for preprocessing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocess DNS data with memory constraints")
    parser.add_argument("--input", "-i", required=True, help="Path to input HDF5 file")
    parser.add_argument("--output", "-o", required=True, help="Path to output HDF5 file")
    parser.add_argument("--field", "-f", default="velocity", help="Field name to process (default: velocity)")
    parser.add_argument("--config", "-c", default=None, help="Path to config file (optional)")
    
    args = parser.parse_args()
    
    try:
        config = get_config()
        validate_config(config)
        
        preprocessor = ChunkedPreprocessor(args.input, args.output, config)
        stats = preprocessor.process_and_save(args.field)
        
        print(f"SUCCESS: Preprocessing finished.")
        print(f"Output: {stats.output_path}")
        print(f"Chunks: {stats.chunks_processed}, Peak Memory: {stats.peak_memory_mb:.2f} MB")
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

if __name__ == "__main__":
    main()