"""
rt_mechanism.py
----------------
Implements the baseline reaction‑time (RT) measurement mechanism for the
experiment.  The mechanism provides millisecond‑accurate timing for a
stimulus presentation and captures the participant's response.  The
measured RTs are saved to ``data/derived/rt_measurements.json``.

The implementation is deliberately lightweight and UI‑agnostic so it can
be exercised in automated tests (where a mock response function is used)
as well as in a real study (where the user presses ``Enter`` after seeing
the stimulus).
"""

import json
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------

def _ensure_parent_dir(file_path: Path) -> None:
    """Make sure the parent directory of *file_path* exists."""
    file_path.parent.mkdir(parents=True, exist_ok=True)


def display_stimulus(stimulus_path: str) -> None:
    """
    Display a stimulus image.

    In a full UI implementation this would open a window or render the
    image in a Streamlit app.  For headless CI environments we simply
    verify that the file exists; the actual display is optional and does
    not affect timing.
    """
    path = Path(stimulus_path)
    if not path.is_file():
        raise FileNotFoundError(f"Stimulus not found: {stimulus_path}")
    # No-op visual display – kept minimal for testability.


def run_rt_trial(
    stimulus_path: str,
    response_func: Callable[[], None],
    *,
    display: bool = True,
) -> float:
    """
    Run a single reaction‑time trial.

    Parameters
    ----------
    stimulus_path: str
        Path to the stimulus image (or any file representing the stimulus).
    response_func: Callable[[], None]
        A callable that blocks until the participant/respondent signals that
        they have perceived the stimulus.  In production this could be a
        ``input()`` call; in tests it is typically a ``lambda: time.sleep(x)``.
    display: bool, optional
        If ``True`` the stimulus is displayed via :func:`display_stimulus`.

    Returns
    -------
    float
        Reaction time in **milliseconds**, measured with ``time.perf_counter``.
    """
    if display:
        display_stimulus(stimulus_path)

    start = time.perf_counter()
    response_func()
    end = time.perf_counter()

    rt_ms = (end - start) * 1000.0
    return rt_ms


def measure_rt_for_directory(
    stimuli_dir: str,
    response_func: Optional[Callable[[], None]] = None,
    *,
    display: bool = True,
) -> Dict[str, float]:
    """
    Measure reaction times for all stimulus files in *stimuli_dir*.

    Parameters
    ----------
    stimuli_dir: str
        Directory containing stimulus files (e.g., images).
    response_func: Callable[[], None] or None
        Function that blocks until the participant responds.  If ``None``,
        a default ``input('Press Enter when you have perceived the stimulus...')``
        is used.
    display: bool, optional
        Forwarded to :func:`run_rt_trial`.

    Returns
    -------
    dict
        Mapping from stimulus filename (without extension) to measured RT in
        milliseconds.
    """
    stimuli_path = Path(stimuli_dir)
    if not stimuli_path.is_dir():
        raise NotADirectoryError(f"Stimuli directory does not exist: {stimuli_dir}")

    if response_func is None:
        # Default interactive behaviour
        def _default_response():
            input("Press Enter when you have perceived the stimulus...")

        response_func = _default_response

    measurements: Dict[str, float] = {}

    for file in sorted(stimuli_path.iterdir()):
        if file.is_file():
            rt = run_rt_trial(str(file), response_func, display=display)
            measurements[file.stem] = rt

    return measurements


def save_rt_measurements(
    measurements: Dict[str, float],
    output_path: str = "data/derived/rt_measurements.json",
) -> None:
    """
    Persist the RT measurements to a JSON file.

    The JSON format is a simple mapping from stimulus identifier to RT
    (float, milliseconds).  The output directory is created automatically
    if it does not already exist.
    """
    out_path = Path(output_path)
    _ensure_parent_dir(out_path)

    # Use ``indent`` for readability – not required for functionality.
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(measurements, f, indent=2, sort_keys=True)


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------

def main() -> None:
    """
    Command‑line interface.

    Example
    -------
    $ python -m src.experiment.rt_mechanism \\
          --stimuli-dir data/stimuli/neutral \\
          --output data/derived/rt_measurements.json
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Run baseline reaction‑time measurement for a set of stimuli."
    )
    parser.add_argument(
        "--stimuli-dir",
        type=str,
        default="data/stimuli/neutral",
        help="Directory containing stimulus files (default: data/stimuli/neutral).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/derived/rt_measurements.json",
        help="Path to write the RT measurements JSON (default: data/derived/rt_measurements.json).",
    )
    args = parser.parse_args()

    measurements = measure_rt_for_directory(args.stimuli_dir)
    save_rt_measurements(measurements, args.output)
    print(f"Saved RT measurements for {len(measurements)} stimuli to {args.output}")


if __name__ == "__main__":
    main()