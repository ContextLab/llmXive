"""
Persistence helpers for :class:`src.models.schemas.AnalysisResult`.

The analysis pipeline produces an ``AnalysisResult`` Pydantic model.
This module supplies two convenience functions:

* ``save_analysis_result`` – serialize the model to JSON on disk.
* ``load_analysis_result`` – read the JSON file and return a populated
  ``AnalysisResult`` instance.

The JSON format matches the schema used throughout the project and is
validated on load.
"""

import json
from pathlib import Path
from typing import Union

from src.models.schemas import AnalysisResult

def save_analysis_result(result: AnalysisResult, path: Union[str, Path]) -> None:
    """
    Write an ``AnalysisResult`` instance to ``path`` as pretty‑printed JSON.

    Parameters
    ----------
    result: AnalysisResult
        The Pydantic model to serialize.
    path: Union[str, Path]
        Destination file.  Parent directories are created automatically.
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(result.model_dump(), fp, indent=2, ensure_ascii=False)

def load_analysis_result(path: Union[str, Path]) -> AnalysisResult:
    """
    Load an ``AnalysisResult`` from a JSON file.

    Parameters
    ----------
    path: Union[str, Path]
        Path to the JSON file produced by ``save_analysis_result``.

    Returns
    -------
    AnalysisResult
        The deserialized Pydantic model.

    Raises
    ------
    FileNotFoundError
        If ``path`` does not exist.
    json.JSONDecodeError
        If the file contents are not valid JSON.
    pydantic.ValidationError
        If the JSON does not conform to the ``AnalysisResult`` schema.
    """
    input_path = Path(path)
    if not input_path.is_file():
        raise FileNotFoundError(f"Analysis result file not found: {input_path}")

    with input_path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)

    # ``AnalysisResult`` is a Pydantic model; ``parse_obj`` validates the
    # structure and types.
    return AnalysisResult.parse_obj(data)
