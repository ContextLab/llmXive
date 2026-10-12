"""
Unit test for the scatter‑plot generation helper used by the
``plot_top_features`` script. The test verifies that a PNG file is
created without raising an exception.
"""

import pandas as pd
import numpy as np
import os
import pytest

from code.plot_top_features import create_scatter_plot_with_regression

def test_create_scatter_plot(tmp_path):
    df = pd.DataFrame({
        "x": np.arange(10),
        "y": np.arange(10) * 2
    })
    out_file = tmp_path / "scatter.png"
    create_scatter_plot_with_regression(df, "x", "y", str(out_file), "Test Plot")
    assert out_file.is_file()