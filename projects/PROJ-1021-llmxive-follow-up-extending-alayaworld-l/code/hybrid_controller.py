"""
Hybrid Controller Logic for AlayaWorld Extension.

This module implements the edge-case handling logic required for the
Hybrid Correction Mechanism (User Story 2). It detects discrepancies
between the symbolic state and visual output, and generates correction
tokens to be injected into the generation prompt.

Edge cases handled:
1. Rendering Failure: Symbolic state (e.g., teleportation) cannot be rendered.
2. Phantom Object: Objects detected in video but not in symbolic log.
3. Occlusion: Fallback logic for occluded objects.
4. Correction Token Generation: Dynamic prompt re-conditioning tokens.
"""

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from pathlib import Path

# Import from existing API surface
from cv_pipeline import DetectedObject, FrameAnalysis
from symbolic_engine import SymbolicEngine, ObjectState, ActionLogEntry


@dataclass
class DiscrepancyReport:
    """Report of a detected discrepancy between symbolic and visual states."""
    error_code: str
    object_id: Optional[str]
    timestamp: str
    details: Dict[str, Any]
    correction_token: Optional[str] = None
    confidence: float = 1.0


@dataclass
class HybridControlState:
    """State tracking for the hybrid controller across frames."""
    last_symbolic_state: Dict[str, ObjectState] = field(default_factory=dict)
    last_visual_state: Dict[str, DetectedObject] = field(default_factory=dict)
    occlusion_map: Dict[str, bool] = field(default_factory=dict)
    drift_score_accumulator: float = 0.0
    low_confidence_frames: List[int] = field(default_factory=list)


class HybridController:
    """
    Controller that manages the interaction between the symbolic engine
    and the computer vision pipeline to detect and correct semantic drift.
    """

    # Correction Token Formats as per specification
    TOKEN_RESET = "[OBJECT_RESET]"
    TOKEN_REMOVE = "[OBJECT_REMOVE]"
    TOKEN_DEAD = "[OBJECT_DEAD]"
    TOKEN_ALIVE = "[OBJECT_ALIVE]"
    TOKEN_OCCLUSION = "[OCCLUSION_FALLBACK]"

    def __init__(self, symbolic_engine: SymbolicEngine):
        """
        Initialize the Hybrid Controller.

        Args:
            symbolic_engine: The running instance of the symbolic engine
                             to track state and inject corrections.
        """
        self.symbolic_engine = symbolic_engine
        self.control_state = HybridControlState()
        self.discrepancy_log: List[DiscrepancyReport] = []

    def _detect_rendering_failure(
        self,
        frame_id: int,
        symbolic_state: Dict[str, ObjectState],
        visual_objects: List[DetectedObject]
    ) -> Optional[DiscrepancyReport]:
        """
        Detect if a symbolic state (e.g., teleportation) cannot be rendered.

        Logic:
        - If symbolic state indicates an object should exist at a location
          but no object is detected there (and it's not occluded), and
          the object is not in a "dead" state, it may be a rendering failure.
        - Specifically checks for teleportation: sudden large displacement
          without intermediate motion (if history is available).
        """
        for obj_id, sym_state in symbolic_state.items():
            if sym_state.is_alive:
                # Check if object is missing in visual output
                visual_match = next(
                    (v for v in visual_objects if v.id == obj_id),
                    None
                )

                if visual_match is None:
                    # Object is missing but should be alive
                    # Check occlusion status
                    if not self.control_state.occlusion_map.get(obj_id, False):
                        return DiscrepancyReport(
                            error_code="RENDER_FAILURE",
                            object_id=obj_id,
                            timestamp=datetime.now(timezone.utc).isoformat(),
                            details={
                                "frame_id": frame_id,
                                "expected_state": asdict(sym_state),
                                "reason": "Object missing from visual output but not occluded"
                            },
                            correction_token=self.TOKEN_RESET
                        )
        return None

    def _detect_phantom_object(
        self,
        frame_id: int,
        symbolic_state: Dict[str, ObjectState],
        visual_objects: List[DetectedObject]
    ) -> Optional[DiscrepancyReport]:
        """
        Detect objects in video not present in the symbolic log.

        Logic:
        - Iterate through visual objects.
        - If an object is detected that has no corresponding entry in the
          symbolic state, it is a "phantom".
        """
        symbolic_ids = set(symbolic_state.keys())
        visual_ids = set(v.id for v in visual_objects)

        phantom_ids = visual_ids - symbolic_ids

        if phantom_ids:
            phantom_id = list(phantom_ids)[0]  # Report first phantom found
            # Find the phantom object details
            phantom_obj = next(v for v in visual_objects if v.id == phantom_id)

            return DiscrepancyReport(
                error_code="PHANTOM_OBJECT",
                object_id=phantom_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                details={
                    "frame_id": frame_id,
                    "detected_bbox": phantom_obj.bbox,
                    "detected_class": phantom_obj.class_label,
                    "reason": "Object detected visually but not in symbolic state"
                },
                correction_token=self.TOKEN_REMOVE
            )
        return None

    def _handle_occlusion(
        self,
        frame_id: int,
        symbolic_state: Dict[str, ObjectState],
        visual_objects: List[DetectedObject]
    ) -> List[DiscrepancyReport]:
        """
        Implement fallback logic for occlusion.

        Logic:
        - If an object is missing from visual output but was present in
          previous frames, mark it as potentially occluded.
        - Update occlusion map.
        - Flag frame as low-confidence.
        - Generate a fallback token if necessary (though spec implies
          just flagging for now).
        """
        reports = []
        symbolic_ids = set(symbolic_state.keys())
        visual_ids = set(v.id for v in visual_objects)

        # Objects in symbolic but not in visual
        missing_ids = symbolic_ids - visual_ids

        for obj_id in missing_ids:
            if self.control_state.occlusion_map.get(obj_id, False):
                # Already marked as occluded, persist state
                continue

            # Check if it was visible in the last frame (simple heuristic)
            # In a real implementation, we'd track a history buffer
            if obj_id in self.control_state.last_visual_state:
                # Likely occluded
                self.control_state.occlusion_map[obj_id] = True
                self.control_state.low_confidence_frames.append(frame_id)
                
                # We don't generate a correction token for occlusion itself,
                # but we log the event.
                reports.append(DiscrepancyReport(
                    error_code="OCCLUSION_DETECTED",
                    object_id=obj_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    details={
                        "frame_id": frame_id,
                        "action": "State persisted, confidence lowered",
                        "reason": "Object missing but previously visible"
                    },
                    correction_token=self.TOKEN_OCCLUSION,
                    confidence=0.5
                ))
            else:
                # Not occluded, likely a rendering failure (handled elsewhere)
                pass

        # Clear occlusion for objects that reappear
        for obj_id in visual_ids:
            if self.control_state.occlusion_map.get(obj_id, False):
                self.control_state.occlusion_map[obj_id] = False

        return reports

    def _generate_death_correction(
        self,
        frame_id: int,
        symbolic_state: Dict[str, ObjectState],
        visual_objects: List[DetectedObject]
    ) -> Optional[DiscrepancyReport]:
        """
        Detect if an object is visually dead but symbolic state says alive,
        or vice versa (if death logic is visual-only).

        Logic:
        - Compare HP/State from symbolic engine vs visual detection.
        - If visual evidence strongly suggests death (e.g., HP=0 or specific
          visual cue) but symbolic says alive, generate correction.
        """
        for obj_id, sym_state in symbolic_state.items():
            if not sym_state.is_alive:
                # Symbolic says dead. Check if visual says alive.
                visual_match = next(
                    (v for v in visual_objects if v.id == obj_id),
                    None
                )
                if visual_match and visual_match.hp > 0:
                    # Visual says alive, symbolic says dead -> Correction needed
                    # Actually, usually we trust symbolic for death if it's rule-based,
                    # but if the prompt needs to reflect the visual reality for the generator:
                    # The spec says: "generate a 'remove' correction token" for phantoms.
                    # For death mismatch: "output prompt string ... [OBJECT_DEAD]"
                    return DiscrepancyReport(
                        error_code="STATE_MISMATCH",
                        object_id=obj_id,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        details={
                            "frame_id": frame_id,
                            "symbolic_state": "dead",
                            "visual_hp": visual_match.hp,
                            "reason": "Visual HP > 0 but symbolic state is dead"
                        },
                        correction_token=self.TOKEN_DEAD
                    )
            else:
                # Symbolic says alive. Check if visual says dead.
                visual_match = next(
                    (v for v in visual_objects if v.id == obj_id),
                    None
                )
                if visual_match and visual_match.hp <= 0:
                    # Visual says dead, symbolic says alive -> Correction needed
                    return DiscrepancyReport(
                        error_code="STATE_MISMATCH",
                        object_id=obj_id,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        details={
                            "frame_id": frame_id,
                            "symbolic_state": "alive",
                            "visual_hp": visual_match.hp,
                            "reason": "Visual HP <= 0 but symbolic state is alive"
                        },
                        correction_token=self.TOKEN_DEAD
                    )
        return None

    def process_frame(
        self,
        frame_id: int,
        symbolic_state: Dict[str, ObjectState],
        visual_analysis: FrameAnalysis
    ) -> Tuple[List[str], List[DiscrepancyReport]]:
        """
        Process a single frame to detect discrepancies and generate correction tokens.

        Args:
            frame_id: The current frame index.
            symbolic_state: Current state from the symbolic engine.
            visual_analysis: The result from the CV pipeline for this frame.

        Returns:
            A tuple of (list of correction tokens to inject, list of discrepancy reports).
        """
        tokens_to_inject = []
        reports = []

        # 1. Detect Rendering Failures
        render_failure = self._detect_rendering_failure(
            frame_id, symbolic_state, visual_analysis.objects
        )
        if render_failure:
            reports.append(render_failure)
            tokens_to_inject.append(render_failure.correction_token)

        # 2. Detect Phantom Objects
        phantom = self._detect_phantom_object(
            frame_id, symbolic_state, visual_analysis.objects
        )
        if phantom:
            reports.append(phantom)
            tokens_to_inject.append(phantom.correction_token)
            # Increment drift score
            self.control_state.drift_score_accumulator += 1.0

        # 3. Handle Occlusion
        occlusion_reports = self._handle_occlusion(
            frame_id, symbolic_state, visual_analysis.objects
        )
        reports.extend(occlusion_reports)
        for r in occlusion_reports:
            if r.correction_token:
                tokens_to_inject.append(r.correction_token)

        # 4. Detect State Mismatches (Death/Alive)
        state_mismatch = self._generate_death_correction(
            frame_id, symbolic_state, visual_analysis.objects
        )
        if state_mismatch:
            reports.append(state_mismatch)
            tokens_to_inject.append(state_mismatch.correction_token)

        # Update state history
        self.control_state.last_symbolic_state = symbolic_state
        self.control_state.last_visual_state = {
            obj.id: obj for obj in visual_analysis.objects
        }

        # Log reports
        self.discrepancy_log.extend(reports)

        return tokens_to_inject, reports

    def get_drift_score(self) -> float:
        """Return the accumulated drift score based on detected discrepancies."""
        return self.control_state.drift_score_accumulator

    def save_discrepancy_log(self, output_path: str):
        """Save the discrepancy log to a JSON file."""
        log_data = [asdict(r) for r in self.discrepancy_log]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)

def main():
    """
    Standalone execution for testing the Hybrid Controller logic.
    This function simulates a frame processing scenario to demonstrate the controller.
    """
    print("Initializing Hybrid Controller...")
    
    # Initialize symbolic engine
    sym_engine = SymbolicEngine()
    
    # Create controller
    controller = HybridController(sym_engine)
    
    # Simulate a scenario
    # 1. Add an object to symbolic state
    sym_engine.apply_action({
        "type": "SUMMON",
        "object_id": "obj_001",
        "position": {"x": 100, "y": 100},
        "hp": 100
    })
    
    # 2. Create a mock visual analysis that misses the object (Rendering Failure)
    from cv_pipeline import DetectedObject, FrameAnalysis
    mock_visual = FrameAnalysis(
        frame_id=1,
        timestamp="2023-01-01T00:00:00Z",
        objects=[] # Object missing
    )
    
    # Get current symbolic state
    current_state = sym_engine.get_state()
    
    print(f"Symbolic State: {current_state}")
    print(f"Visual Objects: {mock_visual.objects}")
    
    # Process frame
    tokens, reports = controller.process_frame(1, current_state, mock_visual)
    
    print(f"Detected Discrepancies: {len(reports)}")
    for r in reports:
        print(f"  - {r.error_code}: {r.details.get('reason', 'N/A')}")
        print(f"    Token: {r.correction_token}")
    
    print(f"Correction Tokens to Inject: {tokens}")
    
    # Simulate Phantom Object
    mock_phantom = FrameAnalysis(
        frame_id=2,
        timestamp="2023-01-01T00:00:01Z",
        objects=[DetectedObject(id="phantom_99", class_label="unknown", bbox=(0,0,10,10), hp=50, confidence=0.9)]
    )
    
    tokens2, reports2 = controller.process_frame(2, current_state, mock_phantom)
    
    print(f"\nPhantom Scenario:")
    print(f"Detected Discrepancies: {len(reports2)}")
    for r in reports2:
        print(f"  - {r.error_code}: {r.details.get('reason', 'N/A')}")
        print(f"    Token: {r.correction_token}")

    # Save log
    log_path = "data/results/controller_discrepancy_log.json"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    controller.save_discrepancy_log(log_path)
    print(f"\nDiscrepancy log saved to {log_path}")

if __name__ == "__main__":
    main()