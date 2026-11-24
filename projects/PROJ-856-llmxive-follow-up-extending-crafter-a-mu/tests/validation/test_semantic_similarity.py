import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from src.validation.semantic_similarity import compute_similarity, _write_validation_record

def _create_solid_image(path: Path, color: tuple[int, int, int]):
    img = Image.new("RGB", (64, 64), color)
    img.save(path)

def test_compute_similarity_identical_images(tmp_path: Path):
    # Two identical images should yield a similarity very close to 1.0.
    img_a = tmp_path / "img_a.png"
    img_b = tmp_path / "img_b.png"

    _create_solid_image(img_a, (255, 0, 0))
    _create_solid_image(img_b, (255, 0, 0))

    sim = compute_similarity(img_a, img_b)
    assert sim > 0.95, f"Expected similarity > 0.95, got {sim}"

def test_write_validation_record(tmp_path: Path):
    out_file = tmp_path / "semantic_validation.jsonl"
    _write_validation_record(
        out_file, figure_id="fig_2", vector_match=False, semantic_pass=True
    )
    line = out_file.read_text(encoding="utf-8").strip()
    import json

    record = json.loads(line)
    assert record["figure_id"] == "fig_2"
    assert record["vector_match"] is False
    assert record["semantic_pass"] is True
