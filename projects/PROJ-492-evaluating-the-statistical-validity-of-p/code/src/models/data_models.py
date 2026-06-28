"""
Pydantic data models for A/B test audit pipeline.

Defines the core data structures:
- ABTestSummary: Extracted A/B test summary from web sources
- AuditRecord: Audit results including reconstruction and validation
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
import re


class ABTestSummary(BaseModel):
    """
    Represents an extracted A/B test summary from a public source.

    Contains the key metrics reported in the summary:
    - Sample sizes for control and treatment groups
    - Conversion rates or means for both groups
    - Reported p-value and effect size
    - Test type (binary/continuous)
    - Source metadata (URL, domain, publication year)
    """

    # Primary identifiers
    url: str = Field(..., description="Source URL of the A/B test summary")
    source_id: Optional[str] = Field(None, description="Repository or source identifier")

    # Sample sizes
    n_control: int = Field(..., ge=1, description="Sample size of control group")
    n_treatment: int = Field(..., ge=1, description="Sample size of treatment group")

    # For binary outcomes (conversion rates)
    baseline_rate: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Baseline conversion rate (control group)"
    )
    treatment_rate: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Treatment conversion rate (treatment group)"
    )

    # For continuous outcomes (means)
    control_mean: Optional[float] = Field(None, description="Mean for control group")
    treatment_mean: Optional[float] = Field(None, description="Mean for treatment group")
    control_std: Optional[float] = Field(None, ge=0.0, description="Standard deviation for control group")
    treatment_std: Optional[float] = Field(None, ge=0.0, description="Standard deviation for treatment group")

    # Reported statistical results
    reported_p_value: Optional[float] = Field(None, ge=0.0, le=1.0, description="Reported p-value")
    reported_effect_size: Optional[float] = Field(None, description="Reported effect size (absolute or relative)")
    effect_size_type: Optional[Literal["absolute", "relative", "percent"]] = Field(
        None,
        description="Type of effect size reported"
    )

    # Test type detection
    outcome_type: Literal["binary", "continuous", "unknown"] = Field(
        "unknown",
        description="Detected outcome type based on available metrics"
    )
    test_type: Optional[Literal["z-test", "t-test", "fisher", "chi-square", "unknown"]] = Field(
        None,
        description="Type of statistical test used"
    )

    # Source metadata
    domain: Optional[str] = Field(None, description="Domain extracted from URL")
    publication_year: Optional[int] = Field(
        None,
        ge=1900,
        le=2100,
        description="Publication year of the A/B test summary"
    )

    # Extraction metadata
    extracted_at: datetime = Field(default_factory=datetime.utcnow, description="Extraction timestamp")
    extraction_confidence: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for extraction quality"
    )

    # Validation flags
    missing_baseline: bool = Field(False, description="Whether baseline conversion rate is missing")
    sample_size_mismatch: bool = Field(False, description="Whether sample sizes are inconsistent")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if not url_pattern.match(v):
            raise ValueError('Invalid URL format')
        return v

    @field_validator('publication_year')
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        """Validate publication year range."""
        if v is not None and (v < 1900 or v > 2100):
            raise ValueError('Publication year must be between 1900 and 2100')
        return v

    @model_validator(mode='after')
    def validate_outcome_type(self) -> 'ABTestSummary':
        """
        Infer outcome type based on available metrics.
        Binary if rates are present, continuous if means/std are present.
        """
        has_rates = self.baseline_rate is not None and self.treatment_rate is not None
        has_means = self.control_mean is not None and self.treatment_mean is not None

        if has_rates and not has_means:
            self.outcome_type = "binary"
        elif has_means and not has_rates:
            self.outcome_type = "continuous"
        elif has_rates and has_means:
            # Prefer binary if both present (common case)
            self.outcome_type = "binary"
        else:
            self.outcome_type = "unknown"

        return self

    @model_validator(mode='after')
    def validate_sample_sizes(self) -> 'ABTestSummary':
        """Check for sample size mismatches (e.g., n_control == n_treatment when unlikely)."""
        if self.n_control == self.treatment and self.n_control < 100:
            # Small equal sample sizes might indicate data quality issues
            self.sample_size_mismatch = True
        return self

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        use_enum_values = True
        extra = "forbid"


class AuditRecord(BaseModel):
    """
    Represents the audit result for a single A/B test summary.

    Contains:
    - The original extracted summary
    - Reconstructed statistical values
    - Inconsistency flags and severity
    - Data quality warnings
    """

    # Reference to original summary
    summary_url: str = Field(..., description="URL of the audited A/B test summary")
    summary_id: Optional[str] = Field(None, description="Unique identifier for the summary")

    # Original extracted data (snapshot)
    original_summary: ABTestSummary = Field(..., description="Original extracted summary")

    # Reconstructed statistical values
    reconstructed_p_value: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Reconstructed p-value from raw metrics"
    )
    reconstructed_effect_size: Optional[float] = Field(
        None,
        description="Reconstructed effect size"
    )
    reconstruction_method: Optional[Literal["z-test", "t-test", "fisher", "baseline", "unknown"]] = Field(
        None,
        description="Method used for reconstruction"
    )

    # Inconsistency detection
    is_inconsistent: bool = Field(False, description="Whether the summary is statistically inconsistent")
    p_value_difference: Optional[float] = Field(
        None,
        description="Absolute difference between reported and reconstructed p-value"
    )
    effect_size_difference: Optional[float] = Field(
        None,
        description="Relative difference between reported and reconstructed effect size"
    )

    # Threshold-based flags (FR-004)
    p_value_flag: bool = Field(False, description="Flagged if |p_diff| > 0.05")
    effect_size_flag: bool = Field(False, description="Flagged if relative effect-size diff > 5%")

    # Data quality warnings
    data_quality_warnings: List[str] = Field(
        default_factory=list,
        description="List of data quality warnings (e.g., sample-size mismatch)"
    )
    missing_baseline_warning: bool = Field(False, description="Warning if baseline rate is missing")

    # Audit metadata
    audit_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Audit timestamp")
    audit_version: str = Field("1.0", description="Version of the audit logic")

    # Error codes (FR-007)
    error_codes: List[str] = Field(
        default_factory=list,
        description="List of error codes encountered during audit"
    )

    @field_validator('original_summary')
    @classmethod
    def validate_summary_url_match(cls, v: ABTestSummary, info) -> ABTestSummary:
        """Ensure summary URL matches record URL."""
        if 'summary_url' in info.data and v.url != info.data['summary_url']:
            raise ValueError('Summary URL does not match record URL')
        return v

    @model_validator(mode='after')
    def compute_inconsistency_flags(self) -> 'AuditRecord':
        """
        Compute inconsistency flags based on thresholds.
        Per FR-004: absolute p-difference > 0.05 OR relative effect-size > 5%
        """
        if self.p_value_difference is not None and abs(self.p_value_difference) > 0.05:
            self.p_value_flag = True
            self.is_inconsistent = True

        if self.effect_size_difference is not None and self.original_summary.reconstructed_effect_size is not None:
            if self.original_summary.reconstructed_effect_size != 0:
                relative_diff = abs(self.effect_size_difference / self.original_summary.reconstructed_effect_size)
                if relative_diff > 0.05:
                    self.effect_size_flag = True
                    self.is_inconsistent = True

        return self

    @model_validator(mode='after')
    def add_quality_warnings(self) -> 'AuditRecord':
        """Add data quality warnings based on summary properties."""
        if self.original_summary.missing_baseline:
            self.missing_baseline_warning = True
            self.data_quality_warnings.append("ERR-012: Missing baseline conversion rate")

        if self.original_summary.sample_size_mismatch:
            self.data_quality_warnings.append("ERR-013: Sample size mismatch detected")

        if self.original_summary.outcome_type == "unknown":
            self.data_quality_warnings.append("ERR-014: Unable to determine outcome type")

        return self

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        use_enum_values = True
        extra = "forbid"


# Convenience functions for type checking
def is_valid_ab_summary(obj: Any) -> bool:
    """Check if object is a valid ABTestSummary instance."""
    return isinstance(obj, ABTestSummary)


def is_valid_audit_record(obj: Any) -> bool:
    """Check if object is a valid AuditRecord instance."""
    return isinstance(obj, AuditRecord)
