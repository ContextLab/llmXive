"""
Base data models for the prompt complexity evaluation project.

Defines Pydantic models for HumanEvalProblem, PromptVariant, GeneratedCode,
and AnalysisResult to ensure type safety and validation throughout the pipeline.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
import json


class ComplexityLabel(str, Enum):
    """Allowed complexity labels for prompt variants."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"
    DEGENERATE = "degenerate"


class ExecutionStatus(str, Enum):
    """Status of code execution against unit tests."""
    PASSED = "passed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"


class HumanEvalProblem(BaseModel):
    """
    Represents a single HumanEval problem instance.
    
    Attributes:
        problem_id: Unique identifier for the problem (e.g., 'HumanEval/0')
        prompt: The original problem description string
        canonical_solution: The reference solution code
        test: The test code to validate solutions
        entry_point: The function name to test
        metadata: Additional problem metadata
    """
    problem_id: str = Field(..., description="Unique identifier for the problem")
    prompt: str = Field(..., description="Original problem description")
    canonical_solution: str = Field(..., description="Reference solution code")
    test: str = Field(..., description="Test code for validation")
    entry_point: str = Field(..., description="Function name to test")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('problem_id')
    @classmethod
    def validate_problem_id(cls, v: str) -> str:
        if not v.startswith('HumanEval/'):
            raise ValueError(f"problem_id must start with 'HumanEval/', got: {v}")
        return v


class PromptVariant(BaseModel):
    """
    Represents a single variant of a prompt generated from a base problem.
    
    Attributes:
        variant_id: Unique identifier for this variant
        problem_id: Reference to the parent HumanEval problem
        complexity_label: The complexity category of this variant
        prompt_text: The actual prompt text sent to the LLM
        structural_elements: Count of structural elements (examples, constraints, etc.)
        token_count: Number of tokens in the prompt (using cl100k_base)
        generated_at: Timestamp of generation
        source_variant: Optional reference to the source variant if derived
        flags: Dictionary of any flags (e.g., 'manual_review')
    """
    variant_id: str = Field(..., description="Unique identifier for this variant")
    problem_id: str = Field(..., description="Reference to parent problem")
    complexity_label: ComplexityLabel = Field(..., description="Complexity category")
    prompt_text: str = Field(..., description="The actual prompt text")
    structural_elements: int = Field(..., ge=0, description="Count of structural elements")
    token_count: int = Field(..., ge=0, description="Token count using cl100k_base")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")
    source_variant: Optional[str] = Field(None, description="Source variant if derived")
    flags: Dict[str, Any] = Field(default_factory=dict, description="Flags for manual review, etc.")

    @field_validator('complexity_label')
    @classmethod
    def validate_complexity_label(cls, v: ComplexityLabel) -> ComplexityLabel:
        if v not in ComplexityLabel:
            raise ValueError(f"Invalid complexity label: {v}")
        return v

    @field_validator('token_count')
    @classmethod
    def validate_token_count(cls, v: int) -> int:
        if v < 0:
            raise ValueError("token_count cannot be negative")
        return v

    @model_validator(mode='after')
    def check_token_thresholds(self) -> 'PromptVariant':
        """Validate token count thresholds based on complexity label."""
        thresholds = {
            ComplexityLabel.SIMPLE: (0, 50),
            ComplexityLabel.MODERATE: (51, 150),
            ComplexityLabel.COMPLEX: (151, 300),
            ComplexityLabel.VERY_COMPLEX: (301, 500),
            ComplexityLabel.DEGENERATE: (501, None)
        }
        
        min_tokens, max_tokens = thresholds[self.complexity_label]
        if self.token_count < min_tokens:
            self.flags['threshold_warning'] = f"Token count {self.token_count} below expected min {min_tokens} for {self.complexity_label}"
        if max_tokens and self.token_count > max_tokens:
            self.flags['threshold_warning'] = f"Token count {self.token_count} above expected max {max_tokens} for {self.complexity_label}"
        
        return self


class GeneratedCode(BaseModel):
    """
    Represents code generated by an LLM for a specific prompt variant.
    
    Attributes:
        generation_id: Unique identifier for this generation
        variant_id: Reference to the prompt variant used
        problem_id: Reference to the original problem
        code_text: The generated code string
        completion_time: Time taken to generate (seconds)
        token_usage: Number of tokens used in the generation
        status: Execution status against unit tests
        execution_results: List of test results if executed
        static_analysis: Static analysis metrics (ruff, etc.)
        created_at: Timestamp of creation
    """
    generation_id: str = Field(..., description="Unique identifier for this generation")
    variant_id: str = Field(..., description="Reference to prompt variant")
    problem_id: str = Field(..., description="Reference to original problem")
    code_text: str = Field(..., description="Generated code string")
    completion_time: Optional[float] = Field(None, ge=0, description="Generation time in seconds")
    token_usage: Optional[int] = Field(None, ge=0, description="Tokens used in generation")
    status: Optional[ExecutionStatus] = Field(None, description="Execution status")
    execution_results: List[Dict[str, Any]] = Field(default_factory=list, description="List of test results")
    static_analysis: Dict[str, Any] = Field(default_factory=dict, description="Static analysis metrics")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    flags: Dict[str, Any] = Field(default_factory=dict, description="Flags for security, etc.")

    @field_validator('code_text')
    @classmethod
    def validate_code_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("code_text cannot be empty")
        return v


class AnalysisResult(BaseModel):
    """
    Represents the result of statistical analysis on generated code.
    
    Attributes:
        analysis_id: Unique identifier for this analysis
        problem_id: Reference to the problem (if per-problem)
        complexity_label: Complexity level analyzed
        metric_name: Name of the metric (e.g., 'pass_rate', 'token_count')
        metric_value: The calculated value
        test_statistic: Statistical test statistic (e.g., t-value, F-value)
        p_value: P-value from statistical test
        effect_size: Calculated effect size (e.g., Cohen's d)
        confidence_interval: Tuple of (lower, upper) bounds
        sample_size: Number of samples used
        model_type: Type of model used (e.g., 'LMM', 'ANOVA')
        covariates: List of covariates included in the model
        corrected_p_value: P-value after multiple comparison correction
        method: Statistical method used
        notes: Additional notes or warnings
        created_at: Timestamp of creation
    """
    analysis_id: str = Field(..., description="Unique identifier for this analysis")
    problem_id: Optional[str] = Field(None, description="Reference to problem if applicable")
    complexity_label: Optional[ComplexityLabel] = Field(None, description="Complexity level analyzed")
    metric_name: str = Field(..., description="Name of the metric")
    metric_value: float = Field(..., description="Calculated metric value")
    test_statistic: Optional[float] = Field(None, description="Test statistic value")
    p_value: Optional[float] = Field(None, ge=0, le=1, description="P-value")
    effect_size: Optional[float] = Field(None, description="Effect size value")
    confidence_interval: Optional[tuple] = Field(None, description="Confidence interval bounds")
    sample_size: Optional[int] = Field(None, ge=1, description="Sample size")
    model_type: Optional[str] = Field(None, description="Model type used")
    covariates: List[str] = Field(default_factory=list, description="List of covariates")
    corrected_p_value: Optional[float] = Field(None, ge=0, le=1, description="Corrected p-value")
    method: Optional[str] = Field(None, description="Statistical method")
    notes: List[str] = Field(default_factory=list, description="Additional notes")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

    @field_validator('p_value', 'corrected_p_value')
    @classmethod
    def validate_probability(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 0 or v > 1):
            raise ValueError(f"Probability value must be between 0 and 1, got: {v}")
        return v

    @field_validator('effect_size')
    @classmethod
    def validate_effect_size(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < -10 or v > 10):
            raise ValueError(f"Effect size seems unreasonable: {v}")
        return v


# Serialization helpers for JSON/Parquet compatibility
def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    """Convert a Pydantic model to a dictionary with JSON-serializable types."""
    data = model.model_dump()
    # Convert datetime to ISO string
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = value.isoformat()
        elif isinstance(value, Enum):
            data[key] = value.value
    return data


def models_to_json(models: List[BaseModel]) -> str:
    """Convert a list of Pydantic models to a JSON string."""
    return json.dumps([model_to_dict(m) for m in models], indent=2)