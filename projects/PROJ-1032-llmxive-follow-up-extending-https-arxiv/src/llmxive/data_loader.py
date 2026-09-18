"""Data loader for GSM8K dataset with integrity checks."""
import os
from typing import Iterator, Dict, Any
from pathlib import Path
from datasets import load_dataset
from src.llmxive.exceptions import DATA_INTEGRITY_ERROR

class GSM8KLoader:
    """Loader for GSM8K dataset with streaming and integrity verification."""
    
    def __init__(self, split: str = "train", streaming: bool = True):
        self.split = split
        self.streaming = streaming
        self.data_source = os.getenv("LLMXIVE_DATA_SOURCE", "openai/gsm8k")
        
        # Load dataset with streaming to prevent OOM
        try:
            self.dataset = load_dataset(
                self.data_source,
                split=split,
                streaming=streaming
            )
        except Exception as e:
            raise DATA_INTEGRITY_ERROR(f"Failed to load dataset {self.data_source}: {str(e)}")
    
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Iterate over dataset examples."""
        for item in self.dataset:
            yield item
    
    def get_sample(self, n: int = 100) -> list:
        """Get a sample of n examples (for testing)."""
        if self.streaming:
            # For streaming, we must iterate
            samples = []
            for i, item in enumerate(self.dataset):
                if i >= n:
                    break
                samples.append(item)
            return samples
        else:
            return list(self.dataset)[:n]
    
    def verify_no_overlap(self, training_indices: set, test_indices: set) -> bool:
        """Verify no overlap between training and test indices."""
        overlap = training_indices.intersection(test_indices)
        if overlap:
            raise DATA_INTEGRITY_ERROR(f"Data overlap detected: {overlap}")
        return True
