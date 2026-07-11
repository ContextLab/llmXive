"""
Base models and entities for the code generation productivity experiment.

These classes define the schema for the SQLite database and serve as
the primary data structures for the experiment pipeline.

Matches the entities defined in data-model.md:
- Participant
- Session
- Problem
- Submission
- Metric
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid
import hashlib


class Condition(Enum):
    """Experiment condition types."""
    BASELINE = "baseline"
    LLM_ASSISTED = "llm_assisted"


class ProblemSource(Enum):
    """Source of the coding problem."""
    HUMANEVAL = "humaneval"
    CODEFORCES = "codeforces"


@dataclass
class Participant:
    """
    Represents a study participant.
    
    Attributes:
        participant_id: Unique identifier (SHA-256 hash of original ID for anonymity)
        recruitment_date: Date when participant was recruited
        years_experience: Years of programming experience (>= 1 required)
        primary_language: Primary programming language (e.g., 'python', 'java')
        consent_verified: Whether IRB consent has been verified
        consent_timestamp: Timestamp of consent verification
    """
    participant_id: str
    recruitment_date: datetime
    years_experience: int
    primary_language: str
    consent_verified: bool = False
    consent_timestamp: Optional[datetime] = None
    
    @classmethod
    def create_anonymous_id(cls, raw_id: str, salt: str = "") -> str:
        """Create an anonymous participant ID using SHA-256."""
        data = f"{raw_id}{salt}".encode('utf-8')
        return hashlib.sha256(data).hexdigest()


@dataclass
class Session:
    """
    Represents a single experimental session for a participant.
    
    Attributes:
        session_id: Unique session identifier
        participant_id: Reference to the participant
        condition: The experimental condition (baseline or llm_assisted)
        start_time: When the session started
        end_time: When the session ended (optional, may be null if incomplete)
        seed: Random seed used for problem ordering in this session
        counterbalance_order: Order index for counterbalancing
        completed: Whether the session was completed
    """
    session_id: str
    participant_id: str
    condition: Condition
    start_time: datetime
    end_time: Optional[datetime] = None
    seed: int = 0
    counterbalance_order: int = 0
    completed: bool = False
    
    def __post_init__(self):
        if not self.session_id:
            self.session_id = str(uuid.uuid4())


@dataclass
class Problem:
    """
    Represents a coding problem from a dataset.
    
    Attributes:
        problem_id: Unique problem identifier (dataset-specific)
        source: Problem source (HumanEval or Codeforces)
        language: Programming language (e.g., 'python', 'java')
        prompt: Problem description/prompt text
        canonical_solution: Reference solution for pass rate calculation
        test_suite: Test cases for validation
        difficulty: Difficulty level (e.g., 'easy', 'medium', 'hard')
        estimated_time_min: Estimated time to solve in minutes
    """
    problem_id: str
    source: ProblemSource
    language: str
    prompt: str
    canonical_solution: Optional[str] = None
    test_suite: Optional[List[Dict[str, Any]]] = None
    difficulty: str = "medium"
    estimated_time_min: int = 10


@dataclass
class Submission:
    """
    Represents a code submission by a participant for a problem.
    
    Attributes:
        submission_id: Unique submission identifier
        session_id: Reference to the session
        problem_id: Reference to the problem
        code: The submitted code
        timestamp: When the submission was made
        condition: The condition under which submission was made
        syntax_valid: Whether the code passed syntax validation
        error_message: Error message if syntax invalid or execution failed
        completion_time_sec: Time taken to complete the problem (seconds)
    """
    submission_id: str
    session_id: str
    problem_id: str
    code: str
    timestamp: datetime
    condition: Condition
    syntax_valid: bool = True
    error_message: Optional[str] = None
    completion_time_sec: Optional[float] = None
    
    def __post_init__(self):
        if not self.submission_id:
            self.submission_id = str(uuid.uuid4())


@dataclass
class Metric:
    """
    Represents quality metrics computed for a submission.
    
    Attributes:
        metric_id: Unique metric identifier
        submission_id: Reference to the submission
        pass_rate: Percentage of tests passed (0.0 to 1.0)
        cyclomatic_complexity: Cyclomatic complexity score (integer >= 1)
        test_coverage: Test coverage percentage (0.0 to 100.0)
        static_warnings: Number of static analysis warnings
        total_quality_score: Aggregated quality score (0.0 to 1.0)
        computed_at: When metrics were computed
        notes: Additional notes or error messages
    """
    submission_id: str
    pass_rate: float = 0.0
    cyclomatic_complexity: int = 1
    test_coverage: float = 0.0
    static_warnings: int = 0
    total_quality_score: float = 0.0
    computed_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        if not self.computed_at:
            self.computed_at = datetime.utcnow()
        
        # Compute total quality score as weighted average
        # Weights: pass_rate (50%), coverage (30%), inverse complexity (10%), inverse warnings (10%)
        complexity_score = max(0, 1.0 - (self.cyclomatic_complexity - 1) / 50.0)  # Normalize
        warning_score = max(0, 1.0 - self.static_warnings / 20.0)  # Normalize
        
        self.total_quality_score = (
            self.pass_rate * 0.5 +
            (self.test_coverage / 100.0) * 0.3 +
            complexity_score * 0.1 +
            warning_score * 0.1
        )
        self.total_quality_score = min(1.0, max(0.0, self.total_quality_score))