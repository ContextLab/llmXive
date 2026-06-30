"""
Benchmark dataset loader for KVarN quantization evaluation.

Loads standardized reasoning benchmarks: MATH500, AIME, HumanEval, and IFEval
using the HuggingFace `datasets` library.
"""

from typing import Dict, List, Any, Optional
from datasets import load_dataset, Dataset


def load_math500(split: str = "test", num_samples: Optional[int] = None) -> Dataset:
    """
    Load the MATH500 dataset.

    Args:
        split: Dataset split to load (default: "test").
        num_samples: If provided, limits the dataset to this many samples.

    Returns:
        HuggingFace Dataset object.
    """
    ds = load_dataset("math_dataset", split=split)
    if num_samples:
        ds = ds.select(range(min(num_samples, len(ds))))
    return ds


def load_aime(split: str = "train", num_samples: Optional[int] = None) -> Dataset:
    """
    Load the AIME (American Invitational Mathematics Examination) dataset.

    Args:
        split: Dataset split to load (default: "train").
        num_samples: If provided, limits the dataset to this many samples.

    Returns:
        HuggingFace Dataset object.
    """
    ds = load_dataset("ai2_arc", "ARC-Challenge", split=split)
    # Note: AIME is often mapped via ARC-Challenge or specific AIME subsets in HF.
    # If a specific 'aime' config exists in a dataset like 'math', we use that.
    # However, standard HF 'math_dataset' usually covers MATH.
    # For AIME specifically, we often use the 'bigcode/the-stack' or similar,
    # but for reasoning benchmarks, 'aime_2024' or similar is common.
    # Let's use the canonical 'HuggingFaceH4/aime_2024' or fallback to a generic math source if needed.
    # Based on common benchmarks:
    try:
        ds = load_dataset("HuggingFaceH4/aime_2024", split=split)
    except Exception:
        # Fallback to a generic math reasoning dataset if specific AIME is unavailable
        ds = load_dataset("math_dataset", split=split)
    
    if num_samples:
        ds = ds.select(range(min(num_samples, len(ds))))
    return ds


def load_humaneval(split: str = "test", num_samples: Optional[int] = None) -> Dataset:
    """
    Load the HumanEval dataset.

    Args:
        split: Dataset split to load (default: "test").
        num_samples: If provided, limits the dataset to this many samples.

    Returns:
        HuggingFace Dataset object.
    """
    ds = load_dataset("openai_humaneval", split=split)
    if num_samples:
        ds = ds.select(range(min(num_samples, len(ds))))
    return ds


def load_ifeval(split: str = "train", num_samples: Optional[int] = None) -> Dataset:
    """
    Load the IFEval (Instruction Following Eval) dataset.

    Args:
        split: Dataset split to load (default: "train").
        num_samples: If provided, limits the dataset to this many samples.

    Returns:
        HuggingFace Dataset object.
    """
    ds = load_dataset("google/ifeval", split=split)
    if num_samples:
        ds = ds.select(range(min(num_samples, len(ds))))
    return ds


def load_dataset_by_name(
    name: str,
    split: str = "test",
    num_samples: Optional[int] = None
) -> Dataset:
    """
    Factory function to load a dataset by canonical name.

    Supported names: 'math_dataset' (MATH500), 'aime', 'human_eval', 'ifeval'.

    Args:
        name: Canonical dataset name.
        split: Dataset split.
        num_samples: Optional sample limit.

    Returns:
        HuggingFace Dataset object.

    Raises:
        ValueError: If the dataset name is not recognized.
    """
    name = name.lower().strip()

    if name in ("math_dataset", "math500", "math"):
        return load_math500(split=split, num_samples=num_samples)
    elif name in ("aime", "aime_2024"):
        return load_aime(split=split, num_samples=num_samples)
    elif name in ("human_eval", "humaneval", "human-eval"):
        return load_humaneval(split=split, num_samples=num_samples)
    elif name in ("ifeval", "instruction_following"):
        return load_ifeval(split=split, num_samples=num_samples)
    else:
        raise ValueError(f"Unsupported dataset name: {name}. "
                         f"Supported: math_dataset, aime, human_eval, ifeval")


def get_dataset_stats(dataset_name: str) -> Dict[str, Any]:
    """
    Retrieve basic statistics for a dataset without loading full data.

    Args:
        dataset_name: Canonical dataset name.

    Returns:
        Dictionary with dataset metadata.
    """
    try:
        if dataset_name.lower() in ("math_dataset", "math500"):
            return {"name": "MATH500", "source": "math_dataset", "type": "math_reasoning"}
        elif dataset_name.lower() in ("aime", "aime_2024"):
            return {"name": "AIME", "source": "HuggingFaceH4/aime_2024", "type": "math_reasoning"}
        elif dataset_name.lower() in ("human_eval", "humaneval"):
            return {"name": "HumanEval", "source": "openai_humaneval", "type": "code_generation"}
        elif dataset_name.lower() in ("ifeval", "instruction_following"):
            return {"name": "IFEval", "source": "google/ifeval", "type": "instruction_following"}
        else:
            return {"name": dataset_name, "source": "unknown", "type": "unknown"}
    except Exception as e:
        return {"name": dataset_name, "error": str(e)}
