"""
Streaming dataset loader for GSM8K, HumanEval, CommonCrawl and Dolly.

Implements task T004: streaming support via
``datasets.load_dataset(..., streaming=True)``.

Real-data policy: this loader NEVER fabricates or falls back to
synthetic data. If the real Hugging Face Hub fetch fails, the error
is re-raised (fail loudly) so the execution stage can act on it.
"""
from typing import Iterator, Dict, Any, Optional, Callable
from datasets import load_dataset
import logging
import json
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# Streaming parameters (see T043: chunk_size=1000, batch_size=32)
CHUNK_SIZE = 1000
BATCH_SIZE = 32

# Ensure output directory exists for logging
LOG_DIR = Path("data/processed")
LOG_DIR.mkdir(parents=True, exist_ok=True)
STREAMING_LOG_PATH = LOG_DIR / "streaming_config.log"

# Canonical Hugging Face dataset identifiers and required configs.
DATASET_REGISTRY: Dict[str, Dict[str, Any]] = {
    "gsm8k": {"name": "gsm8k", "config": "main", "split": "train"},
    "humaneval": {"name": "openai_humaneval", "config": None, "split": "test"},
    "openai_humaneval": {"name": "openai_humaneval", "config": None, "split": "test"},
    "dolly": {"name": "databricks/dolly-15k", "config": None, "split": "train"},
    "common_crawl": {"name": "wikimedia/wikipedia", "config": "20231101.en", "split": "train"},
}


def _log_streaming_config(
    dataset_name: str,
    split: str,
    strategy: str,
    estimated_size_mb: Optional[float] = None,
    sample_count: int = 0,
):
    """
    Logs streaming configuration to data/processed/streaming_config.log.
    This ensures explicit logging of sample size and streaming strategy as required.
    """
    log_entry = {
        "dataset": dataset_name,
        "split": split,
        "strategy": strategy,
        "chunk_size": CHUNK_SIZE,
        "batch_size": BATCH_SIZE,
        "streaming_mode": True,
        "estimated_size_mb": estimated_size_mb,
        "sample_count_processed": sample_count,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    with open(STREAMING_LOG_PATH, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    logger.info(
        f"Streaming config logged: {dataset_name} -> {strategy} "
        f"(samples: {sample_count}, chunk_size={CHUNK_SIZE}, batch_size={BATCH_SIZE})"
    )


def load_dataset_streaming(
    dataset_name: str,
    split: str = "train",
    streaming: bool = True,
    dataset_config: Optional[Dict[str, Any]] = None,
) -> Iterator[Dict[str, Any]]:
    """
    Load a dataset with streaming support.

    This function strictly enforces real data sourcing. If the dataset
    cannot be fetched from the Hugging Face Hub or the specified source,
    it raises a RuntimeError. NO synthetic or mock data is generated.

    For large datasets (e.g., CommonCrawl-scale corpora), streaming=True
    ensures that data is processed in chunks to fit within memory
    constraints (~7GB RAM).

    Args:
        dataset_name: The name of the dataset on Hugging Face Hub
            (e.g. 'gsm8k', 'humaneval', 'dolly', 'common_crawl').
        split: The split to load (e.g., 'train', 'test').
        streaming: If True, returns an iterator.
        dataset_config: Optional config dict forwarded to load_dataset
            (e.g. {'name': 'main'} for GSM8K).

    Returns:
        An iterator yielding dataset samples.

    Raises:
        RuntimeError: If the dataset fetch fails (network error, missing
            dataset, etc.). Never falls back to synthetic data.
    """
    strategy = "streaming" if streaming else "full_load"

    # Resolve canonical dataset id / config from the registry.
    key = dataset_name.lower()
    registry_entry = DATASET_REGISTRY.get(key)
    if registry_entry is not None:
        hub_id = registry_entry["name"]
        if dataset_config is None or "name" not in (dataset_config or {}):
            cfg_name = registry_entry["config"]
        else:
            cfg_name = dataset_config["name"]
    else:
        hub_id = dataset_name
        cfg_name = (dataset_config or {}).get("name")

    # Estimate size logic for specific datasets
    estimated_size = None
    if "common_crawl" in key or "wikipedia" in hub_id.lower():
        estimated_size = 50000.0  # Large dataset indicator
        strategy = "streaming_large_chunked"
    elif "dolly" in key or "dolly" in hub_id.lower():
        estimated_size = 500.0
        strategy = "streaming_standard"
    elif "gsm8k" in key:
        estimated_size = 50.0
        strategy = "streaming_standard"
    elif "humaneval" in key:
        estimated_size = 10.0
        strategy = "streaming_standard"

    load_kwargs: Dict[str, Any] = {}
    if cfg_name is not None:
        load_kwargs["name"] = cfg_name

    try:
        logger.info(
            f"Attempting to stream dataset: {hub_id} "
            f"(split={split}, streaming={streaming})"
        )

        # Load with streaming enabled
        ds = load_dataset(
            hub_id,
            split=split,
            streaming=streaming,
            **load_kwargs,
        )

        # Log the streaming configuration immediately upon successful load
        _log_streaming_config(
            dataset_name, split, strategy, estimated_size, sample_count=0
        )

        return iter(ds)
    except Exception as e:
        # Fail loudly: Do not catch and return synthetic data.
        # Propagate the error so the pipeline stops and the user knows
        # the real source is unavailable.
        logger.error(
            f"CRITICAL: Failed to load real dataset '{dataset_name}' "
            f"(hub id '{hub_id}'). No fallback to synthetic data "
            f"allowed. Error: {e}"
        )
        raise RuntimeError(
            f"Failed to load real dataset '{dataset_name}' "
            f"(hub id '{hub_id}', split={split}): {e}"
        ) from e


def load_gsm8k_streaming() -> Iterator[Dict[str, Any]]:
    """
    Load GSM8K dataset in streaming mode.

    Enforces strict real data loading. Raises if GSM8K is unavailable.
    """
    return load_dataset_streaming(
        "gsm8k", split="train", streaming=True, dataset_config={"name": "main"}
    )


def load_humaneval_streaming() -> Iterator[Dict[str, Any]]:
    """
    Load HumanEval dataset in streaming mode.

    Enforces strict real data loading. Raises if HumanEval is unavailable.
    """
    return load_dataset_streaming("openai_humaneval", split="test", streaming=True)


def load_common_crawl_streaming(
    subset: str = "20231101.en", split: str = "train"
) -> Iterator[Dict[str, Any]]:
    """
    Load a large natural-language corpus in streaming mode.

    This function is specifically designed to handle large datasets by
    streaming chunks of data to avoid memory overflow. The canonical
    large public corpus used for the natural-language domain is
    Wikipedia (20231101.en dump); CommonCrawl itself is not exposed
    as a single loadable HF dataset, so the equivalent large-scale
    natural-language corpus is streamed instead.

    Args:
        subset: The config/subset of the corpus (e.g., '20231101.en').
        split: The split to load.

    Returns:
        An iterator yielding dataset samples.
    """
    return load_dataset_streaming(
        "common_crawl",
        split=split,
        streaming=True,
        dataset_config={"name": subset},
    )


def load_dolly_streaming() -> Iterator[Dict[str, Any]]:
    """
    Load Dolly dataset in streaming mode.

    Returns:
        An iterator yielding dataset samples.
    """
    return load_dataset_streaming("databricks/dolly-15k", split="train", streaming=True)


def process_streamed_dataset_with_logging(
    dataset_name: str,
    split: str,
    process_fn: Callable,
    max_samples: Optional[int] = None,
) -> int:
    """
    Utility to process a streamed dataset, counting samples and logging
    the final count. This ensures the logging requirement for sample
    size is met for any processing task.

    Args:
        dataset_name: Name of the dataset.
        split: Split name.
        process_fn: Function to apply to each sample.
        max_samples: Optional limit on number of samples to process.

    Returns:
        Total number of samples processed.
    """
    iterator = load_dataset_streaming(dataset_name, split=split, streaming=True)
    count = 0

    logger.info(f"Starting stream processing for {dataset_name}...")
    start_time = time.time()

    for sample in iterator:
        if max_samples and count >= max_samples:
            break

        process_fn(sample)
        count += 1

        # Log progress every CHUNK_SIZE samples for large streams
        if count % CHUNK_SIZE == 0:
            logger.info(f"Processed {count} samples...")

    elapsed = time.time() - start_time
    _log_streaming_config(dataset_name, split, "streaming_processed", sample_count=count)
    logger.info(f"Completed processing {count} samples in {elapsed:.2f}s")

    return count