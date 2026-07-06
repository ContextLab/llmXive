"""
Integration test for reproducibility: verify std dev of crossover SNR < 0.5 across 10 runs.

This test runs the full inference pipeline 10 times with different seeds and computes
the standard deviation of identified crossover points where quantization error exceeds
10% of instrumental error.
"""
import os
import sys
import tempfile
import shutil
import json
import logging
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import set_seed, get_seed
from src.data_generation import generate_dataset
from src.inference_engine import run_batch_inference
from src.analysis import compute_mse_metrics, load_inference_results


logger = logging.getLogger(__name__)


class TestReproducibility(unittest.TestCase):
    """Test reproducibility of crossover SNR identification across multiple runs."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.temp_dir = tempfile.mkdtemp(prefix="test_reproducibility_")
        cls.data_dir = Path(cls.temp_dir) / "data"
        cls.results_dir = Path(cls.temp_dir) / "results"
        cls.data_dir.mkdir(parents=True, exist_ok=True)
        cls.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    def test_crossover_snr_reproducibility(self):
        """
        Verify that the crossover SNR (where quantization error > 10% instrumental error)
        has std dev < 0.5 across 10 independent runs with different seeds.
        
        This is an integration test that:
        1. Runs 10 independent iterations
        2. Each iteration:
           - Generates a small pilot dataset with a unique seed
           - Runs Bayesian inference on quantized signals
           - Computes MSE metrics and identifies crossover point
        3. Collects crossover SNR values from all runs
        4. Verifies std dev < 0.5
        """
        num_runs = 10
        crossover_snrs = []
        
        logger.info(f"Starting reproducibility test with {num_runs} runs...")
        
        for run_idx in range(num_runs):
            run_seed = 1000 + run_idx  # Different seed for each run
            logger.info(f"\n=== Run {run_idx + 1}/{num_runs} (seed={run_seed}) ===")
            
            # Set seed for reproducibility within this run
            set_seed(run_seed)
            
            # Create run-specific directories
            run_data_dir = self.data_dir / f"run_{run_idx}"
            run_results_dir = self.results_dir / f"run_{run_idx}"
            run_data_dir.mkdir(parents=True, exist_ok=True)
            run_results_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Generate pilot dataset
                logger.info(f"Generating pilot dataset for run {run_idx + 1}...")
                dataset_path = run_data_dir / f"waveforms_pilot_{run_seed}.h5"
                
                generate_dataset(
                    output_path=str(dataset_path),
                    num_signals_per_bin=5,  # Small pilot: 5 signals per bin
                    bit_depths=[8, 12, 16],  # Subset of bit depths
                    snr_bins=[(8, 14), (14, 20), (20, 30), (30, 50)],
                    seed=run_seed
                )
                
                self.assertTrue(
                    dataset_path.exists(),
                    f"Dataset not created at {dataset_path}"
                )
                logger.info(f"Dataset created: {dataset_path}")
                
                # Run inference
                logger.info(f"Running inference for run {run_idx + 1}...")
                inference_path = run_results_dir / f"inference_pilot_{run_seed}.json"
                
                run_batch_inference(
                    dataset_path=str(dataset_path),
                    output_path=str(inference_path),
                    num_processes=1,
                    seed=run_seed
                )
                
                self.assertTrue(
                    inference_path.exists(),
                    f"Inference results not created at {inference_path}"
                )
                logger.info(f"Inference completed: {inference_path}")
                
                # Compute MSE metrics
                logger.info(f"Computing MSE metrics for run {run_idx + 1}...")
                mse_path = run_results_dir / f"mse_metrics_{run_seed}.json"
                
                compute_mse_metrics(
                    inference_results_path=str(inference_path),
                    output_path=str(mse_path)
                )
                
                self.assertTrue(
                    mse_path.exists(),
                    f"MSE metrics not created at {mse_path}"
                )
                logger.info(f"MSE metrics saved: {mse_path}")
                
                # Load MSE results and identify crossover point
                with open(mse_path, 'r') as f:
                    mse_results = json.load(f)
                
                # Extract crossover SNR from results
                # Crossover is identified where quantization error > 10% of instrumental error
                crossover_snr = self._identify_crossover_snr(mse_results)
                
                if crossover_snr is not None:
                    crossover_snrs.append(crossover_snr)
                    logger.info(f"Run {run_idx + 1} crossover SNR: {crossover_snr:.2f}")
                else:
                    logger.warning(f"Could not identify crossover SNR for run {run_idx + 1}")
            
            except Exception as e:
                logger.error(f"Error in run {run_idx + 1}: {e}", exc_info=True)
                raise
        
        # Verify reproducibility
        logger.info(f"\n=== Reproducibility Analysis ===")
        logger.info(f"Collected {len(crossover_snrs)} crossover SNR values: {crossover_snrs}")
        
        self.assertGreaterEqual(
            len(crossover_snrs),
            num_runs // 2,  # At least half should succeed
            "Too many runs failed to identify crossover SNR"
        )
        
        crossover_array = __import__('numpy').array(crossover_snrs)
        mean_crossover = float(crossover_array.mean())
        std_crossover = float(crossover_array.std())
        
        logger.info(f"Mean crossover SNR: {mean_crossover:.3f}")
        logger.info(f"Std dev of crossover SNR: {std_crossover:.3f}")
        
        # Main assertion: std dev < 0.5
        self.assertLess(
            std_crossover,
            0.5,
            f"Crossover SNR std dev {std_crossover:.3f} exceeds tolerance 0.5"
        )
        
        logger.info("✓ Reproducibility test PASSED: std dev < 0.5")

    def _identify_crossover_snr(self, mse_results):
        """
        Identify the crossover SNR where quantization error exceeds 10% of instrumental error.
        
        Args:
            mse_results: Dictionary with MSE metrics from compute_mse_metrics
        
        Returns:
            Crossover SNR value, or None if not found
        """
        import numpy as np
        
        # Extract SNR bins and corresponding errors
        snr_points = []
        quant_errors = []
        inst_errors = []
        
        # Iterate through results to find error curves
        if 'by_bit_depth' in mse_results:
            # Use 8-bit vs 16-bit comparison
            bd_8 = mse_results['by_bit_depth'].get('8', {})
            bd_16 = mse_results['by_bit_depth'].get('16', {})
            
            if 'by_snr_bin' in bd_8 and 'by_snr_bin' in bd_16:
                for snr_bin_key in sorted(bd_8['by_snr_bin'].keys()):
                    if snr_bin_key in bd_16['by_snr_bin']:
                        bin_8 = bd_8['by_snr_bin'][snr_bin_key]
                        bin_16 = bd_16['by_snr_bin'][snr_bin_key]
                        
                        # Extract SNR (use bin midpoint)
                        try:
                            snr_min, snr_max = map(float, snr_bin_key.split('-'))
                            snr_mid = (snr_min + snr_max) / 2.0
                        except:
                            continue
                        
                        # Quantization error: difference between 8-bit and 16-bit MSE
                        if 'mean_mse' in bin_8 and 'mean_mse' in bin_16:
                            quant_err = float(bin_8['mean_mse']) - float(bin_16['mean_mse'])
                            inst_err = float(bin_16['mean_mse'])  # 16-bit as baseline
                            
                            if inst_err > 0:
                                snr_points.append(snr_mid)
                                quant_errors.append(quant_err)
                                inst_errors.append(inst_err)
        
        # Find crossover point
        if len(snr_points) > 0:
            snr_array = np.array(snr_points)
            quant_array = np.array(quant_errors)
            inst_array = np.array(inst_errors)
            
            # Identify where quantization error > 10% of instrumental error
            threshold = 0.1 * inst_array
            crossover_mask = quant_array > threshold
            
            if np.any(crossover_mask):
                # Return the SNR at first crossover
                crossover_idx = np.where(crossover_mask)[0][0]
                return float(snr_array[crossover_idx])
        
        return None
