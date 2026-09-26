import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.lme_model import validate_sufficient_trials

def test_validate_sufficient_trials_pass():
    """Test that valid data passes validation."""
    df = pd.DataFrame({
        'subject_id': [1, 1, 1, 2, 2, 2],
        'trial': [1, 2, 3, 1, 2, 3]
    })
    # 2 trials per subject, min is 2 -> should pass
    validate_sufficient_trials(df, subject_col='subject_id', min_trials=2)

def test_validate_sufficient_trials_fail():
    """Test that insufficient data raises RuntimeError."""
    df = pd.DataFrame({
        'subject_id': [1, 1, 2, 2],
        'trial': [1, 2, 1, 2]
    })
    # 2 trials per subject, min is 3 -> should fail
    with pytest.raises(RuntimeError, match="Subject validation failed"):
        validate_sufficient_trials(df, subject_col='subject_id', min_trials=3)

def test_validate_sufficient_trials_aggregation():
    """Test that aggregation flag allows failure."""
    df = pd.DataFrame({
        'subject_id': [1, 1, 2, 2],
        'trial': [1, 2, 1, 2]
    })
    # Should not raise, but log warning
    try:
        validate_sufficient_trials(
            df, 
            subject_col='subject_id', 
            min_trials=3, 
            allow_aggregation=True
        )
    except RuntimeError:
        pytest.fail("Validation should not raise when allow_aggregation is True")

def test_validate_missing_subject_column():
    """Test that missing subject column raises ValueError."""
    df = pd.DataFrame({'trial': [1, 2, 3]})
    with pytest.raises(ValueError, match="Subject column"):
        validate_sufficient_trials(df, subject_col='nonexistent')