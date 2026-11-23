import unittest
from pathlib import Path
import sys

# Ensure the project root is in the path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.pruning import RewardFidelityLevel, fidelity_context


class TestPruningLogic(unittest.TestCase):
    """
    Contract tests for the pruning logic, specifically validating
    the fidelity_level parameter constraints.
    """

    def test_pruning_logic_validates_fidelity_level(self):
        """
        Assertion: Verify that a pruning request with an invalid `fidelity_level`
        (e.g., "quaternary") raises ValueError.
        """
        invalid_level = "quaternary"
        
        # The fidelity_context function (or the underlying logic) should validate
        # the input against the RewardFidelityLevel enum.
        # We expect a ValueError to be raised for invalid enum values.
        
        with self.assertRaises(ValueError) as context:
            # Attempt to use the context manager with an invalid string
            # Note: fidelity_context expects a RewardFidelityLevel enum member.
            # Passing a string that is not a valid member should raise ValueError
            # either during enum construction or inside the function logic.
            with fidelity_context(invalid_level):
                pass

        # Verify the error message contains relevant information (optional but good practice)
        self.assertIn("fidelity_level", str(context.exception).lower())

    def test_pruning_logic_accepts_valid_fidelity_levels(self):
        """
        Assertion: Verify that valid fidelity levels do not raise errors.
        """
        valid_levels = [
            RewardFidelityLevel.DENSE,
            RewardFidelityLevel.BINARY,
            RewardFidelityLevel.THREE_BIN
        ]

        for level in valid_levels:
            try:
                with fidelity_context(level):
                    pass
            except Exception as e:
                self.fail(f"fidelity_context raised {type(e).__name__} for valid level {level}: {e}")

    def test_pruning_logic_rejects_none_fidelity_level(self):
        """
        Assertion: Verify that passing None as fidelity_level raises ValueError.
        """
        with self.assertRaises(ValueError):
            with fidelity_context(None):
                pass


if __name__ == '__main__':
    unittest.main()