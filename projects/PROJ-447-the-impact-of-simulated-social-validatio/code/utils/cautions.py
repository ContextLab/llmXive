"""
Causal language scanner module.

This module scans text reports for causal language trigger words
and raises an error if any are found.
"""

import os
import logging
from typing import List, Optional, Tuple

from utils.constants import get_causal_triggers

logger = logging.getLogger(__name__)


def scan_report_for_causal_language(
    report_text: str,
    triggers: Optional[List[str]] = None
) -> List[str]:
    """
    Scan a report string for causal language trigger words.

    Args:
        report_text: The text to scan.
        triggers: Optional list of trigger words. Defaults to config.

    Returns:
        List of trigger words found in the report.
    """
    if triggers is None:
        triggers = get_causal_triggers()

    found_triggers = []
    lower_text = report_text.lower()

    for trigger in triggers:
        if trigger.lower() in lower_text:
            found_triggers.append(trigger)

    if found_triggers:
        logger.warning(f"Causal language detected: {found_triggers}")

    return found_triggers
