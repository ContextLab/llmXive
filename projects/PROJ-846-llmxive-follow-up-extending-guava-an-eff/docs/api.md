# llmXive API Reference

This document provides function signatures and usage examples for the llmXive automated science pipeline.

## Data Models (`code/data/models.py`)

### Enumerations

```python
class FailureType(Enum):
 """Types of task failures."""
 GEOMETRIC = "geometric"
 SEMANTIC = "semantic"
 PERCEPTION = "perception"
 LATENCY = "latency"
 UNKNOWN = "unknown"

class PerceptionQuality(Enum):
 """Quality levels for perception logs."""
 HIGH = "high"
 MEDIUM = "medium"
 LOW = "low"
 MISSING = "missing"
```

### Data Classes

```python
class SymbolicObservation(BaseModel):
 """Symbolic representation of a single frame."""
 frame_id: int
 timestamp: float
 objects: List[Dict[str, Any]]
 scene_empty: bool = False

class Trajectory(BaseModel):
 """A sequence of symbolic observations."""
 trajectory_id: str
 task_name: str
 observations: List[SymbolicObservation]
 start_time: datetime
 end_time: datetime

class TaskOutcome(BaseModel):
 """Result of an agent's execution on a task."""
 trajectory_id: str
 agent_name: str
 success: bool
 steps: int
 failure_category: Optional[FailureType] = None
 latency_ms: Optional[float] = None
 timestamp: datetime

class PerceptionLog(BaseModel):
 """Log of perception system performance."""
 timestamp: float
 detected_objects: List[Dict[str, Any]]
 confidence_scores: List[float]
 object_missing_if_visible: bool
 latency_ms: float
```

### Serialization Functions

```python
def serialize_trajectory(trajectory: Trajectory) -> Dict[str, Any]:...
def serialize_outcome(outcome: TaskOutcome) -> Dict[str, Any]:...
def serialize_perception_log(log: PerceptionLog) -> Dict[str, Any]:...
```

---

## Data Pipeline (`code/data/`)

### `download_guava.py`

```python
def calculate_sha256(file_path: Path) -> str:
 """Calculate SHA256 hash of a file."""

def download_guava_dataset(output_dir: Path) -> Dict[str, str]:
 """Download Guava dataset and return checksums."""

def main():
 """Entry point for dataset download."""
```

### `verify_ground_truth.py`

```python
def scan_file_for_keys(file_path: Path, keys: List[str]) -> bool:
 """Check if a JSON file contains specific keys."""

def find_ground_truth_annotations(data_dir: Path) -> Optional[Path]:
 """Locate ground truth annotations in raw data directory."""

def verify_ground_truth(data_dir: Path) -> Path:
 """Verify and copy ground truth annotations, raising if missing."""

def main():
 """Entry point for ground truth verification."""
```

### `transform_symbolic.py`

```python
class YOLOv8ONNX:
 """YOLOv8 ONNX runtime wrapper."""
 def __init__(self, model_path: str):...
 def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:...

class SymbolicTransformer:
 """Transforms raw trajectories to symbolic format."""
 def __init__(self, yolo_model: YOLOv8ONNX):...
 def transform_frame(self, image: np.ndarray, frame_id: int) -> SymbolicObservation:...
 def process_trajectory(self, trajectory_path: Path) -> Trajectory:...

def find_trajectories(data_dir: Path) -> List[Path]:
 """Find all trajectory directories."""

def main():
 """Entry point for symbolic transformation pipeline."""
```

### `validate_perception.py`

```python
def calculate_iou(bbox1: List[int], bbox2: List[int]) -> float:
 """Calculate Intersection over Union between two bounding boxes."""

def calculate_metrics_from_ground_truth(predictions: List, ground_truth: List) -> Dict[str, float]:
 """Calculate precision, recall, and mAP from predictions and ground truth."""

def validate_transformation_time(input_dir: Path, output_dir: Path, max_time_ms: float = 150) -> bool:
 """Validate that transformation meets latency constraints."""

def main():
 """Entry point for perception validation."""
```

---

## Utilities (`code/utils/`)

### `config.py`

```python
def initialize_paths(project_root: Path) -> Dict[str, Path]:
 """Initialize and return all project paths."""

def get_path(key: str) -> Path:
 """Get a specific path by key."""

def set_hyperparameter(key: str, value: Any) -> None:
 """Set a hyperparameter in global config."""

def get_hyperparameter(key: str, default: Any = None) -> Any:
 """Get a hyperparameter value."""

def set_global_seed(seed: int) -> None:
 """Set random seeds for reproducibility."""

def ensure_directories() -> None:
 """Create all required directories."""

def get_config_summary() -> Dict[str, Any]:
 """Return a summary of current configuration."""
```

### `exceptions.py`

```python
class LlmXiveError(Exception):...
class DatasetUnavailableError(LlmXiveError):...
class PerceptionInferenceError(LlmXiveError):...
class SymbolicTransformationError(LlmXiveError):...
class ValidationThresholdError(LlmXiveError):...
class BaselineUnavailableError(LlmXiveError):...
class GroundTruthSchemaMissingError(LlmXiveError):...
class EnvironmentConfigError(LlmXiveError):...
```

### `logger.py`

```python
def log_perception_ground_truth(
 timestamp: float,
 detected_objects: List[Dict[str, Any]],
 confidence_scores: List[float],
 object_missing_if_visible: bool
) -> None:
 """Append a perception log entry to the artifacts log."""

def log_latency(
 frame_id: int,
 latency_ms: float,
 trajectory_id: str
) -> None:
 """Append latency measurement to the perception log."""

def get_current_log_stats() -> Dict[str, Any]:
 """Get statistics from the current perception log."""

def clear_log() -> None:
 """Clear the perception log file."""
```

### `state_manager.py`

```python
def calculate_file_hash(file_path: Path) -> str:
 """Calculate SHA256 hash of a file."""

def get_all_files(directory: Path) -> List[Path]:
 """Recursively get all files in a directory."""

def generate_state_hash(files: List[Path]) -> str:
 """Generate a hash representing the state of all files."""

def update_state_file(state_path: Path, artifact_hashes: Dict[str, str]) -> None:
 """Update the state YAML file atomically."""

def verify_state_integrity(state_path: Path) -> bool:
 """Verify the integrity of the state file."""

def get_state_summary(state_path: Path) -> Dict[str, Any]:
 """Get a summary of the current project state."""

def main():
 """Entry point for state management."""
```

### `environment_config.py`

```python
def detect_cpu_count() -> int:
 """Detect the number of available CPU cores."""

def verify_cpu_only_constraint() -> bool:
 """Verify the system is running in CPU-only mode."""

def configure_torch_for_cpu() -> None:
 """Configure PyTorch to use CPU only."""

def enforce_cpu_only() -> None:
 """Enforce CPU-only execution, raising if GPU is detected."""

def get_environment_summary() -> Dict[str, Any]:
 """Get a summary of the current environment configuration."""
```

---

## Models (`code/models/`)

### `train_llm.py`

```python
class SymbolicDataset(Dataset):
 """Dataset wrapper for symbolic trajectories."""

def load_symbolic_dataset(data_dir: Path) -> SymbolicDataset:
 """Load the symbolic dataset from disk."""

def prepare_training_data(dataset: SymbolicDataset) -> List[Dict[str, Any]]:
 """Prepare data for LLM training."""

def setup_model_and_tokenizer(model_name: str) -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
 """Load model and tokenizer."""

def setup_lora(model: PreTrainedModel) -> LoraModel:
 """Configure LoRA adapters."""

class TrainingCheckpointer:
 """Handles model checkpointing during training."""

def train_model(
 model: PreTrainedModel,
 train_data: List[Dict[str, Any]],
 output_dir: Path,
 max_steps: int = 1000
) -> Dict[str, float]:
 """Perform LoRA fine-tuning."""

def main():
 """Entry point for model training."""
```

### `inference_symbolic.py`

```python
class SymbolicGuavaAgent:
 """The fine-tuned Symbolic-Guava agent."""
 def __init__(self, model_path: str):...
 def act(self, observation: SymbolicObservation) -> str:...

def load_held_out_trajectories(data_dir: Path) -> List[Trajectory]:
 """Load held-out test trajectories."""

def evaluate_agent(
 agent: SymbolicGuavaAgent,
 trajectories: List[Trajectory]
) -> List[TaskOutcome]:
 """Run evaluation on a set of trajectories."""

def run_symbolic_evaluation() -> List[TaskOutcome]:
 """Run the full symbolic evaluation pipeline."""

def main():
 """Entry point for symbolic inference."""
```

### `inference_baseline.py`

```python
class BaselineVisualAgent:
 """The Baseline-Guava (Visual) agent."""
 def __init__(self, model_path: str):...
 def act(self, observation: np.ndarray) -> str:...

def run_baseline_evaluation(
 trajectories: List[Trajectory]
) -> List[TaskOutcome]:
 """Run evaluation using the visual baseline."""

def main():
 """Entry point for baseline inference."""
```

### `inference_oracle.py`

```python
class OracleSymbolicAgent:
 """Oracle agent using ground-truth actions."""
 def __init__(self, ground_truth_path: Path):...
 def act(self, observation: SymbolicObservation) -> str:...

def run_oracle_evaluation(
 trajectories: List[Trajectory]
) -> List[TaskOutcome]:
 """Run evaluation using the oracle agent."""

def main():
 """Entry point for oracle inference."""
```

---

## Analysis (`code/analysis/`)

### `stats_test.py`

```python
def load_evaluation_outcomes(file_path: Path) -> List[TaskOutcome]:
 """Load evaluation outcomes from a JSON file."""

def extract_success_vector(outcomes: List[TaskOutcome]) -> List[int]:
 """Extract binary success vector from outcomes."""

def run_permutation_test(
 vector_a: List[int],
 vector_b: List[int],
 n_iterations: int = 10000
) -> float:
 """Run a permutation test and return p-value."""

def check_convergence(p_values: List[float], threshold: float = 0.01) -> bool:
 """Check if p-value has converged."""

def main():
 """Entry point for statistical testing."""
```

### `failure_categorizer.py`

```python
def load_task_outcomes(file_path: Path) -> List[TaskOutcome]:
 """Load task outcomes."""

def load_perception_log(file_path: Path) -> List[PerceptionLog]:
 """Load perception logs."""

def categorize_failure(
 outcome: TaskOutcome,
 perception_log: Optional[PerceptionLog]
) -> FailureType:
 """Categorize a single failure."""

def categorize_all_failures(outcomes: List[TaskOutcome], log_path: Path) -> List[TaskOutcome]:
 """Categorize failures for all outcomes."""

def write_categorized_outcomes(outcomes: List[TaskOutcome], output_path: Path) -> None:
 """Write categorized outcomes to disk."""

def main():
 """Entry point for failure categorization."""
```

### `semantic_failure_analyzer.py`

```python
def load_categorized_outcomes(file_path: Path) -> List[TaskOutcome]:
 """Load categorized outcomes."""

def calculate_semantic_ratio(outcomes: List[TaskOutcome]) -> float:
 """Calculate the ratio of semantic failures to total non-perception/latency failures."""

def write_verification_result(ratio: float, output_path: Path) -> None:
 """Write semantic ratio verification result."""

def write_research_conclusion(ratio: float, output_path: Path) -> None:
 """Write research conclusion based on SC-004 threshold."""

def main():
 """Entry point for semantic failure analysis."""
```

### `latency_failure_flagger.py`

```python
def get_latency_for_task(outcome: TaskOutcome) -> float:
 """Get latency for a specific task."""

def flag_latency_induced_failures(
 outcomes: List[TaskOutcome],
 threshold_ms: float = 150
) -> List[TaskOutcome]:
 """Flag outcomes with latency-induced failures."""

def write_flagged_outcomes(outcomes: List[TaskOutcome], output_path: Path) -> None:
 """Write flagged outcomes to disk."""

def main():
 """Entry point for latency flagging."""
```

### `latency_filter.py`

```python
def is_latency_failure(outcome: TaskOutcome) -> bool:
 """Check if an outcome is a latency failure."""

def filter_latency_failures(outcomes: List[TaskOutcome]) -> List[TaskOutcome]:
 """Filter out latency-induced failures."""

def write_filtered_outcomes(outcomes: List[TaskOutcome], output_path: Path) -> None:
 """Write filtered outcomes to disk."""

def main():
 """Entry point for latency filtering."""
```

### `latency_exclusion_verifier.py`

```python
def load_filtered_outcomes(file_path: Path) -> List[TaskOutcome]:
 """Load filtered outcomes."""

def count_latency_failures(outcomes: List[TaskOutcome]) -> int:
 """Count the number of latency failures."""

def verify_exclusion_logic(
 all_outcomes: List[TaskOutcome],
 filtered_outcomes: List[TaskOutcome]
) -> bool:
 """Verify that exclusion logic was applied correctly."""

def write_verification_result(is_valid: bool, output_path: Path) -> None:
 """Write verification result."""

def main():
 """Entry point for exclusion verification."""
```

### `oracle_comparison.py`

```python
def compare_agents(
 symbolic_outcomes: List[TaskOutcome],
 oracle_outcomes: List[TaskOutcome]
) -> Dict[str, Any]:
 """Compare symbolic and oracle performance."""

def write_comparison_results(results: Dict[str, Any], output_path: Path) -> None:
 """Write comparison results to disk."""

def main():
 """Entry point for oracle comparison."""
```

### `evaluation_results_generator.py`

```python
def calculate_success_rate(outcomes: List[TaskOutcome]) -> float:
 """Calculate success rate from outcomes."""

def calculate_step_efficiency(outcomes: List[TaskOutcome]) -> float:
 """Calculate average steps per success."""

def aggregate_failure_distribution(outcomes: List[TaskOutcome]) -> Dict[str, int]:
 """Aggregate failure counts by category."""

def load_stats_test_results(file_path: Path) -> Dict[str, Any]:
 """Load statistical test results."""

def load_symbolic_outcomes(file_path: Path) -> List[TaskOutcome]:
 """Load symbolic agent outcomes."""

def load_baseline_outcomes(file_path: Path) -> List[TaskOutcome]:
 """Load baseline agent outcomes."""

def load_oracle_outcomes(file_path: Path) -> List[TaskOutcome]:
 """Load oracle agent outcomes."""

def build_evaluation_summary(
 symbolic: List[TaskOutcome],
 baseline: List[TaskOutcome],
 oracle: List[TaskOutcome],
 stats: Dict[str, Any]
) -> Dict[str, Any]:
 """Build a comprehensive evaluation summary."""

def write_evaluation_results(summary: Dict[str, Any], output_path: Path) -> None:
 """Write final evaluation results to disk."""

def main():
 """Entry point for results generation."""
```

---

## Git Operations (`code/`)

```python
def run_git_command(command: List[str]) -> str:
 """Run a git command and return output."""

def stage_all_files() -> None:
 """Stage all changes in the repository."""

def commit_changes(message: str) -> str:
 """Commit staged changes and return commit hash."""

def add_remote(name: str, url: str) -> None:
 """Add a remote repository."""

def main():
 """Entry point for git operations."""
```