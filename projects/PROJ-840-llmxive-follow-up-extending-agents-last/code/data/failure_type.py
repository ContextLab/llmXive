"""
Failure type enumeration for ALE synthetic trace generation.

This module defines the `FailureType` enum used to label execution traces
with their ground‑truth failure mode. It is imported by the data generator
script (`code/data/generator.py`) to ensure a consistent, type‑safe
representation across the project.
"""
from enum import Enum

class FailureType(Enum):
    """
    Enumeration of possible failure modes for an ALE execution trace.

    The string values match exactly the labels required by the dataset
    schema (`contracts/dataset.schema.yaml`) and downstream classification
    logic.
    """
    STATE_PERSISTENCE_ERROR = "State Persistence Error"
    REASONING_DEFICIT = "Reasoning Deficit"
    PASS = "Pass"

    def __str__(self) -> str:
        return self.value
