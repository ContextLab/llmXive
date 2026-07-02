import pytest
from analysis.scaling_plot_generator import generate_scaling_plot_with_notes

def test_scaling_integration(tmp_path):
    data = [
        {"agent_count": 3, "specialization_index": 1},
        {"agent_count": 5, "specialization_index": 2},
        {"agent_count": 7, "specialization_index": 3},
    ]
    output = tmp_path / "scaling_plot.pdf"
    generate_scaling_plot_with_notes(data, output)
    assert output.exists()
