import os
import logging
from typing import List, Optional, Tuple

def scan_report_for_causal_language(report: str) -> bool:
    """
    Scans a report for causal language and returns True if any is found, False otherwise.
    """
    causal_triggers = ["causes", "leads to", "results in", "impacts", "affects"]
    for trigger in causal_triggers:
        if trigger in report.lower():
            return True
    return False

if __name__ == "__main__":
    # Example usage
    report_text = "This study shows that increased engagement leads to higher self-esteem."
    if scan_report_for_causal_language(report_text):
        print("Causal language detected!")
    else:
        print("No causal language detected.")