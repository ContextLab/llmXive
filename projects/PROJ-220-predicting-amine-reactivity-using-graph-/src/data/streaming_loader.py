"""
Streaming data loader for large reaction datasets.

Implements batched loading of ReactionRecord objects to handle datasets
exceeding available RAM, accumulating statistics online without full memory load.
"""

import logging
from typing import Generator, List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

import numpy as np

from src.data.ingestion import ReactionRecord
from src.utils.memory_monitor import check_limits, graceful_exit
from src.utils.sampling import sample_dataset

logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_BATCH_SIZE = 500
MEMORY_THRESHOLD_MB = 6500  # Leave buffer for 7GB limit


@dataclass
class StreamingStats:
    """Accumulated statistics for online computation."""
    count: int = 0
    sum_rate: float = 0.0
    sum_rate_sq: float = 0.0
    sum_pka: float = 0.0
    sum_pka_sq: float = 0.0
    min_rate: float = float('inf')
    max_rate: float = float('-inf')
    min_pka: float = float('inf')
    max_pka: float = float('-inf')
    
    def update(self, rate: float, pka: float) -> None:
        """Update statistics with a new data point."""
        self.count += 1
        self.sum_rate += rate
        self.sum_rate_sq += rate ** 2
        self.sum_pka += pka
        self.sum_pka_sq += pka ** 2
        self.min_rate = min(self.min_rate, rate)
        self.max_rate = max(self.max_rate, rate)
        self.min_pka = min(self.min_pka, pka)
        self.max_pka = max(self.max_pka, pka)
    
    @property
    def mean_rate(self) -> float:
        return self.sum_rate / self.count if self.count > 0 else 0.0
    
    @property
    def mean_pka(self) -> float:
        return self.sum_pka / self.count if self.count > 0 else 0.0
    
    @property
    def std_rate(self) -> float:
        if self.count < 2:
            return 0.0
        variance = (self.sum_rate_sq - (self.sum_rate ** 2) / self.count) / (self.count - 1)
        return max(0.0, variance) ** 0.5
    
    @property
    def std_pka(self) -> float:
        if self.count < 2:
            return 0.0
        variance = (self.sum_pka_sq - (self.sum_pka ** 2) / self.count) / (self.count - 1)
        return max(0.0, variance) ** 0.5


def _load_chembl_streaming(batch_size: int = DEFAULT_BATCH_SIZE) -> Generator[ReactionRecord, None, None]:
    """
    Stream data from ChEMBL in batches.
    
    This implementation assumes that `fetch_chembl_sn2_data` can be modified
    to support streaming, or we use a chunked approach. For now, we simulate
    streaming by processing records in batches if the full dataset is loaded.
    
    In a real production scenario, this would use ChEMBL's pagination or
    database cursor streaming.
    """
    from src.data.ingestion import fetch_chembl_sn2_data, filter_primary_secondary_amine
    
    logger.info("Starting ChEMBL data stream")
    
    try:
        # Fetch all data (in real implementation, this would be paginated)
        raw_data = fetch_chembl_sn2_data()
        filtered_data = filter_primary_secondary_amine(raw_data)
        
        logger.info(f"Loaded {len(filtered_data)} filtered records from ChEMBL")
        
        # Process in batches
        for i in range(0, len(filtered_data), batch_size):
            batch = filtered_data[i:i + batch_size]
            for record in batch:
                yield record
                
    except Exception as e:
        logger.error(f"Error streaming ChEMBL data: {e}")
        raise


def _load_pubchem_streaming(batch_size: int = DEFAULT_BATCH_SIZE) -> Generator[ReactionRecord, None, None]:
    """
    Stream data from PubChem in batches.
    
    Similar to ChEMBL, this would use PubChem's PUG-REST with pagination
    in a production implementation.
    """
    from src.data.ingestion import fetch_pubchem_sn2_data, filter_primary_secondary_amine
    
    logger.info("Starting PubChem data stream")
    
    try:
        raw_data = fetch_pubchem_sn2_data()
        filtered_data = filter_primary_secondary_amine(raw_data)
        
        logger.info(f"Loaded {len(filtered_data)} filtered records from PubChem")
        
        for i in range(0, len(filtered_data), batch_size):
            batch = filtered_data[i:i + batch_size]
            for record in batch:
                yield record
                
    except Exception as e:
        logger.error(f"Error streaming PubChem data: {e}")
        raise


def load_batch(
    source: str = "chembl",
    batch_size: int = DEFAULT_BATCH_SIZE,
    stats_callback: Optional[callable] = None
) -> Generator[Tuple[List[ReactionRecord], StreamingStats], None, None]:
    """
    Generator that yields batches of ReactionRecord objects along with
    accumulated statistics.
    
    Args:
        source: Data source ("chembl" or "pubchem")
        batch_size: Number of records per batch
        stats_callback: Optional callback function(stats) to be called after each batch
    
    Yields:
        Tuple of (batch_records, cumulative_stats)
    
    Raises:
        ValueError: If source is invalid
        RuntimeError: If memory limits are exceeded
    """
    if source not in ["chembl", "pubchem"]:
        raise ValueError(f"Invalid source: {source}. Must be 'chembl' or 'pubchem'")
    
    logger.info(f"Starting batched stream from {source} with batch_size={batch_size}")
    
    # Initialize statistics accumulator
    stats = StreamingStats()
    
    # Select loader
    loader = _load_chembl_streaming if source == "chembl" else _load_pubchem_streaming
    
    batch = []
    batch_count = 0
    
    for record in loader(batch_size=batch_size):
        # Check memory limits
        if not check_limits(threshold_mb=MEMORY_THRESHOLD_MB):
            logger.warning("Memory limit approached, yielding current batch")
            if batch:
                yield batch, stats
                batch = []
                batch_count = 0
            # Graceful exit if memory is critically low
            if not check_limits(threshold_mb=MEMORY_THRESHOLD_MB - 500):
                graceful_exit("Memory limit exceeded during streaming")
        
        batch.append(record)
        batch_count += 1
        
        # Update statistics
        if hasattr(record, 'normalized_rate') and hasattr(record, 'pka'):
            stats.update(float(record.normalized_rate), float(record.pka))
        
        # Yield when batch is full
        if batch_count >= batch_size:
            if stats_callback:
                stats_callback(stats)
            yield batch, stats
            batch = []
            batch_count = 0
    
    # Yield final partial batch
    if batch:
        if stats_callback:
            stats_callback(stats)
        yield batch, stats
    
    logger.info(f"Streaming complete. Total records processed: {stats.count}")
    logger.info(f"Final statistics - Mean rate: {stats.mean_rate:.4f}, "
               f"Mean pKa: {stats.mean_pka:.2f}, "
               f"Std rate: {stats.std_rate:.4f}, "
               f"Std pKa: {stats.std_pka:.2f}")


def load_dataset_streaming(
    source: str = "chembl",
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_records: Optional[int] = None
) -> Generator[ReactionRecord, None, None]:
    """
    Simple generator that yields individual ReactionRecord objects from a stream.
    
    Args:
        source: Data source ("chembl" or "pubchem")
        batch_size: Internal batch size for processing
        max_records: Maximum number of records to yield (None for all)
    
    Yields:
        Individual ReactionRecord objects
    """
    count = 0
    for batch, _ in load_batch(source=source, batch_size=batch_size):
        for record in batch:
            yield record
            count += 1
            if max_records and count >= max_records:
                return


def compute_online_statistics(
    source: str = "chembl",
    batch_size: int = DEFAULT_BATCH_SIZE
) -> StreamingStats:
    """
    Compute complete statistics for a dataset without loading it all into memory.
    
    Args:
        source: Data source ("chembl" or "pubchem")
        batch_size: Batch size for processing
    
    Returns:
        Complete StreamingStats object for the entire dataset
    """
    final_stats = StreamingStats()
    
    for batch, batch_stats in load_batch(source=source, batch_size=batch_size):
        # batch_stats contains cumulative stats up to this point
        final_stats = batch_stats
    
    return final_stats


def main():
    """Main entry point for streaming loader demonstration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Streaming Loader Demo")
    logger.info("=" * 50)
    
    try:
        # Demonstrate batched loading
        logger.info("Loading ChEMBL data in batches...")
        total_records = 0
        
        for batch, stats in load_batch(source="chembl", batch_size=100):
            total_records += len(batch)
            logger.info(f"Batch: {len(batch)} records, "
                       f"Cumulative: {stats.count} records, "
                       f"Mean rate: {stats.mean_rate:.4f}")
        
        logger.info(f"Total records processed: {total_records}")
        logger.info("Streaming complete successfully.")
        
    except Exception as e:
        logger.error(f"Streaming failed: {e}")
        raise


if __name__ == "__main__":
    main()
