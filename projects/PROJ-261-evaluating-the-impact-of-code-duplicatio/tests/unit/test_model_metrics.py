import math
import pytest

# Import the validation function from the model_metrics module.
# The import path follows the project layout where `code` is a package.
from code.model_metrics import validate_perplexity

@pytest.mark.parametrize(
    "invalid_value",
    [
        math.nan,
        math.inf,
        -math.inf,
    ],
)
def test_validate_perplexity_raises_on_invalid_values(invalid_value):
    """
    The `validate_perplexity` function must reject non‑finite values.
    It should raise a ValueError when given NaN or infinite perplexity scores.
    """
    with pytest.raises(ValueError):
        validate_perplexity(invalid_value)