"""
code/main.py: Orchestration interface for the llmXive data pipeline.

This module defines the contract and dependencies for the data pipeline:
1. Download (T011)
2. Derive (T012a)
3. Noise Injection (T013)
4. Quantization (T012)

It ensures the correct ordering and interfaces are established before
the implementation of the specific pipeline stages.
"""
import os
import sys
import time
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field

# Local imports from project structure
from config import ensure_dirs, set_seed, get_config_summary, DATA_DIR, LOGS_DIR, RESULTS_DIR
from utils.logging import get_logger, LlmXiveError, log_metric
from utils.monitor import ResourceMonitor, get_peak_memory_mb, format_bytes
from utils.checkpoint import CheckpointManager, get_checkpoint_manager
from data.schema import QuantizationLevel, DiscreteStateVector
from data.validation import validate_dataset_for_degeneracy, DegeneracyError

# Placeholder imports for pipeline stages (to be implemented in T011, T012a, T013, T012)
# These are imported conditionally or via a factory pattern to avoid circular dependencies
# during the initial orchestration definition.
try:
    from data.download_libero import download_libero_subset
    DOWNLOAD_FN: Optional[Callable] = download_libero_subset
except ImportError:
    DOWNLOAD_FN = None
    logging.getLogger(__name__).warning("download_libero not yet implemented (T011)")

try:
    from data.velocity_deriver import derive_velocity_fields
    DERIVE_FN: Optional[Callable] = derive_velocity_fields
except ImportError:
    DERIVE_FN = None
    logging.getLogger(__name__).warning("velocity_deriver not yet implemented (T012a)")

try:
    from data.noise import inject_noise
    NOISE_FN: Optional[Callable] = inject_noise
except ImportError:
    NOISE_FN = None
    logging.getLogger(__name__).warning("noise not yet implemented (T013)")

try:
    from data.quantize import quantize_dataset
    QUANTIZE_FN: Optional[Callable] = quantize_dataset
except ImportError:
    QUANTIZE_FN = None
    logging.getLogger(__name__).warning("quantize not yet implemented (T012)")


@dataclass
class PipelineConfig:
    """Configuration container for the data pipeline."""
    seed: int
    quantization_bits: int  # Must be in [4, 6, 8, 16]
    noise_std_dev: float
    subset_size: int
    input_hdf5_path: Optional[str] = None
    output_json_path: Optional[str] = None
    skip_download: bool = False
    skip_derive: bool = False
    skip_noise: bool = False
    skip_quantize: bool = False
    validate_degeneracy: bool = True


def validate_header_size(file_path: str) -> Dict[str, Any]:
    """
    Validates the header of a potential HDF5 file to estimate size.
    This is a utility for T040 to check dataset size before full load.
    """
    import h5py
    logger = get_logger(__name__)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found for header validation: {file_path}")
    
    try:
        with h5py.File(file_path, 'r') as f:
            # Basic header info
            num_groups = len(f.keys())
            size_estimate = 0
            for key in f.keys():
                if isinstance(f[key], h5py.Group):
                    num_groups += len(f[key].keys())
                else:
                    size_estimate += f[key].size * 4 # Approx float32
            
            return {
                "file": file_path,
                "valid": True,
                "num_groups": num_groups,
                "estimated_bytes": size_estimate,
                "estimated_mb": size_estimate / (1024 * 1024)
            }
    except Exception as e:
        logger.error(f"Header validation failed: {e}")
        return {
            "file": file_path,
            "valid": False,
            "error": str(e)
        }


def run_pipeline(config: PipelineConfig) -> Dict[str, Any]:
    """
    Executes the data pipeline in the correct order:
    1. Download (if not skipped)
    2. Derive Velocity (if not skipped)
    3. Inject Noise (if not skipped)
    4. Quantize (if not skipped)
    
    Returns a summary of the run.
    """
    logger = get_logger(__name__)
    start_time = time.time()
    results = {
        "config": get_config_summary(config.seed),
        "steps": [],
        "status": "running",
        "peak_memory_mb": 0
    }

    # Initialize monitoring
    monitor = ResourceMonitor()
    monitor.start()

    try:
        # Step 1: Download
        if not config.skip_download:
            if DOWNLOAD_FN is None:
                raise LlmXiveError("Download function not implemented (T011).")
            logger.info("Step 1: Downloading LIBERO subset...")
            download_result = DOWNLOAD_FN(
                subset_size=config.subset_size,
                output_path=config.input_hdf5_path or str(DATA_DIR / "raw" / "libero_subset.h5")
            )
            results["steps"].append({
                "step": "download",
                "status": "success",
                "output": download_result.get("output_path", "unknown")
            })
            config.input_hdf5_path = download_result.get("output_path")
        else:
            logger.info("Step 1: Skipped (Download)")
            results["steps"].append({"step": "download", "status": "skipped"})

        # Step 2: Derive Velocity
        if not config.skip_derive:
            if DERIVE_FN is None:
                raise LlmXiveError("Derive function not implemented (T012a).")
            logger.info("Step 2: Deriving velocity fields...")
            # Assuming derive returns a modified dataset or path
            derive_result = DERIVE_FN(
                input_path=config.input_hdf5_path,
                output_path=str(Path(config.input_hdf5_path).parent / "libero_velocity.h5")
            )
            results["steps"].append({
                "step": "derive",
                "status": "success",
                "output": derive_result.get("output_path")
            })
            # Update input for next step if output differs
            config.input_hdf5_path = derive_result.get("output_path")

        # Step 3: Inject Noise
        if not config.skip_noise:
            if NOISE_FN is None:
                raise LlmXiveError("Noise function not implemented (T013).")
            logger.info("Step 3: Injecting noise...")
            noise_result = NOISE_FN(
                input_path=config.input_hdf5_path,
                output_path=str(Path(config.input_hdf5_path).parent / "libero_noisy.h5"),
                std_dev=config.noise_std_dev,
                seed=config.seed
            )
            results["steps"].append({
                "step": "noise",
                "status": "success",
                "output": noise_result.get("output_path")
            })
            config.input_hdf5_path = noise_result.get("output_path")

        # Step 4: Quantize
        if not config.skip_quantize:
            if QUANTIZE_FN is None:
                raise LlmXiveError("Quantize function not implemented (T012).")
            logger.info("Step 4: Quantizing to discrete vectors...")
            
            # Validate bit depth
            try:
                q_level = QuantizationLevel(config.quantization_bits)
            except ValueError:
                raise LlmXiveError(f"Invalid quantization level: {config.quantization_bits}. Must be 4, 6, 8, or 16.")

            quantize_result = QUANTIZE_FN(
                input_path=config.input_hdf5_path,
                output_path=config.output_json_path or str(RESULTS_DIR / "discrete_vectors.json"),
                bit_depth=config.quantization_bits,
                seed=config.seed
            )
            results["steps"].append({
                "step": "quantize",
                "status": "success",
                "output": quantize_result.get("output_path")
            })
            final_output = quantize_result.get("output_path")

            # Step 5: Validation (T015 logic embedded here for orchestration)
            if config.validate_degeneracy:
                logger.info("Step 5: Validating for degeneracy...")
                try:
                    validate_dataset_for_degeneracy(final_output, q_level)
                    results["steps"].append({"step": "validation", "status": "success"})
                except DegeneracyError as e:
                    results["steps"].append({"step": "validation", "status": "failed", "error": str(e)})
                    raise e

        results["status"] = "completed"
        
    except Exception as e:
        results["status"] = "failed"
        results["error"] = str(e)
        logger.error(f"Pipeline failed: {traceback.format_exc()}")
        raise
    finally:
        monitor.stop()
        peak_mem = get_peak_memory_mb()
        results["peak_memory_mb"] = peak_mem
        results["duration_seconds"] = time.time() - start_time
        log_metric("pipeline_duration", results["duration_seconds"])
        log_metric("pipeline_peak_memory_mb", peak_mem)

    return results


def main():
    """
    Main entry point for the orchestration interface.
    Parses arguments (or uses defaults) and runs the pipeline.
    Outputs a validation log confirming the interface definition.
    """
    logger = get_logger(__name__)
    logger.info("Starting llmXive Data Pipeline Orchestration (T014a)")
    
    # Ensure directories exist
    ensure_dirs()

    # Default configuration for validation run
    config = PipelineConfig(
        seed=42,
        quantization_bits=8,
        noise_std_dev=0.01,
        subset_size=50,
        skip_download=False,
        skip_derive=False,
        skip_noise=False,
        skip_quantize=False,
        validate_degeneracy=True
    )

    # Log interface definition
    interface_log = {
        "task_id": "T014a",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "interface_definition": {
            "download": "download_libero.download_libero_subset",
            "derive": "velocity_deriver.derive_velocity_fields",
            "noise": "noise.inject_noise",
            "quantize": "quantize.quantize_dataset",
            "validation": "validation.validate_dataset_for_degeneracy"
        },
        "execution_order": ["download", "derive", "noise", "quantize", "validation"],
        "dependencies": {
            "T011": "download_libero.py",
            "T012a": "velocity_deriver.py",
            "T013": "noise.py",
            "T012": "quantize.py",
            "T015": "validation.py"
        },
        "status": "Interface defined and ready for implementation"
    }

    # Write validation log
    log_path = LOGS_DIR / "interface_validation.log"
    with open(log_path, 'w') as f:
        json.dump(interface_log, f, indent=2)
    
    logger.info(f"Interface validation log written to {log_path}")
    print(f"Interface validation log written to {log_path}")

    # If dependencies are missing, we still validate the interface structure
    # but we cannot run the full pipeline.
    missing_deps = []
    if DOWNLOAD_FN is None: missing_deps.append("T011 (download_libero)")
    if DERIVE_FN is None: missing_deps.append("T012a (velocity_deriver)")
    if NOISE_FN is None: missing_deps.append("T013 (noise)")
    if QUANTIZE_FN is None: missing_deps.append("T012 (quantize)")

    if missing_deps:
        logger.warning(f"Missing dependencies (expected for T014a): {missing_deps}")
        print(f"Pipeline skipped execution due to missing dependencies: {missing_deps}")
        return 0

    # Run pipeline if all dependencies are present
    try:
        results = run_pipeline(config)
        logger.info(f"Pipeline completed: {results['status']}")
        print(f"Pipeline completed: {results['status']}")
        return 0
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        print(f"Pipeline execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())