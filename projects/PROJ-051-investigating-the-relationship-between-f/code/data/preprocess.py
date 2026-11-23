"""
Streaming/Chunked Preprocessing for 512³ Turbulence Grids.

This module implements memory-constrained processing of large DNS datasets.
It reads velocity fields from HDF5 files in chunks, computes derived quantities
(vorticity, strain rate), and writes aggregated statistics to disk.
"""

import numpy as np
import h5py
from pathlib import Path
from typing import Generator, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import sys
import logging
import psutil
import gc

# Import from project API surface
from config import get_config
from utils.logging import get_logger

@dataclass
class ProcessingStats:
    """Aggregated statistics from the preprocessing run."""
    total_vorticity_magnitude: float = 0.0
    total_vorticity_squared: float = 0.0
    total_strain_magnitude: float = 0.0
    total_strain_squared: float = 0.0
    sample_count: int = 0
    max_vorticity: float = -np.inf
    min_vorticity: float = np.inf
    max_strain: float = -np.inf
    min_strain: float = np.inf
    mean_velocity_x: float = 0.0
    mean_velocity_y: float = 0.0
    mean_velocity_z: float = 0.0

    def update(self, vort_mag: float, vort_sq: float, strain_mag: float, 
               strain_sq: float, max_v: float, min_v: float, 
               max_s: float, min_s: float, n: int, 
               vel_x: float, vel_y: float, vel_z: float):
        """Update running statistics with chunk results."""
        self.total_vorticity_magnitude += vort_mag * n
        self.total_vorticity_squared += vort_sq * n
        self.total_strain_magnitude += strain_mag * n
        self.total_strain_squared += strain_sq * n
        self.max_vorticity = max(self.max_vorticity, max_v)
        self.min_vorticity = min(self.min_vorticity, min_v)
        self.max_strain = max(self.max_strain, max_s)
        self.min_strain = min(self.min_strain, min_s)
        self.sample_count += n
        
        # Update mean velocities (running average)
        if self.sample_count == n:
            self.mean_velocity_x = vel_x
            self.mean_velocity_y = vel_y
            self.mean_velocity_z = vel_z
        else:
            prev_n = self.sample_count - n
            self.mean_velocity_x = (self.mean_velocity_x * prev_n + vel_x * n) / self.sample_count
            self.mean_velocity_y = (self.mean_velocity_y * prev_n + vel_y * n) / self.sample_count
            self.mean_velocity_z = (self.mean_velocity_z * prev_n + vel_z * n) / self.sample_count

    def finalize(self) -> Dict[str, Any]:
        """Compute final averages and return as dictionary."""
        if self.sample_count == 0:
            return {"error": "No data processed"}
        
        return {
            "mean_vorticity_magnitude": self.total_vorticity_magnitude / self.sample_count,
            "std_vorticity_magnitude": np.sqrt(
                (self.total_vorticity_squared / self.sample_count) - 
                (self.total_vorticity_magnitude / self.sample_count)**2
            ) if self.sample_count > 1 else 0.0,
            "mean_strain_magnitude": self.total_strain_magnitude / self.sample_count,
            "std_strain_magnitude": np.sqrt(
                (self.total_strain_squared / self.sample_count) - 
                (self.total_strain_magnitude / self.sample_count)**2
            ) if self.sample_count > 1 else 0.0,
            "max_vorticity": self.max_vorticity,
            "min_vorticity": self.min_vorticity,
            "max_strain": self.max_strain,
            "min_strain": self.min_strain,
            "mean_velocity_x": self.mean_velocity_x,
            "mean_velocity_y": self.mean_velocity_y,
            "mean_velocity_z": self.mean_velocity_z,
            "total_samples": self.sample_count
        }


class ChunkedPreprocessor:
    """
    Processes large 512³ turbulence grids in chunks to enforce memory constraints.
    
    Reads velocity fields from HDF5 files, computes vorticity and strain rates,
    and aggregates statistics without loading the entire grid into memory.
    """
    
    def __init__(self, input_path: Path, output_path: Path, chunk_size: int = 64):
        """
        Initialize the preprocessor.
        
        Args:
            input_path: Path to the input HDF5 file containing velocity fields.
            output_path: Path to write the output statistics JSON.
            chunk_size: Size of the chunk to process along the first dimension.
        """
        self.input_path = input_path
        self.output_path = output_path
        self.chunk_size = chunk_size
        self.logger = get_logger("preprocess")
        self.config = get_config()
        
        # Memory limit from config (in GB)
        self.max_memory_gb = self.config.pipeline.max_memory_gb if hasattr(self.config, 'pipeline') else 6.0

    def _check_memory(self):
        """Check current memory usage and raise if exceeded."""
        process = psutil.Process()
        mem_mb = process.memory_info().rss / (1024 * 1024)
        mem_gb = mem_mb / 1024.0
        
        if mem_gb > self.max_memory_gb:
            raise MemoryError(
                f"Memory limit exceeded: {mem_gb:.2f} GB > {self.max_memory_gb} GB"
            )

    def _compute_vorticity(self, u: np.ndarray, v: np.ndarray, w: np.ndarray, 
                           dx: float, dy: float, dz: float) -> np.ndarray:
        """
        Compute vorticity magnitude from velocity components.
        
        Vorticity ω = ∇ × u
        ω_x = ∂w/∂y - ∂v/∂z
        ω_y = ∂u/∂z - ∂w/∂x
        ω_z = ∂v/∂x - ∂u/∂y
        """
        # Central differences with periodic boundary handling
        # Using np.gradient for simplicity, handles boundaries
        # Note: np.gradient assumes uniform spacing
        
        du_dx = np.gradient(u, dx, axis=0)
        du_dy = np.gradient(u, dy, axis=1)
        du_dz = np.gradient(u, dz, axis=2)
        
        dv_dx = np.gradient(v, dx, axis=0)
        dv_dy = np.gradient(v, dy, axis=1)
        dv_dz = np.gradient(v, dz, axis=2)
        
        dw_dx = np.gradient(w, dx, axis=0)
        dw_dy = np.gradient(w, dy, axis=1)
        dw_dz = np.gradient(w, dz, axis=2)
        
        omega_x = dw_dy - dv_dz
        omega_y = du_dz - dw_dx
        omega_z = dv_dx - du_dy
        
        vort_magnitude = np.sqrt(omega_x**2 + omega_y**2 + omega_z**2)
        return vort_magnitude

    def _compute_strain_rate(self, u: np.ndarray, v: np.ndarray, w: np.ndarray, 
                             dx: float, dy: float, dz: float) -> np.ndarray:
        """
        Compute strain rate magnitude S_ij S_ij.
        
        Strain rate tensor S_ij = 0.5 * (∂u_i/∂x_j + ∂u_j/∂x_i)
        Magnitude: sqrt(2 * S_ij * S_ij)
        """
        # Compute gradients
        du_dx = np.gradient(u, dx, axis=0)
        du_dy = np.gradient(u, dy, axis=1)
        du_dz = np.gradient(u, dz, axis=2)
        
        dv_dx = np.gradient(v, dx, axis=0)
        dv_dy = np.gradient(v, dy, axis=1)
        dv_dz = np.gradient(v, dz, axis=2)
        
        dw_dx = np.gradient(w, dx, axis=0)
        dw_dy = np.gradient(w, dy, axis=1)
        dw_dz = np.gradient(w, dz, axis=2)
        
        # Strain rate components
        S_xx = du_dx
        S_yy = dv_dy
        S_zz = dw_dz
        S_xy = 0.5 * (du_dy + dv_dx)
        S_xz = 0.5 * (du_dz + dw_dx)
        S_yz = 0.5 * (dv_dz + dw_dy)
        
        # S_ij * S_ij
        s_sq = (S_xx**2 + S_yy**2 + S_zz**2 + 
               2 * (S_xy**2 + S_xz**2 + S_yz**2))
        
        strain_magnitude = np.sqrt(2 * s_sq)
        return strain_magnitude

    def process(self) -> Dict[str, Any]:
        """
        Main processing loop. Reads data in chunks, computes statistics,
        and writes results to disk.
        
        Returns:
            Dictionary containing final processing statistics.
        """
        self.logger.info(f"Starting preprocessing of {self.input_path}")
        self.logger.info(f"Memory limit: {self.max_memory_gb} GB")
        
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_path}")
        
        stats = ProcessingStats()
        
        try:
            with h5py.File(self.input_path, 'r') as f:
                # Detect dataset structure
                # Expected keys: 'u', 'v', 'w' or 'velocity'
                if 'u' in f:
                    u_ds = f['u']
                    v_ds = f['v']
                    w_ds = f['w']
                elif 'velocity' in f:
                    vel_ds = f['velocity']
                    u_ds = vel_ds[..., 0]
                    v_ds = vel_ds[..., 1]
                    w_ds = vel_ds[..., 2]
                else:
                    raise ValueError(f"Unknown dataset structure in {self.input_path}")
                
                # Get dimensions and grid spacing
                # Assuming 512³ grid
                nx, ny, nz = u_ds.shape
                L = 2 * np.pi  # Typical domain size for turbulence
                dx = L / nx
                dy = L / ny
                dz = L / nz
                
                self.logger.info(f"Grid dimensions: {nx}x{ny}x{nz}")
                self.logger.info(f"Grid spacing: dx={dx:.6f}, dy={dy:.6f}, dz={dz:.6f}")
                
                # Process in chunks along the first dimension
                n_chunks = (nx + self.chunk_size - 1) // self.chunk_size
                self.logger.info(f"Processing in {n_chunks} chunks of size {self.chunk_size}")
                
                for i in range(n_chunks):
                    self._check_memory()
                    
                    start_idx = i * self.chunk_size
                    end_idx = min((i + 1) * self.chunk_size, nx)
                    chunk_size_actual = end_idx - start_idx
                    
                    # Read chunk
                    u_chunk = u_ds[start_idx:end_idx, :, :]
                    v_chunk = v_ds[start_idx:end_idx, :, :]
                    w_chunk = w_ds[start_idx:end_idx, :, :]
                    
                    # Compute statistics
                    vort_mag = self._compute_vorticity(u_chunk, v_chunk, w_chunk, dx, dy, dz)
                    strain_mag = self._compute_strain_rate(u_chunk, v_chunk, w_chunk, dx, dy, dz)
                    
                    # Aggregate stats
                    n_samples = vort_mag.size
                    vort_sum = np.sum(vort_mag)
                    vort_sq_sum = np.sum(vort_mag**2)
                    strain_sum = np.sum(strain_mag)
                    strain_sq_sum = np.sum(strain_mag**2)
                    
                    stats.update(
                        vort_sum, vort_sq_sum,
                        strain_sum, strain_sq_sum,
                        np.max(vort_mag), np.min(vort_mag),
                        np.max(strain_mag), np.min(strain_mag),
                        n_samples,
                        np.mean(u_chunk), np.mean(v_chunk), np.mean(w_chunk)
                    )
                    
                    # Free memory
                    del u_chunk, v_chunk, w_chunk, vort_mag, strain_mag
                    gc.collect()
                    
                    self.logger.info(f"Processed chunk {i+1}/{n_chunks} ({start_idx}:{end_idx})")
                    
        except MemoryError as e:
            self.logger.error(f"Memory error during processing: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error during processing: {e}")
            raise
        
        # Finalize and write results
        final_stats = stats.finalize()
        self.logger.info(f"Preprocessing complete. Total samples: {final_stats['total_samples']}")
        self.logger.info(f"Mean vorticity magnitude: {final_stats['mean_vorticity_magnitude']:.6f}")
        self.logger.info(f"Mean strain magnitude: {final_stats['mean_strain_magnitude']:.6f}")
        
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write results
        import json
        with open(self.output_path, 'w') as f:
            json.dump(final_stats, f, indent=2)
        
        self.logger.info(f"Results written to {self.output_path}")
        return final_stats


def main():
    """CLI entry point for preprocessing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocess turbulence data in chunks")
    parser.add_argument("--input", type=str, required=True, help="Input HDF5 file path")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file path")
    parser.add_argument("--chunk-size", type=int, default=64, help="Chunk size for processing")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    preprocessor = ChunkedPreprocessor(input_path, output_path, args.chunk_size)
    
    try:
        stats = preprocessor.process()
        print(json.dumps(stats, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()