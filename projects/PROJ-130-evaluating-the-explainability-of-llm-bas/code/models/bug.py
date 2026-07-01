"""
Bug entity definition for the llmXive automated science pipeline.

Defines the Bug dataclass representing a bug instance from the Defects4J dataset.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Bug:
    """
    Represents a specific bug instance from the Defects4J dataset.
    
    Attributes:
        id (str): Unique identifier for the bug (e.g., 'Lang-1', 'Math-42').
        file_path (str): Path to the source file containing the bug, relative to the project root.
        test_suite (List[str]): List of test class/method names associated with this bug.
        reference_text (str): The original source code content of the file before the bug fix.
    """
    id: str
    file_path: str
    test_suite: List[str]
    reference_text: str

    def __post_init__(self):
        """
        Validates the Bug instance after initialization.
        
        Ensures that required fields are not empty and test_suite is a list.
        """
        if not self.id:
            raise ValueError("Bug ID cannot be empty")
        if not self.file_path:
            raise ValueError("File path cannot be empty")
        if not isinstance(self.test_suite, list):
            raise TypeError("test_suite must be a list of strings")
        if not self.reference_text:
            raise ValueError("Reference text cannot be empty")

    def to_dict(self) -> dict:
        """
        Converts the Bug instance to a dictionary representation.
        
        Returns:
            dict: Dictionary containing the bug's attributes.
        """
        return {
            "id": self.id,
            "file_path": self.file_path,
            "test_suite": self.test_suite,
            "reference_text": self.reference_text
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Bug":
        """
        Creates a Bug instance from a dictionary.
        
        Args:
            data (dict): Dictionary containing bug attributes.
        
        Returns:
            Bug: A new Bug instance.
        """
        return cls(
            id=data["id"],
            file_path=data["file_path"],
            test_suite=data["test_suite"],
            reference_text=data["reference_text"]
        )
