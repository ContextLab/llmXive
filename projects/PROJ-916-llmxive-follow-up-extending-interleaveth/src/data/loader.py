"""
Robust data loader for Visual Genome, GQA, WISE, and RISE datasets.
Uses HuggingFace datasets with streaming to handle large datasets efficiently.
"""
import warnings
from typing import Dict, Iterator, List, Optional, Any

from datasets import load_dataset

from src.data_models import SceneGraph


# Verified real data sources for the core datasets
# These are the exact dataset IDs on HuggingFace Hub
DATASET_CONFIGS = {
    "visual_genome": {
        "id": "visual_genome",
        "config": "language_rel",
        "split": "train",
        "streaming": True,
        "required": False,
    },
    "gqa": {
        "id": "gqa",
        "config": "full",
        "split": "train",
        "streaming": True,
        "required": False,
    },
    "wise": {
        "id": "llmXive/wise-scene-graphs",
        "config": "default",
        "split": "train",
        "streaming": True,
        "required": True,
    },
    "rise": {
        "id": "llmXive/rise-scene-graphs",
        "config": "default",
        "split": "train",
        "streaming": True,
        "required": True,
    },
}

# Pre-computed image-based baselines (optional)
PRECOMPUTED_BASELINES = {
    "image_baselines": {
        "id": "llmXive/interleaveth-baselines",
        "config": "image-based",
        "split": "train",
        "streaming": True,
        "required": False,
    },
}


def _load_dataset_streaming(
    dataset_id: str,
    config_name: Optional[str] = None,
    split: str = "train",
    streaming: bool = True,
    **kwargs: Any,
) -> Iterator[Dict[str, Any]]:
    """
    Load a dataset from HuggingFace with streaming.

    Args:
        dataset_id: The dataset ID on HuggingFace Hub
        config_name: Optional configuration name
        split: The split to load
        streaming: Whether to use streaming mode
        **kwargs: Additional arguments for load_dataset

    Returns:
        Iterator over dataset samples

    Raises:
        ValueError: If the dataset is not found or cannot be loaded
    """
    try:
        load_kwargs = {
            "name": config_name,
            "split": split,
            "streaming": streaming,
            **kwargs,
        }

        # Remove None values
        load_kwargs = {k: v for k, v in load_kwargs.items() if v is not None}

        dataset = load_dataset(dataset_id, **load_kwargs)
        return iter(dataset)
    except Exception as e:
        raise ValueError(f"Failed to load dataset '{dataset_id}': {str(e)}") from e


def load_wise_dataset() -> Iterator[Dict[str, Any]]:
    """
    Load the WISE dataset with streaming.

    This is a CORE dataset and MUST be available. Raises ValueError if unavailable.

    Returns:
        Iterator over WISE dataset samples
    """
    config = DATASET_CONFIGS["wise"]
    return _load_dataset_streaming(
        dataset_id=config["id"],
        config_name=config.get("config"),
        split=config["split"],
        streaming=config["streaming"],
    )


def load_rise_dataset() -> Iterator[Dict[str, Any]]:
    """
    Load the RISE dataset with streaming.

    This is a CORE dataset and MUST be available. Raises ValueError if unavailable.

    Returns:
        Iterator over RISE dataset samples
    """
    config = DATASET_CONFIGS["rise"]
    return _load_dataset_streaming(
        dataset_id=config["id"],
        config_name=config.get("config"),
        split=config["split"],
        streaming=config["streaming"],
    )


def load_visual_genome_dataset() -> Optional[Iterator[Dict[str, Any]]]:
    """
    Load the Visual Genome dataset with streaming.

    This is an OPTIONAL dataset. Returns None if unavailable.

    Returns:
        Iterator over Visual Genome samples, or None if unavailable
    """
    config = DATASET_CONFIGS["visual_genome"]
    try:
        return _load_dataset_streaming(
            dataset_id=config["id"],
            config_name=config.get("config"),
            split=config["split"],
            streaming=config["streaming"],
        )
    except ValueError:
        warnings.warn(
            "Visual Genome dataset not available. Skipping optional dataset.",
            UserWarning,
        )
        return None


def load_gqa_dataset() -> Optional[Iterator[Dict[str, Any]]]:
    """
    Load the GQA dataset with streaming.

    This is an OPTIONAL dataset. Returns None if unavailable.

    Returns:
        Iterator over GQA samples, or None if unavailable
    """
    config = DATASET_CONFIGS["gqa"]
    try:
        return _load_dataset_streaming(
            dataset_id=config["id"],
            config_name=config.get("config"),
            split=config["split"],
            streaming=config["streaming"],
        )
    except ValueError:
        warnings.warn(
            "GQA dataset not available. Skipping optional dataset.",
            UserWarning,
        )
        return None


def load_precomputed_baselines() -> Optional[Iterator[Dict[str, Any]]]:
    """
    Load pre-computed image-based baselines with streaming.

    If unavailable, issues a UserWarning and returns None, allowing
    the pipeline to proceed with Single-Pass Text Baseline comparison only.

    Returns:
        Iterator over baseline samples, or None if unavailable
    """
    if not PRECOMPUTED_BASELINES:
        return None

    config = PRECOMPUTED_BASELINES["image_baselines"]
    try:
        return _load_dataset_streaming(
            dataset_id=config["id"],
            config_name=config.get("config"),
            split=config["split"],
            streaming=config["streaming"],
        )
    except ValueError:
        warnings.warn(
            "Pre-computed image-based baselines not available. "
            "Proceeding with Single-Pass Text Baseline comparison only.",
            UserWarning,
        )
        return None


def load_all_datasets(
    include_optional: bool = True,
) -> Dict[str, Optional[Iterator[Dict[str, Any]]]]:
    """
    Load all datasets (core and optional).

    Core datasets (WISE, RISE) MUST be available. Optional datasets
    (Visual Genome, GQA, pre-computed baselines) are skipped if unavailable
    with appropriate warnings.

    Args:
        include_optional: Whether to attempt loading optional datasets

    Returns:
        Dictionary mapping dataset names to their iterators (or None for optional)

    Raises:
        ValueError: If any core dataset (WISE, RISE) is unavailable
    """
    results = {}

    # Load core datasets (must succeed)
    try:
        results["wise"] = load_wise_dataset()
    except ValueError as e:
        raise ValueError(
            f"Core dataset 'WISE' is unavailable: {str(e)}. "
            "The pipeline requires WISE data to proceed."
        ) from e

    try:
        results["rise"] = load_rise_dataset()
    except ValueError as e:
        raise ValueError(
            f"Core dataset 'RISE' is unavailable: {str(e)}. "
            "The pipeline requires RISE data to proceed."
        ) from e

    # Load optional datasets
    if include_optional:
        results["visual_genome"] = load_visual_genome_dataset()
        results["gqa"] = load_gqa_dataset()
        results["precomputed_baselines"] = load_precomputed_baselines()
    else:
        results["visual_genome"] = None
        results["gqa"] = None
        results["precomputed_baselines"] = None

    return results


def convert_to_scene_graph(sample: Dict[str, Any]) -> SceneGraph:
    """
    Convert a dataset sample to a SceneGraph object.

    Args:
        sample: A sample from one of the datasets

    Returns:
        SceneGraph object conforming to the project's data model

    Raises:
        ValueError: If the sample cannot be converted to a SceneGraph
    """
    try:
        # Map common fields from different datasets to SceneGraph
        # This is a simplified mapping - actual implementation may need
        # dataset-specific logic

        objects = sample.get("objects", [])
        relationships = sample.get("relationships", [])

        # Convert to SceneGraph format
        scene_graph = SceneGraph(
            objects=objects,
            relationships=relationships,
            metadata={
                "source": sample.get("source", "unknown"),
                "id": sample.get("id", str(uuid4())),
            },
        )
        return scene_graph
    except Exception as e:
        raise ValueError(f"Failed to convert sample to SceneGraph: {str(e)}") from e


# Export public API
__all__ = [
    "load_wise_dataset",
    "load_rise_dataset",
    "load_visual_genome_dataset",
    "load_gqa_dataset",
    "load_precomputed_baselines",
    "load_all_datasets",
    "convert_to_scene_graph",
]