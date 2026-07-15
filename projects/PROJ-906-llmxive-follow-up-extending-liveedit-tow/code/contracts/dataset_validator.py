"""
Validator for Dataset (VideoClip) schema.
"""
import json
from typing import Any, Dict, List, Optional
from dataclasses import asdict
from data.models import VideoClip


class DatasetValidator:
    """
    Validates Dataset artifacts (VideoClip objects) against the expected schema.
    """

    REQUIRED_FIELDS = [
        "clip_id",
        "source_dataset",
        "file_path",
        "duration_frames",
        "width",
        "height",
        "fps",
        "motion_category",
        "mask_path",
        "flow_path",
        "created_at",
    ]

    MOTION_CATEGORIES = {"static", "slow_rigid", "fast_non_rigid"}

    @classmethod
    def validate_video_clip(cls, clip: VideoClip) -> Dict[str, Any]:
        """
        Validates a single VideoClip instance.

        Args:
            clip: The VideoClip instance to validate.

        Returns:
            A dict with 'valid' (bool) and 'errors' (list of str).
        """
        errors = []

        # Check required fields exist
        clip_dict = asdict(clip)
        for field in cls.REQUIRED_FIELDS:
            if field not in clip_dict or clip_dict[field] is None:
                errors.append(f"Missing required field: {field}")

        # Validate motion_category
        if clip_dict.get("motion_category") not in cls.MOTION_CATEGORIES:
            errors.append(
                f"Invalid motion_category: {clip_dict.get('motion_category')}. "
                f"Must be one of {cls.MOTION_CATEGORIES}"
            )

        # Validate numeric constraints
        if clip_dict.get("duration_frames", 0) <= 0:
            errors.append("duration_frames must be positive")
        if clip_dict.get("width", 0) <= 0:
            errors.append("width must be positive")
        if clip_dict.get("height", 0) <= 0:
            errors.append("height must be positive")
        if clip_dict.get("fps", 0) <= 0:
            errors.append("fps must be positive")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    @classmethod
    def validate_dataset(cls, clips: List[VideoClip]) -> Dict[str, Any]:
        """
        Validates a list of VideoClip instances.

        Args:
            clips: List of VideoClip instances.

        Returns:
            A dict with 'valid' (bool), 'errors' (list of str), and 'stats' (dict).
        """
        all_errors = []
        valid_count = 0

        for i, clip in enumerate(clips):
            result = cls.validate_video_clip(clip)
            if not result["valid"]:
                all_errors.extend([f"[Clip {i}] {e}" for e in result["errors"]])
            else:
                valid_count += 1

        return {
            "valid": len(all_errors) == 0,
            "errors": all_errors,
            "stats": {
                "total_clips": len(clips),
                "valid_clips": valid_count,
                "invalid_clips": len(clips) - valid_count,
            },
        }

    @classmethod
    def validate_json_file(cls, file_path: str) -> Dict[str, Any]:
        """
        Validates a JSON file containing a list of VideoClip records.

        Args:
            file_path: Path to the JSON file.

        Returns:
            Validation result dict.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                return {
                    "valid": False,
                    "errors": ["JSON root must be a list of clips"],
                    "stats": {},
                }

            # Reconstruct VideoClip objects from dict
            clips = []
            for item in data:
                # Ensure required fields are present before instantiation
                if all(k in item for k in cls.REQUIRED_FIELDS):
                    try:
                        clip = VideoClip(**item)
                        clips.append(clip)
                    except TypeError as e:
                        return {
                            "valid": False,
                            "errors": [f"Failed to instantiate VideoClip: {str(e)}"],
                            "stats": {},
                        }
                else:
                    missing = set(cls.REQUIRED_FIELDS) - set(item.keys())
                    return {
                        "valid": False,
                        "errors": [f"Missing fields in clip record: {missing}"],
                        "stats": {},
                    }

            return cls.validate_dataset(clips)

        except FileNotFoundError:
            return {
                "valid": False,
                "errors": [f"File not found: {file_path}"],
                "stats": {},
            }
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "errors": [f"Invalid JSON: {str(e)}"],
                "stats": {},
            }
