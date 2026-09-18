"""
Ground Truth Annotation Tool for AlayaWorld.

This tool loads a video file, displays frames sequentially, and allows
a human annotator to label object states (HP, alive/dead) for each frame.
The annotations are saved to data/annotated/gt_subset_50.json.

Usage:
    python code/data/gt_tool.py --video <path_to_video.mp4> --output <path_to_output.json>
"""

import argparse
import json
import sys
import cv2
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Constants for UI
WINDOW_NAME = "AlayaWorld Ground Truth Annotator"
INSTRUCTIONS = (
    "Controls:\n"
    "  [Space] / [Right Arrow]: Next Frame\n"
    "  [Left Arrow]: Previous Frame\n"
    "  [A]: Set State = Alive\n"
    "  [D]: Set State = Dead\n"
    "  [UP]: Increase HP (+10)\n"
    "  [DOWN]: Decrease HP (-10)\n"
    "  [S]: Save & Exit\n"
    "  [Q]: Quit (Discard Changes)\n"
    f"Current HP: {0} | State: {None}"
)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ground Truth Annotation Tool")
    parser.add_argument(
        "--video",
        type=str,
        required=True,
        help="Path to the input video file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/annotated/gt_subset_50.json",
        help="Path to save the ground truth JSON file."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of frames to annotate (default: 50)."
    )
    return parser.parse_args()

def load_video(video_path: str) -> List[np.ndarray]:
    """
    Loads video frames into a list of numpy arrays.
    Raises an error if the video cannot be opened.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Error: Could not open video file at {video_path}")

    frames = []
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
        frame_count += 1
        # Optional: limit initial load if video is massive, though we process sequentially
        if frame_count >= 10000: # Safety break for extremely long videos
            print("Warning: Video exceeds 10000 frames. Stopping load.")
            break

    cap.release()
    if not frames:
        raise ValueError("Error: Video file contains no readable frames.")
    return frames

def draw_frame(frame: np.ndarray, state: str, hp: int, current_idx: int, total: int) -> np.ndarray:
    """
    Draws the current state overlay on the frame for the annotator.
    """
    # Convert to RGB for display if necessary (OpenCV uses BGR)
    display_frame = frame.copy()
    h, w, _ = display_frame.shape

    # Background overlay for info
    overlay_y = 20
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    color = (255, 255, 255)
    thickness = 2

    # Frame info
    info_text = f"Frame: {current_idx + 1} / {total}"
    cv2.putText(display_frame, info_text, (10, overlay_y), font, font_scale, color, thickness)

    # State info
    state_text = f"State: {state.upper() if state else 'UNSET'}"
    color_state = (0, 255, 0) if state == "alive" else (0, 0, 255) if state == "dead" else (255, 255, 0)
    cv2.putText(display_frame, state_text, (10, overlay_y + 30), font, font_scale, color_state, thickness)

    # HP info
    hp_text = f"HP: {hp}"
    cv2.putText(display_frame, hp_text, (10, overlay_y + 60), font, font_scale, (255, 255, 255), thickness)

    # Instructions (smaller)
    cv2.putText(display_frame, "Controls: [A]live [D]ead [UP]HP+ [DOWN]HP- [Space]Next [S]ave [Q]uit", (10, h - 20), font, 0.4, (200, 200, 200), 1)

    return display_frame

def run_annotation_tool(video_path: str, output_path: str, limit: int = 50) -> None:
    """
    Main loop for the annotation tool.
    """
    print(f"Loading video from: {video_path}...")
    frames = load_video(video_path)
    total_frames = len(frames)
    print(f"Loaded {total_frames} frames. Limiting to {min(limit, total_frames)} for annotation.")

    # Determine actual limit
    actual_limit = min(limit, total_frames)

    # Initialize state storage
    # We only store annotations for the frames we actually annotate
    annotations: List[Dict] = []

    current_idx = 0
    current_state: Optional[str] = None
    current_hp = 0

    # Pre-fill annotations list with None or placeholders if we want to track all,
    # but the spec implies we save the subset we annotate.
    # We will append to 'annotations' as the user saves or at the end.
    # To match the schema exactly, we will build the list of annotated frames.

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 800, 600)

    print(f"Starting annotation for {actual_limit} frames.")
    print("Press 'S' to save and exit, 'Q' to quit without saving.")

    while current_idx < actual_limit:
        frame = frames[current_idx]
        display_frame = draw_frame(frame, current_state, current_hp, current_idx, total_frames)

        cv2.imshow(WINDOW_NAME, display_frame)

        key = cv2.waitKey(0) & 0xFF

        if key == ord('q'):
            print("Quitting without saving.")
            cv2.destroyAllWindows()
            return

        elif key == ord('s'):
            # Save current state if valid, then move to next or finish
            if current_state is not None:
                # Check if this frame is already in the list (shouldn't be if we append on save)
                # Actually, the workflow is: user navigates, sets state, then saves?
                # Or user navigates, sets state, and we record it when they move?
                # Let's assume: User sets state for current frame, then hits Space to move.
                # If they hit 'S', we save the current frame if it has a state, and exit.
                annotation_entry = {
                    "frame_id": current_idx,
                    "object_state": current_state,
                    "hp": current_hp,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                # Avoid duplicates if they press S multiple times on same frame
                if not any(a["frame_id"] == current_idx for a in annotations):
                    annotations.append(annotation_entry)
                print(f"Saved frame {current_idx}. Exiting.")
            else:
                print("Cannot save: No state set for current frame.")

            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump({"frames": annotations}, f, indent=2)
            print(f"Ground truth saved to: {output_path}")
            cv2.destroyAllWindows()
            return

        elif key == ord(' '):
            # Next frame
            # If current frame has state, record it before moving?
            # The prompt says "step through frames... and allow a human annotator to label".
            # Let's auto-save current if state is set before moving, to prevent loss.
            if current_state is not None:
                if not any(a["frame_id"] == current_idx for a in annotations):
                    annotations.append({
                        "frame_id": current_idx,
                        "object_state": current_state,
                        "hp": current_hp,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
            
            current_idx += 1
            if current_idx >= actual_limit:
                print("Reached end of annotation limit.")
                # Save remaining if any? No, we only save on explicit save or exit.
                # Let's force save if we hit limit? No, user might want to review.
                # We'll just stop the loop.
                break

        elif key == ord('a'):
            current_state = "alive"
            if current_hp == 0: current_hp = 100 # Default HP if not set
        elif key == ord('d'):
            current_state = "dead"
            if current_hp == 0: current_hp = 0
        elif key == 81: # Left Arrow
            if current_idx > 0:
                current_idx -= 1
        elif key == 83: # Right Arrow
            if current_idx < actual_limit - 1:
                current_idx += 1
        elif key == 82: # Up Arrow
            current_hp = max(0, current_hp + 10)
        elif key == 84: # Down Arrow
            current_hp = max(0, current_hp - 10)

    # If loop finishes naturally (reached limit)
    print("Annotation limit reached. Saving current progress...")
    if current_state is not None:
        if not any(a["frame_id"] == current_idx - 1 for a in annotations):
            annotations.append({
                "frame_id": current_idx - 1,
                "object_state": current_state,
                "hp": current_hp,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({"frames": annotations}, f, indent=2)
    print(f"Ground truth saved to: {output_path}")
    cv2.destroyAllWindows()

def main() -> None:
    args = parse_args()
    try:
        run_annotation_tool(args.video, args.output, args.limit)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
