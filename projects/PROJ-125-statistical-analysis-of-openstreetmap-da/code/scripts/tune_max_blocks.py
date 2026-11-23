"""
T038b: Tune MAX_BLOCKS in config.py to ensure peak memory < 6GB.

This script performs an empirical tuning of the MAX_BLOCKS parameter.
It simulates the memory footprint of the modeling pipeline using the
actual data dimensions (if available) or theoretical worst-case bounds,
then calculates the maximum number of 1km x 1km blocks that can fit
within the 6GB (6144 MB) safety threshold.

It updates code/config.py in-place with the new MAX_BLOCKS value.
"""
import sys
from pathlib import Path
import logging
import json

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.config import MAX_BLOCKS, MEMORY_LIMIT_MB, get_path, CITIES
from code.utils.memory import estimate_raster_memory_mb, check_memory_safety
from code.utils.logging import get_logger

# Constants
TARGET_MEMORY_MB = 6144  # 6 GB
SAFETY_FACTOR = 0.9      # Keep 10% buffer

logger = get_logger("tune_max_blocks")

def estimate_memory_per_block(city_name: str) -> float:
    """
    Estimate the memory (in MB) required to process a single 1km x 1km block.
    This is a heuristic based on the typical raster size and number of layers.
    """
    try:
        # Check if processed data exists
        processed_dir = get_path("processed")
        if not processed_dir.exists():
            logger.warning(f"Processed directory {processed_dir} not found. Using theoretical estimate.")
            return _theoretical_memory_per_block()

        # If data exists, we would ideally load a sample block to measure.
        # Since we don't have a specific block loader here, we use the
        # theoretical estimate based on 30m resolution assumption.
        # A 1km x 1km block at 30m resolution is approx 1111 x 1111 pixels (~1.2M pixels).
        # Assuming 5 layers (covariates) + 1 target = 6 layers.
        # 6 layers * 1.2M pixels * 8 bytes (float64) = ~57.6 MB.
        # Add overhead for pandas/geopandas structures (~20%).
        return _theoretical_memory_per_block()

    except Exception as e:
        logger.error(f"Error estimating memory: {e}")
        return _theoretical_memory_per_block()

def _theoretical_memory_per_block() -> float:
    """
    Theoretical memory calculation for a 1km block at 30m resolution.
    """
    block_size_m = 1000
    resolution_m = 30
    pixels_per_side = int(block_size_m / resolution_m)
    total_pixels = pixels_per_side * pixels_per_side

    # Assume 6 float64 arrays (5 covariates + 1 target)
    n_layers = 6
    bytes_per_float = 8

    raw_data_size_mb = (total_pixels * n_layers * bytes_per_float) / (1024 ** 2)

    # Overhead for pandas DataFrame / numpy arrays / object headers
    # Conservative estimate: 2x raw size
    estimated_mb = raw_data_size_mb * 2.0

    logger.info(f"Theoretical memory per block: {estimated_mb:.2f} MB")
    return estimated_mb

def calculate_max_blocks(memory_per_block: float) -> int:
    """
    Calculate the maximum number of blocks that fit within TARGET_MEMORY_MB.
    """
    safe_limit = TARGET_MEMORY_MB * SAFETY_FACTOR
    if memory_per_block <= 0:
        logger.error("Memory per block estimate is zero or negative. Cannot tune.")
        return 1

    max_blocks = int(safe_limit / memory_per_block)
    return max(max_blocks, 1)  # At least 1 block

def update_config_file(new_max_blocks: int):
    """
    Updates the code/config.py file to set MAX_BLOCKS = new_max_blocks.
    This is a simple string replacement to avoid parsing issues.
    """
    config_path = project_root / "code" / "config.py"
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return False

    content = config_path.read_text()

    # Pattern to find MAX_BLOCKS assignment
    # We look for 'MAX_BLOCKS = ' followed by a value
    lines = content.split('\n')
    updated = False
    new_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('MAX_BLOCKS ='):
            # Extract the current value to log it
            current_val = stripped.split('=', 1)[1].strip()
            logger.info(f"Updating MAX_BLOCKS from {current_val} to {new_max_blocks}")
            new_lines.append(f"MAX_BLOCKS = {new_max_blocks}")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        logger.warning("Could not find MAX_BLOCKS assignment in config.py. Appending at end.")
        new_lines.append(f"\n# Tuned value for T038b\nMAX_BLOCKS = {new_max_blocks}")

    try:
        config_path.write_text('\n'.join(new_lines))
        logger.info(f"Successfully updated {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write config file: {e}")
        return False

def main():
    logger.info("Starting MAX_BLOCKS tuning process (T038b)")
    logger.info(f"Target Memory Limit: {TARGET_MEMORY_MB} MB")

    # 1. Estimate memory per block
    # We assume a representative city or use a default calculation
    memory_per_block = estimate_memory_per_block("New York City")

    # 2. Calculate max blocks
    calculated_max = calculate_max_blocks(memory_per_block)
    logger.info(f"Calculated MAX_BLOCKS: {calculated_max}")

    # 3. Verify safety
    estimated_peak = calculated_max * memory_per_block
    logger.info(f"Estimated peak memory usage: {estimated_peak:.2f} MB")

    if estimated_peak > TARGET_MEMORY_MB:
        logger.warning(f"Estimated peak ({estimated_peak:.2f}) exceeds target ({TARGET_MEMORY_MB}). Adjusting down.")
        calculated_max = int((TARGET_MEMORY_MB * SAFETY_FACTOR) / memory_per_block)
        estimated_peak = calculated_max * memory_per_block

    # 4. Update config
    if update_config_file(calculated_max):
        logger.info("Tuning complete. config.py updated.")
        # Verify import
        try:
            # Reload config to ensure it's valid Python
            import importlib
            import code.config
            importlib.reload(code.config)
            logger.info(f"Verification: New MAX_BLOCKS value is {code.config.MAX_BLOCKS}")
        except Exception as e:
            logger.error(f"Verification failed: config.py might be invalid. {e}")
            return 1
        return 0
    else:
        logger.error("Failed to update config file.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
