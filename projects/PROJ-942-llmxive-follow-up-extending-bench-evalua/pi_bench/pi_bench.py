"""
Minimal HuggingFace `datasets` loader for the placeholder π‑Bench dataset.

The dataset consists of a collection of JSON files placed in the directory
specified by `data_dir` (default: ``data/raw``). Each file is treated as a
single example; the example fields are:

- ``file_path``: the relative path to the JSON file (string).
- ``content``: the raw JSON content of the file (string).

This loader purposefully avoids any deep parsing to keep the implementation
lightweight and to remain compatible with downstream scripts that operate on
the raw JSON files directly.
"""

import json
from pathlib import Path
from typing import Generator, Tuple

import datasets

_DESCRIPTION = """Placeholder π‑Bench dataset loader that reads raw JSON files."""
_CITATION = """\
@misc{placeholder_pi_bench,
  title = {Placeholder π‑Bench dataset},
  author = {Generated for llmxive follow‑up project},
  year = {2026},
  note = {This dataset is a minimal stand‑in for the official π‑Bench.}
}"""

class PiBenchConfig(datasets.BuilderConfig):
    """Configuration for the PiBench dataset."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class PiBench(datasets.GeneratorBasedBuilder):
    """DatasetBuilder that loads raw JSON files from a directory."""

    VERSION = datasets.Version("1.0.0")
    BUILDER_CONFIGS = [
        PiBenchConfig(name="default", version=VERSION, description=_DESCRIPTION),
    ]

    def _info(self) -> datasets.DatasetInfo:
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            citation=_CITATION,
            features=datasets.Features(
                {
                    "file_path": datasets.Value("string"),
                    "content": datasets.Value("string"),
                }
            ),
            supervised_keys=None,
        )

    def _split_generators(self, dl_manager: datasets.DownloadManager):
        # The quick‑start passes ``data_dir`` as a kwarg; we retrieve it from
        # ``self.config`` if present, otherwise fall back to the default.
        data_dir = getattr(self.config, "data_dir", None)
        if data_dir is None:
            # Default location used by the download script.
            data_dir = Path("data") / "raw"
        else:
            data_dir = Path(data_dir)

        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN,
                gen_kwargs={"data_dir": data_dir},
            )
        ]

    def _generate_examples(self, data_dir: Path) -> Generator[Tuple[int, dict], None, None]:
        """Yield examples from each JSON file in ``data_dir``."""
        json_files = sorted(data_dir.rglob("*.json"))
        for idx, json_path in enumerate(json_files):
            try:
                # Load the raw file content as a string; downstream code may parse it.
                content = json_path.read_text(encoding="utf-8")
            except Exception as exc:
                # Propagate a clear error so that failures are loud.
                raise RuntimeError(f"Failed to read JSON file {json_path}: {exc}") from exc

            yield idx, {
                "file_path": str(json_path.relative_to(Path.cwd())),
                "content": content,
            }
