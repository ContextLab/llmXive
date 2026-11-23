from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
import re
import unicodedata

class Message(BaseModel):
    """
    Schema for a single text message with extracted emoji metrics.
    
    Attributes:
        message_id: Unique identifier for the message.
        text: The raw text content of the message.
        emoji_present: Boolean indicating if any emoji are present.
        emoji_count: Total number of emoji characters in the text.
        emoji_types: List of unique emoji code points (normalized) found in the text.
        text_length: Character count of the text.
        punctuation_count: Count of punctuation characters.
    """
    message_id: str = Field(..., description="Unique identifier for the message")
    text: str = Field(..., min_length=0, description="Raw text content")
    emoji_present: bool = Field(False, description="Whether any emoji are present")
    emoji_count: int = Field(0, ge=0, description="Total count of emoji")
    emoji_types: List[str] = Field(default_factory=list, description="List of unique emoji code points")
    text_length: int = Field(0, ge=0, description="Character count of text")
    punctuation_count: int = Field(0, ge=0, description="Count of punctuation characters")
    
    @field_validator('text')
    @classmethod
    def validate_text_type(cls, v):
        if not isinstance(v, str):
            raise ValueError("Text must be a string")
        return v
    
    @field_validator('emoji_types')
    @classmethod
    def validate_emoji_types(cls, v):
        if not isinstance(v, list):
            raise ValueError("emoji_types must be a list")
        if not all(isinstance(item, str) for item in v):
            raise ValueError("All items in emoji_types must be strings")
        return v
    
    def model_post_init(self, __context: Any) -> None:
        """Calculate derived fields if not provided."""
        if self.text_length == 0 and self.text:
            object.__setattr__(self, 'text_length', len(self.text))
        if self.punctuation_count == 0 and self.text:
            # Count punctuation using Unicode category
            self.punctuation_count = sum(1 for char in self.text if unicodedata.category(char).startswith('P'))

class AnalysisResult(BaseModel):
    """
    Schema for the result of a statistical analysis step.
    
    Attributes:
        analysis_id: Unique identifier for the analysis run.
        metric_name: Name of the metric analyzed (e.g., 'correlation', 'regression').
        effect_size: The calculated effect size (e.g., Beta, r).
        p_value: The p-value associated with the statistic.
        is_significant: Boolean indicating if the result is significant at alpha=0.05.
        confidence_interval_lower: Lower bound of the 95% CI.
        confidence_interval_upper: Upper bound of the 95% CI.
        sample_size: Number of samples used in the analysis.
        control_variables: List of variables controlled for in the analysis.
        metadata: Additional context or parameters used.
    """
    analysis_id: str = Field(..., description="Unique identifier for the analysis")
    metric_name: str = Field(..., description="Name of the metric")
    effect_size: float = Field(..., description="Calculated effect size")
    p_value: float = Field(..., ge=0.0, le=1.0, description="P-value")
    is_significant: bool = Field(..., description="Significance at alpha=0.05")
    confidence_interval_lower: Optional[float] = Field(None, description="Lower bound of 95% CI")
    confidence_interval_upper: Optional[float] = Field(None, description="Upper bound of 95% CI")
    sample_size: int = Field(..., ge=1, description="Sample size used")
    control_variables: List[str] = Field(default_factory=list, description="Variables controlled for")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('p_value')
    @classmethod
    def validate_p_value(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("P-value must be between 0 and 1")
        return v
    
    @field_validator('effect_size')
    @classmethod
    def validate_effect_size(cls, v):
        # Effect sizes can be negative (e.g., correlation)
        return float(v)
    
    @field_validator('is_significant')
    @classmethod
    def derive_significance(cls, v, info):
        # If not explicitly set, derive from p_value
        if v is None and 'p_value' in info.data:
            return info.data['p_value'] < 0.05
        return v
