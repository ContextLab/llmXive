"""
Data model for Working Memory Capacity.
Represents the behavioral performance metric (k-score or d-prime) derived from the task.
"""
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
import logging
import csv
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class WMCapacity:
    """
    Represents the working memory capacity metric for a subject.
    
    Attributes:
        subject_id: ID of the subject.
        k_score: Change detection capacity (K) score.
        d_prime: Sensitivity index (d') if calculated.
        accuracy: Overall accuracy percentage.
        reaction_time: Mean reaction time (ms).
        source: Description of how the score was derived (e.g., 'Cowan K', 'Signal Detection').
    """
    subject_id: str
    k_score: Optional[float] = None
    d_prime: Optional[float] = None
    accuracy: Optional[float] = None
    reaction_time: Optional[float] = None
    source: str = "derived"

    def __post_init__(self):
        if self.k_score is None and self.d_prime is None:
            logger.warning("WMCapacity initialized with no primary capacity metric (k or d').")

    def to_dict(self) -> dict:
        """Converts the metric to a dictionary for export."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'WMCapacity':
        """Constructs an instance from a dictionary."""
        return cls(
            subject_id=data['subject_id'],
            k_score=data.get('k_score'),
            d_prime=data.get('d_prime'),
            accuracy=data.get('accuracy'),
            reaction_time=data.get('reaction_time'),
            source=data.get('source', 'derived')
        )

    def is_valid(self) -> bool:
        """Checks if the record has at least one primary metric."""
        return self.k_score is not None or self.d_prime is not None

@dataclass
class WMCapacityCollection:
    """
    A container for multiple WMCapacity records, providing CSV I/O operations.
    """
    records: List[WMCapacity] = None

    def __post_init__(self):
        if self.records is None:
            self.records = []

    def add(self, record: WMCapacity) -> None:
        """Adds a single record to the collection."""
        if not record.is_valid():
            logger.warning(f"Skipping invalid record for subject {record.subject_id}")
            return
        self.records.append(record)

    def from_csv(self, file_path: str) -> None:
        """Loads records from a CSV file."""
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"CSV file not found: {file_path}. Creating empty collection.")
            return

        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert optional float fields
                for field in ['k_score', 'd_prime', 'accuracy', 'reaction_time']:
                    if row.get(field) == '' or row.get(field) is None:
                        row[field] = None
                    elif row.get(field) is not None:
                        try:
                            row[field] = float(row[field])
                        except ValueError:
                            row[field] = None
                
                self.add(WMCapacity.from_dict(row))

    def to_csv(self, file_path: str) -> None:
        """Saves the collection to a CSV file."""
        if not self.records:
            logger.warning("Collection is empty. Nothing to write.")
            return

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = ['subject_id', 'k_score', 'd_prime', 'accuracy', 'reaction_time', 'source']
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for record in self.records:
                writer.writerow(record.to_dict())

    def get_subject_ids(self) -> List[str]:
        """Returns a list of all subject IDs in the collection."""
        return [r.subject_id for r in self.records]

    def get_k_scores(self) -> List[float]:
        """Returns a list of k-scores for subjects who have them."""
        return [r.k_score for r in self.records if r.k_score is not None]

    def get_d_primes(self) -> List[float]:
        """Returns a list of d-primes for subjects who have them."""
        return [r.d_prime for r in self.records if r.d_prime is not None]

    def __len__(self) -> int:
        return len(self.records)

    def __iter__(self):
        return iter(self.records)

def main():
    """
    Entry point for testing the WMCapacity model.
    Creates a sample collection, saves it, and reloads it to verify I/O.
    """
    import sys
    import os
    
    # Setup logging for this script
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Define output path relative to project root
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "wm_capacity_sample.csv"

    # Create a sample collection
    collection = WMCapacityCollection()
    
    # Add sample data (simulating what T015 would produce)
    sample_data = [
        {'subject_id': 'sub-001', 'k_score': 2.5, 'accuracy': 0.85, 'reaction_time': 450.2, 'source': 'Cowan K'},
        {'subject_id': 'sub-002', 'k_score': 3.1, 'accuracy': 0.92, 'reaction_time': 420.5, 'source': 'Cowan K'},
        {'subject_id': 'sub-003', 'd_prime': 2.8, 'accuracy': 0.88, 'reaction_time': 410.0, 'source': 'Signal Detection'},
        {'subject_id': 'sub-004', 'k_score': 1.9, 'accuracy': 0.75, 'reaction_time': 500.1, 'source': 'Cowan K'},
    ]

    for item in sample_data:
        collection.add(WMCapacity.from_dict(item))

    logger.info(f"Created collection with {len(collection)} valid records.")

    # Save to CSV
    collection.to_csv(str(output_file))
    logger.info(f"Saved collection to {output_file}")

    # Reload to verify
    reloaded = WMCapacityCollection()
    reloaded.from_csv(str(output_file))
    
    if len(reloaded) == len(collection):
        logger.info("Verification successful: Reloaded collection matches original.")
    else:
        logger.error("Verification failed: Mismatch in record count.")
        sys.exit(1)

    # Print summary
    print(f"\n--- Working Memory Capacity Summary ---")
    print(f"Total Subjects: {len(reloaded)}")
    print(f"Subjects with K-score: {len(reloaded.get_k_scores())}")
    print(f"Subjects with d': {len(reloaded.get_d_primes())}")
    if reloaded.get_k_scores():
        print(f"Mean K-score: {sum(reloaded.get_k_scores())/len(reloaded.get_k_scores()):.2f}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())