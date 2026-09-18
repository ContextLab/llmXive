"""
CSV dataset loading for paired participant data (US3).

Loads experiment results from CSV files produced by the quality assessment pipeline
and formats them for statistical analysis. Handles paired within-subject data structure.

Dependencies:
- data/models.py: Condition, ProblemSource enums
- config/settings.py: Configuration access
"""
import os
import sys
import csv
import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Iterator
from pathlib import Path
from dataclasses import dataclass, field

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.models import Condition, ProblemSource
from config.settings import get_datasets_config

logger = logging.getLogger(__name__)

@dataclass
class PairedObservation:
    """A single paired observation for within-subject analysis."""
    participant_id: str
    problem_id: str
    condition: str
    time_seconds: float
    pass_rate: float
    complexity: int
    coverage: float
    static_warnings: int
    submission_id: str
    problem_source: str
    task_order: int  # 1 for first condition, 2 for second (counterbalanced)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'participant_id': self.participant_id,
            'problem_id': self.problem_id,
            'condition': self.condition,
            'time_seconds': self.time_seconds,
            'pass_rate': self.pass_rate,
            'complexity': self.complexity,
            'coverage': self.coverage,
            'static_warnings': self.static_warnings,
            'submission_id': self.submission_id,
            'problem_source': self.problem_source,
            'task_order': self.task_order
        }

@dataclass
class PairedDataset:
    """Container for paired participant data ready for statistical analysis."""
    observations: List[PairedObservation]
    metadata: Dict[str, Any]
    
    def group_by_participant(self) -> Dict[str, List[PairedObservation]]:
        """Group observations by participant ID."""
        groups: Dict[str, List[PairedObservation]] = {}
        for obs in self.observations:
            if obs.participant_id not in groups:
                groups[obs.participant_id] = []
            groups[obs.participant_id].append(obs)
        return groups
    
    def get_pairs(self) -> Iterator[Tuple[PairedObservation, PairedObservation]]:
        """Yield (condition_A, condition_B) pairs for each participant/problem."""
        groups = self.group_by_participant()
        for pid, obs_list in groups.items():
            # Sort by problem_id and condition to ensure consistent pairing
            sorted_obs = sorted(obs_list, key=lambda x: (x.problem_id, x.condition))
            # Group by problem_id to find pairs
            problem_groups: Dict[str, List[PairedObservation]] = {}
            for obs in sorted_obs:
                if obs.problem_id not in problem_groups:
                    problem_groups[obs.problem_id] = []
                problem_groups[obs.problem_id].append(obs)
            
            for pid_obs_list in problem_groups.values():
                if len(pid_obs_list) == 2:
                    # Identify baseline and LLM-assisted
                    baseline = None
                    assisted = None
                    for obs in pid_obs_list:
                        if obs.condition == 'baseline':
                            baseline = obs
                        elif obs.condition == 'llm_assisted':
                            assisted = obs
                    
                    if baseline and assisted:
                        yield (baseline, assisted)

class DataLoaderError(Exception):
    """Custom exception for data loading errors."""
    pass

def load_csv_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load a single CSV file and return rows as dictionaries.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        List of row dictionaries.
        
    Raises:
        DataLoaderError: If file cannot be read or parsed.
    """
    if not os.path.exists(file_path):
        raise DataLoaderError(f"File not found: {file_path}")
    
    rows = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except Exception as e:
        raise DataLoaderError(f"Failed to parse CSV {file_path}: {e}")
    
    if not rows:
        logger.warning(f"CSV file {file_path} is empty")
    
    return rows

def parse_condition(condition_str: str) -> Condition:
    """Parse condition string to Condition enum."""
    condition_str = condition_str.lower().strip()
    if condition_str in ('baseline', 'control'):
        return Condition.BASELINE
    elif condition_str in ('llm_assisted', 'treatment', 'llm'):
        return Condition.LLM_ASSISTED
    else:
        raise ValueError(f"Unknown condition: {condition_str}")

def parse_problem_source(source_str: str) -> ProblemSource:
    """Parse problem source string to ProblemSource enum."""
    source_str = source_str.lower().strip()
    if source_str == 'humaneval':
        return ProblemSource.HUMANEVAL
    elif source_str == 'codeforces':
        return ProblemSource.CODEFORCES
    else:
        raise ValueError(f"Unknown problem source: {source_str}")

def coerce_value(value: str, target_type: type, default: Any = None) -> Any:
    """Safely coerce a string value to a target type."""
    if value is None or value == '':
        return default
    try:
        if target_type == float:
            return float(value)
        elif target_type == int:
            return int(value)
        elif target_type == str:
            return str(value)
        else:
            return target_type(value)
    except (ValueError, TypeError):
        return default

def load_paired_dataset(
    data_dir: Optional[str] = None,
    filename_pattern: str = "quality_metrics.csv"
) -> PairedDataset:
    """
    Load paired participant data from CSV files in the data directory.
    
    This function aggregates quality metrics from the US2 pipeline and structures
    them for within-subject statistical analysis (US3).
    
    Args:
        data_dir: Directory containing CSV files. Defaults to configured data path.
        filename_pattern: Pattern for CSV files to load.
        
    Returns:
        PairedDataset containing structured observations and metadata.
        
    Raises:
        DataLoaderError: If no data can be loaded or required columns are missing.
    """
    if data_dir is None:
        config = get_datasets_config()
        data_dir = config.get('output_path', 'data')
    
    data_path = Path(data_dir)
    if not data_path.exists():
        raise DataLoaderError(f"Data directory not found: {data_path}")
    
    # Find CSV files
    csv_files = list(data_path.glob(f"*{filename_pattern}"))
    if not csv_files:
        # Fallback to common names
        csv_files = list(data_path.glob("quality_metrics*.csv"))
        if not csv_files:
            csv_files = list(data_path.glob("*.csv"))
    
    if not csv_files:
        raise DataLoaderError(f"No CSV files found in {data_path}")
    
    logger.info(f"Found {len(csv_files)} CSV files to process")
    
    all_rows = []
    for csv_file in csv_files:
        try:
            rows = load_csv_file(str(csv_file))
            all_rows.extend(rows)
            logger.info(f"Loaded {len(rows)} rows from {csv_file.name}")
        except DataLoaderError as e:
            logger.warning(f"Skipping file {csv_file.name}: {e}")
            continue
    
    if not all_rows:
        raise DataLoaderError("No valid data rows found in any CSV file")
    
    # Required columns
    required_cols = {
        'participant_id', 'problem_id', 'condition', 
        'time_seconds', 'pass_rate', 'submission_id'
    }
    available_cols = set(all_rows[0].keys()) if all_rows else set()
    missing_cols = required_cols - available_cols
    
    if missing_cols:
        raise DataLoaderError(f"Missing required columns: {missing_cols}")
    
    # Convert rows to PairedObservation
    observations = []
    for idx, row in enumerate(all_rows):
        try:
            obs = PairedObservation(
                participant_id=row['participant_id'],
                problem_id=row['problem_id'],
                condition=row['condition'],
                time_seconds=coerce_value(row.get('time_seconds'), float, 0.0),
                pass_rate=coerce_value(row.get('pass_rate'), float, 0.0),
                complexity=coerce_value(row.get('complexity'), int, 1),
                coverage=coerce_value(row.get('coverage'), float, 0.0),
                static_warnings=coerce_value(row.get('static_warnings'), int, 0),
                submission_id=row['submission_id'],
                problem_source=row.get('problem_source', 'humaneval'),
                task_order=coerce_value(row.get('task_order'), int, 1)
            )
            observations.append(obs)
        except Exception as e:
            logger.warning(f"Skipping row {idx}: {e}")
            continue
    
    if not observations:
        raise DataLoaderError("No valid observations could be parsed from data")
    
    # Compute metadata
    unique_participants = len(set(o.participant_id for o in observations))
    unique_problems = len(set(o.problem_id for o in observations))
    conditions = set(o.condition for o in observations)
    
    metadata = {
        'total_observations': len(observations),
        'unique_participants': unique_participants,
        'unique_problems': unique_problems,
        'conditions': list(conditions),
        'sources': list(set(o.problem_source for o in observations)),
        'load_timestamp': datetime.now().isoformat(),
        'source_files': [str(f) for f in csv_files]
    }
    
    logger.info(f"Loaded dataset: {unique_participants} participants, "
               f"{unique_problems} problems, {len(observations)} observations")
    
    return PairedDataset(observations=observations, metadata=metadata)

def verify_pairing_completeness(dataset: PairedDataset) -> Dict[str, Any]:
    """
    Verify that the dataset has complete pairs for within-subject analysis.
    
    Args:
        dataset: The loaded PairedDataset.
        
    Returns:
        Dictionary with completeness statistics.
    """
    groups = dataset.group_by_participant()
    complete_pairs = 0
    incomplete_participants = []
    
    for pid, obs_list in groups.items():
        # Check if each problem has both conditions
        problem_conditions: Dict[str, set] = {}
        for obs in obs_list:
            if obs.problem_id not in problem_conditions:
                problem_conditions[obs.problem_id] = set()
            problem_conditions[obs.problem_id].add(obs.condition)
        
        # Count problems with both conditions
        for pid_obs_list in problem_conditions.values():
            if 'baseline' in pid_obs_list and 'llm_assisted' in pid_obs_list:
                complete_pairs += 1
            else:
                if pid not in incomplete_participants:
                    incomplete_participants.append(pid)
    
    total_unique_problems = dataset.metadata['unique_problems']
    expected_pairs = dataset.metadata['unique_participants'] * total_unique_problems
    
    return {
        'complete_pairs': complete_pairs,
        'total_possible_pairs': expected_pairs,
        'completeness_rate': complete_pairs / expected_pairs if expected_pairs > 0 else 0.0,
        'incomplete_participants': incomplete_participants,
        'total_participants': len(groups)
    }

def main():
    """Main entry point for CLI usage."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load dataset
        dataset = load_paired_dataset()
        
        # Verify pairing
        completeness = verify_pairing_completeness(dataset)
        
        print(f"\nDataset Summary:")
        print(f"  Total Observations: {dataset.metadata['total_observations']}")
        print(f"  Unique Participants: {dataset.metadata['unique_participants']}")
        print(f"  Unique Problems: {dataset.metadata['unique_problems']}")
        print(f"  Conditions: {dataset.metadata['conditions']}")
        
        print(f"\nPairing Completeness:")
        print(f"  Complete Pairs: {completeness['complete_pairs']}")
        print(f"  Completeness Rate: {completeness['completeness_rate']:.2%}")
        
        if completeness['incomplete_participants']:
            print(f"  Incomplete Participants: {completeness['incomplete_participants']}")
        
        # Demonstrate pairing iteration
        print(f"\nSample Pairs:")
        pair_count = 0
        for baseline, assisted in dataset.get_pairs():
            if pair_count < 3:
                print(f"  Participant {baseline.participant_id}, Problem {baseline.problem_id}:")
                print(f"    Baseline: {baseline.time_seconds:.2f}s, Pass: {baseline.pass_rate:.2f}")
                print(f"    Assisted: {assisted.time_seconds:.2f}s, Pass: {assisted.pass_rate:.2f}")
                print(f"    Delta: {baseline.time_seconds - assisted.time_seconds:.2f}s")
            pair_count += 1
        
        if pair_count == 0:
            print("  No complete pairs found in dataset.")
        
        print(f"\nTotal pairs available for analysis: {pair_count}")
        
        return 0
      
    except DataLoaderError as e:
        logger.error(f"Data loading failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())