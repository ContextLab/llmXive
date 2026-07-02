"""
Data model for PLV (Phase Locking Value) metrics.
"""
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
import logging
import csv
from pathlib import Path
import pandas as pd

@dataclass
class PLVMetric:
    """
    Represents a single PLV measurement between two electrodes for a subject.
    """
    subject_id: str
    electrode_pair: str
    plv_value: float
    delay_start: float = 0.0
    delay_end: float = 1.0
    condition: str = "all"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class PLVCollection:
    """
    Collection of PLV metrics.
    """
    def __init__(self, metrics: List[PLVMetric] = None):
        self.metrics = metrics if metrics is not None else []

    def add(self, metric: PLVMetric):
        self.metrics.append(metric)

    def __len__(self):
        return len(self.metrics)

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the collection to a pandas DataFrame.
        """
        if not self.metrics:
            return pd.DataFrame()
        
        data = [m.to_dict() for m in self.metrics]
        return pd.DataFrame(data)

    def save_to_csv(self, path: Path) -> None:
        """
        Save the collection to a CSV file.
        """
        df = self.to_dataframe()
        df.to_csv(path, index=False)
        logging.info(f"Saved {len(df)} PLV metrics to {path}")

def main():
    """
    Main entry point for testing the PLV model.
    """
    logging.basicConfig(level=logging.INFO)
    collection = PLVCollection()
    collection.add(PLVMetric("sub-01", "F3-P3", 0.45, 0.5, 1.5, "high_load"))
    collection.add(PLVMetric("sub-01", "F4-P4", 0.32, 0.5, 1.5, "high_load"))
    
    df = collection.to_dataframe()
    print(df)

if __name__ == "__main__":
    main()