import pytest
from analysis.scaling import generate_scaling_plot

def test_generate_scaling_plot(tmp_path):
    # Provide minimal data for scaling plot
    data = [
        {"agent_count": 3, "specialization_index": 1},
        {"agent_count": 5, "specialization_index": 2},
        {"agent_count": 7, "specialization_index": 3},
    ]
    output_file = tmp_path / "scaling_plot.pdf"
    generate_scaling_plot(data, output_file)
    assert output_file.exists()
