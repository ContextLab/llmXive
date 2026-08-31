from typing import Iterator, Dict, Any, Optional, Literal
from datasets import load_dataset

def load_dataset_streaming(
    dataset_name: str, 
    split: str = "train", 
    streaming: bool = True
) -> Iterator[Dict[str, Any]]:
    """
    Load a dataset with streaming support.
    """
    ds = load_dataset(dataset_name, split=split, streaming=streaming)
    return iter(ds)

def load_gsm8k_streaming() -> Iterator[Dict[str, Any]]:
    """
    Load GSM8K dataset in streaming mode.
    """
    return load_dataset_streaming("gsm8k", split="train", streaming=True)

def load_humaneval_streaming() -> Iterator[Dict[str, Any]]:
    """
    Load HumanEval dataset in streaming mode.
    """
    return load_dataset_streaming("openai_humaneval", split="test", streaming=True)
