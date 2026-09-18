"""
Execute Ground Truth Validation (Task T008a).

This script runs the annotation tool (T002b) to generate the required
manual ground truth file: `data/annotated/gt_subset_50.json`.

It loads a source video, steps through frames, and allows a human
annotator to label object states. It then saves the annotations to the
specified output path.

Logic:
1. Verify T002b (gt_tool.py) is available.
2. Determine the input video path (from args or default).
3. Invoke the annotation tool to collect 50 frames of annotations.
4. Save the result to `data/annotated/gt_subset_50.json`.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Import the annotation tool logic as specified in the API surface
from data.gt_tool import run_annotation_tool, parse_args as gt_parse_args

def main():
    parser = argparse.ArgumentParser(
        description="Execute Ground Truth Validation: Generate gt_subset_50.json"
    )
    parser.add_argument(
        "--video",
        type=str,
        default="data/input/sample_video.mp4",
        help="Path to the source video to annotate. "
             "If not found, the tool will attempt to use the first available video "
             "in data/input/ or fail loudly."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/annotated/gt_subset_50.json",
        help="Path to save the generated ground truth JSON."
    )
    parser.add_argument(
        "--frame-limit",
        type=int,
        default=50,
        help="Number of frames to annotate."
    )

    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    video_path = Path(args.video)
    if not video_path.exists():
        # Attempt to find a fallback video in data/input/
        input_dir = Path("data/input")
        if input_dir.exists():
            fallback = next(input_dir.glob("*.mp4"), None) or next(input_dir.glob("*.avi"), None)
            if fallback:
                print(f"Warning: Specified video '{video_path}' not found. Using fallback: {fallback}")
                video_path = fallback
            else:
                print(f"Error: No video file found at '{video_path}' and no fallback in '{input_dir}'.")
                sys.exit(1)
        else:
            print(f"Error: Video file not found at '{video_path}'.")
            sys.exit(1)

    print(f"Starting Ground Truth Annotation for: {video_path}")
    print(f"Target: {args.frame_limit} frames")
    print(f"Output: {output_path}")

    try:
        # Run the annotation tool
        # The tool is expected to be interactive or process frames and return the list of annotations.
        # Based on T002b spec, it generates the file. We call it here to ensure the file is created.
        annotations = run_annotation_tool(str(video_path), frame_limit=args.frame_limit)

        if not annotations:
            print("Error: No annotations were collected. Aborting.")
            sys.exit(1)

        # Construct the output schema as defined in T002b
        # {"frames": [{"frame_id": int, "object_state": "alive"|"dead", "hp": int, "timestamp": string}]}
        output_data = {
            "frames": annotations,
            "metadata": {
                "source_video": str(video_path),
                "frame_count": len(annotations),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": "1.0.0"
            }
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

        print(f"Success: Ground truth file generated at {output_path}")
        print(f"Total frames annotated: {len(annotations)}")

    except Exception as e:
        print(f"Error during annotation execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
