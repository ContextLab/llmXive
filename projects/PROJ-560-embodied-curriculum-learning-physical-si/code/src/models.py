from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import json

@dataclass
class DatasetRecord:
    """
    Represents a single record in the dataset.
    
    Attributes:
        pre_test_score: Score before instruction.
        post_test_score: Score after instruction.
        instruction_type: Type of instruction (e.g., 'embodied', 'static').
        covariates: Additional covariates.
        gain_score: Calculated gain score (post - pre).
    """
    pre_test_score: float
    post_test_score: float
    instruction_type: str
    covariates: Dict[str, Any] = field(default_factory=dict)
    gain_score: Optional[float] = None

@dataclass
class AnalysisResult:
    """
    Represents the result of a statistical analysis.
    
    Attributes:
        test_name: Name of the statistical test performed.
        statistic: The test statistic value.
        p_value: The p-value of the test.
        effect_size: Effect size (e.g., Cohen's d).
        confidence_interval: Confidence interval tuple.
        inference_framing: Framing of the inference (e.g., "associational").
    """
    test_name: str
    statistic: float
    p_value: float
    effect_size: float
    confidence_interval: tuple
    inference_framing: str

@dataclass
class SensitivitySweep:
    """
    Represents a sensitivity analysis sweep result.
    
    Attributes:
        threshold: The threshold value used for the sweep.
        n_participants: Number of participants in the analysis.
        effect_size_cohen_d: Effect size calculated.
        robustness_flag: Flag indicating if the result is robust.
    """
    threshold: float
    n_participants: int
    effect_size_cohen_d: float
    robustness_flag: bool