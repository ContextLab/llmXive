"""
Data model for Alpha Power Metric.
Represents the calculated alpha-band power for a specific electrode and subject.
"""
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
import logging
import csv
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AlphaPowerMetric:
    """
    Represents a single alpha power measurement.
    
    Attributes:
        subject_id: Unique identifier for the subject.
        electrode: Name of the electrode (e.g., 'Fz', 'Pz').
        alpha_power: The calculated power value in the alpha band (8-13 Hz).
        condition: Experimental condition (e.g., 'load_3', 'load_5').
        frequency_band: Tuple or string defining the band used (e.g., '8-13').
    """
    subject_id: str
    electrode: str
    alpha_power: float
    condition: str
    frequency_band: str = "8-13"

    def to_dict(self) -> Dict[str, Any]:
        """Converts the metric to a dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlphaPowerMetric':
        """Creates an instance from a dictionary."""
        return cls(
            subject_id=data['subject_id'],
            electrode=data['electrode'],
            alpha_power=data['alpha_power'],
            condition=data['condition'],
            frequency_band=data.get('frequency_band', '8-13')
        )


class AlphaPowerCollection:
    """
    A collection of AlphaPowerMetric objects with persistence methods.
    """
    def __init__(self):
        self.metrics: List[AlphaPowerMetric] = []

    def add(self, metric: AlphaPowerMetric) -> None:
        """Adds a metric to the collection."""
        self.metrics.append(metric)
        logger.debug(f"Added alpha power metric: {metric.subject_id} @ {metric.electrode}")

    def filter_by_subject(self, subject_id: str) -> List[AlphaPowerMetric]:
        """Returns all metrics for a specific subject."""
        return [m for m in self.metrics if m.subject_id == subject_id]

    def filter_by_electrode(self, electrode: str) -> List[AlphaPowerMetric]:
        """Returns all metrics for a specific electrode."""
        return [m for m in self.metrics if m.electrode == electrode]

    def save_to_csv(self, filepath: str) -> None:
        """Saves all metrics to a CSV file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.metrics:
            logger.warning("No metrics to save to CSV.")
            return

        fieldnames = ['subject_id', 'electrode', 'alpha_power', 'condition', 'frequency_band']
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for m in self.metrics:
                writer.writerow(m.to_dict())
        
        logger.info(f"Saved {len(self.metrics)} alpha power metrics to {filepath}")

    @classmethod
    def load_from_csv(cls, filepath: str) -> 'AlphaPowerCollection':
        """Loads metrics from a CSV file."""
        path = Path(filepath)
        if not path.exists():
            logger.warning(f"File not found: {filepath}")
            return cls()

        collection = cls()
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    metric = AlphaPowerMetric(
                        subject_id=row['subject_id'],
                        electrode=row['electrode'],
                        alpha_power=float(row['alpha_power']),
                        condition=row['condition'],
                        frequency_band=row.get('frequency_band', '8-13')
                    )
                    collection.add(metric)
                except (ValueError, KeyError) as e:
                    logger.error(f"Error parsing row in {filepath}: {e}")
        
        logger.info(f"Loaded {len(collection.metrics)} alpha power metrics from {filepath}")
        return collection

def main():
    """
    Main entry point for testing the AlphaPowerMetric model.
    """
    logging.basicConfig(level=logging.INFO)
    collection = AlphaPowerCollection()
    
    # Create sample metrics (in real usage, these come from processing)
    m1 = AlphaPowerMetric("sub-01", "Fz", 12.5, "load_3")
    m2 = AlphaPowerMetric("sub-01", "Pz", 15.2, "load_3")
    m3 = AlphaPowerMetric("sub-02", "Fz", 10.1, "load_5")
    
    collection.add(m1)
    collection.add(m2)
    collection.add(m3)
    
    output_path = "data/metrics/alpha_power_sample.csv"
    collection.save_to_csv(output_path)
    
    # Verify load
    loaded = AlphaPowerCollection.load_from_csv(output_path)
    assert len(loaded.metrics) == 3, "Failed to load metrics correctly"
    logger.info("AlphaPowerMetric model test passed.")

if __name__ == "__main__":
    main()
