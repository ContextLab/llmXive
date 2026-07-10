"""
Compliance Rule Engine (Task T026).

Implements the core logic for validating compliance logs against study rules:
- Social media usage must be <= 30 minutes
- News consumption must be 0 minutes
- Notifications must be disabled (flagged if enabled, but currently not a hard fail for compliance)

This module is designed to support the unit tests in tests/unit/test_compliance_rules.py (T023)
and the aggregation pipeline in code/pipeline/aggregate_compliance.py (T027).
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class ComplianceResult:
    """Result of a compliance check for a single daily log entry."""
    is_compliant: bool
    social_media_violation: bool
    news_violation: bool
    social_media_minutes: Optional[int] = None
    social_media_limit: int = 30
    news_minutes: Optional[int] = None
    notifications_enabled: Optional[bool] = None
    violation_reasons: List[str] = None

    def __post_init__(self):
        if self.violation_reasons is None:
            self.violation_reasons = []


def check_compliance_rules(log_entry: Dict[str, Any]) -> ComplianceResult:
    """
    Check a daily log entry against compliance rules.

    Args:
        log_entry: Dictionary containing:
            - social_media_minutes (int): Minutes spent on social media
            - news_minutes (int): Minutes spent reading news
            - notifications_enabled (bool): Whether notifications were enabled

    Returns:
        ComplianceResult object with validation status and specific violation flags.

    Raises:
        ValueError: If values are negative, non-numeric, or missing required keys.
    """
    # Extract values with validation
    try:
        social_media_raw = log_entry.get("social_media_minutes")
        news_raw = log_entry.get("news_minutes")
        notifications_raw = log_entry.get("notifications_enabled")

        if social_media_raw is None or news_raw is None:
            raise ValueError("Missing required keys: 'social_media_minutes' and 'news_minutes' are required.")

        social_media = int(social_media_raw)
        news = int(news_raw)
        
        # Handle boolean conversion carefully for various input types (str vs bool)
        if isinstance(notifications_raw, str):
            notifications = notifications_raw.lower() in ('true', '1', 'yes', 'enabled')
        elif notifications_raw is None:
            notifications = False # Default assumption if not provided
        else:
            notifications = bool(notifications_raw)

    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid value type in log entry: {e}")

    if social_media < 0 or news < 0:
        raise ValueError("Time values cannot be negative.")

    # Rule 1: Social media <= 30 minutes
    social_media_violation = social_media > 30
    
    # Rule 2: No news allowed (must be 0)
    news_violation = news > 0

    # Rule 3: Notifications (Informational/Flagging only, not a hard fail for 'is_compliant' 
    # based on standard strict interpretation unless specified otherwise. 
    # However, we flag it for analysis).
    notifications_violation = notifications

    is_compliant = not social_media_violation and not news_violation

    violation_reasons = []
    if social_media_violation:
        violation_reasons.append(f"Social media exceeded limit ({social_media} > {30} min)")
    if news_violation:
        violation_reasons.append(f"News consumption detected ({news} > 0 min)")
    if notifications_violation:
        violation_reasons.append("Notifications were enabled")

    return ComplianceResult(
        is_compliant=is_compliant,
        social_media_violation=social_media_violation,
        news_violation=news_violation,
        social_media_minutes=social_media,
        social_media_limit=30,
        news_minutes=news,
        notifications_enabled=notifications,
        violation_reasons=violation_reasons
    )