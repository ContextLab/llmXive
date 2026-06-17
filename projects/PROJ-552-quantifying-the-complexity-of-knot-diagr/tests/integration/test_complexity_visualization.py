"""
End‑to‑end integration test that the complexity visualization script creates the
required PNG file.
"""

from pathlib import Path

from code.analysis.complexity_visualization_examples import main as viz_main

def test_complexity_visualization_creates_png(tmp_path, monkeypatch):
    # Run in an isolated temporary directory
    monkeypatch.chdir(tmp_path)
    # The downloader must have run to provide data
    from code.download.knot_atlas_loader import main as download_main

    download_main()
    # Run the visualization script
    viz_main()
    output = Path("data/plots/complexity_visualization_examples.png")
    assert output.is_file()
    # Simple sanity: file size > 0
    assert output.stat().st_size > 0