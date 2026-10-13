import pytest
from pathlib import Path
from code.utils.plotting import plot_convergence_loglog, plot_regression_scatter, plot_critical_threshold_detection

def test_plots_written(tmp_path):
    log_path = str(tmp_path / "log.png")
    reg_path = str(tmp_path / "reg.png")
    trace_path = str(tmp_path / "trace.png")

    plot_convergence_loglog([{"epsilon": 0.1, "convergence_time": 10}], log_path)
    plot_regression_scatter([1, 2], [1, 2], reg_path)
    plot_critical_threshold_detection([0.1, 0.01], 0.2, trace_path)

    assert Path(log_path).exists() and Path(log_path).stat().st_size > 0
    assert Path(reg_path).exists() and Path(reg_path).stat().st_size > 0
    assert Path(trace_path).exists() and Path(trace_path).stat().st_size > 0