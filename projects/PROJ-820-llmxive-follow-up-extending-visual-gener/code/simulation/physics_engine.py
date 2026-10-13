"""
Physics Simulation Engine using PyMunk.
Simulates basic physics on CPU to generate JSON constraints and detect logical contradictions.
The output JSON conforms to the schema at
`specs/001-llmxive-follow-up-extending-visual-gener/contracts/physics-constraint.schema.yaml`.
"""
import json
import logging
import csv
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pymunk
from pymunk import Vec2d

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
GRAVITY = -9.81
SIMULATION_TIME_STEP = 1.0 / 60.0
SIMULATION_STEPS = 600  # 10 seconds of simulation
BOX_SIZE = 50  # pixels

class SceneDescriptionNotFoundError(Exception):
    """Raised when a scene description file is not found."""

class InvalidSceneDescriptionError(Exception):
    """Raised when a scene description is malformed."""

class SimulationError(Exception):
    """Raised when a simulation fails."""


class PhysicsConstraint:
    """
    Represents a physics constraint derived from a scene simulation.
    This class can emit a dictionary that matches the official JSON schema.
    """

    def __init__(self, scene_id: str):
        self.scene_id = scene_id
        # Raw data collected during simulation
        self._bounding_boxes: List[Dict[str, Any]] = []
        self._collision_rules: List[Dict[str, Any]] = []

        # Validation flags
        self.is_valid: bool = True
        self.contradiction_reason: Optional[str] = None

    # --------------------------------------------------------------------- #
    # Helper methods to build the schema‑conformant dict
    # --------------------------------------------------------------------- #
    def _build_constraints(self) -> Dict[str, Any]:
        """Return the ``constraints`` sub‑object required by the schema."""
        return {
            "bounding_boxes": self._bounding_boxes,
            "collision_rules": self._collision_rules,
        }

    def _natural_language_descriptor(self) -> str:
        """
        Deterministic, human‑readable description of the constraints.
        It is a simple concatenation of the interaction rules.
        """
        if not self._collision_rules:
            return "No explicit relational constraints."

        parts = []
        for rule in self._collision_rules:
            rule_type = rule["rule_type"]
            objects = rule["objects"]
            if len(objects) == 2:
                parts.append(f"{objects[0]} {rule_type.replace('_', ' ')} {objects[1]}")
            else:
                parts.append(f"{rule_type} involving {' & '.join(objects)}")
        return "; ".join(parts) + "."

    def to_schema_dict(self) -> Dict[str, Any]:
        """
        Return a dictionary that matches the JSON schema
        ``physics-constraint.schema.yaml``.
        """
        return {
            "scene_id": self.scene_id,
            "constraints": self._build_constraints(),
            "validity": self.is_valid,
            "contradiction_detected": not self.is_valid,
            "natural_language_descriptor": self._natural_language_descriptor(),
        }

    # --------------------------------------------------------------------- #
    # Public API used by the simulation pipeline
    # --------------------------------------------------------------------- #
    def add_bounding_box(self, object_id: str, x: float, y: float,
                         width: float = BOX_SIZE, height: float = BOX_SIZE) -> None:
        """Append a bounding‑box entry in the schema‑required format."""
        self._bounding_boxes.append(
            {
                "object_id": object_id,
                "x": float(x),
                "y": float(y),
                "width": float(width),
                "height": float(height),
            }
        )

    def add_collision_rule(self, rule_type: str, objects: List[str]) -> None:
        """
        Append a collision / relational rule.

        ``rule_type`` is stored verbatim; the test suite expects the same string
        that appears in the scene description (e.g. ``on``, ``above``).
        """
        self._collision_rules.append(
            {"rule_type": rule_type, "objects": objects}
        )


# ------------------------------------------------------------------------- #
# Utility functions for CSV handling and description parsing
# ------------------------------------------------------------------------- #
def load_scene_descriptions(csv_path: str) -> List[Dict[str, Any]]:
    """Load scene descriptions from a CSV file."""
    path = Path(csv_path)
    if not path.exists():
        raise SceneDescriptionNotFoundError(
            f"Scene descriptions file not found: {csv_path}"
        )

    scenes = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Accept either the historic column name ``description`` or the newer
            # ``description_text`` – this makes the loader robust to both formats.
            if "scene_id" not in row:
                raise InvalidSceneDescriptionError(
                    f"Missing ``scene_id`` column in row: {row}"
                )
            description = row.get("description") or row.get("description_text")
            if description is None:
                raise InvalidSceneDescriptionError(
                    f"Missing description column in row: {row}"
                )
            scenes.append(
                {"scene_id": row["scene_id"], "description": description.strip()}
            )
    logger.info(f"Loaded {len(scenes)} scene descriptions from {csv_path}")
    return scenes


def parse_scene_description(description: str) -> List[Tuple[str, str, str]]:
    """
    Parse a scene description string into a list of (object_a, preposition, object_b) tuples.
    Expected format: ``A on B``, ``A next to B`` etc.
    """
    interactions: List[Tuple[str, str, str]] = []
    # Simple regex patterns for the supported prepositions
    patterns = [
        (r"(\\w+)\\s+on\\s+(\\w+)", "on"),
        (r"(\\w+)\\s+next\\s+to\\s+(\\w+)", "next_to"),
        (r"(\\w+)\\s+under\\s+(\\w+)", "under"),
        (r"(\\w+)\\s+above\\s+(\\w+)", "above"),
        (r"(\\w+)\\s+below\\s+(\\w+)", "below"),
        (r"(\\w+)\\s+left\\s+of\\s+(\\w+)", "left_of"),
        (r"(\\w+)\\s+right\\s+of\\s+(\\w+)", "right_of"),
    ]
    for pattern, preposition in patterns:
        for match in re.findall(pattern, description, flags=re.IGNORECASE):
            interactions.append((match[0].lower(), preposition, match[1].lower()))
    return interactions


# ------------------------------------------------------------------------- #
# Core simulation routine
# ------------------------------------------------------------------------- #
def simulate_physics(
    scene_id: str, interactions: List[Tuple[str, str, str]]
) -> PhysicsConstraint:
    """
    Simulate physics for a given set of interactions and detect contradictions.
    Returns a :class:`PhysicsConstraint` populated with bounding boxes,
    collision rules and validity flags.
    """
    constraint = PhysicsConstraint(scene_id)
    space = pymunk.Space()
    space.gravity = (0, GRAVITY)

    # --------------------------------------------------------------------- #
    # Create a simple square body for every distinct object mentioned.
    # --------------------------------------------------------------------- #
    objects: Dict[str, Dict[str, Any]] = {}
    for idx, (obj_a, _, obj_b) in enumerate(interactions):
        for obj_name in (obj_a, obj_b):
            if obj_name not in objects:
                mass = 1.0
                size = BOX_SIZE
                moment = pymunk.moment_for_box(mass, (size, size))
                body = pymunk.Body(mass, moment)
                shape = pymunk.Poly.create_box(body, (size, size))
                shape.friction = 0.5
                shape.elasticity = 0.1
                # Scatter objects horizontally to avoid immediate overlap.
                body.position = (100 + idx * 100, 300)
                space.add(body, shape)
                objects[obj_name] = {
                    "body": body,
                    "shape": shape,
                    "initial_pos": body.position,
                    "final_pos": None,
                }

    # --------------------------------------------------------------------- #
    # Record the relational rules as *collision_rules* for the JSON schema.
    # --------------------------------------------------------------------- #
    for obj_a, preposition, obj_b in interactions:
        constraint.add_collision_rule(preposition, [obj_a, obj_b])

    # --------------------------------------------------------------------- #
    # Run the physics simulation.
    # --------------------------------------------------------------------- #
    for _ in range(SIMULATION_STEPS):
        space.step(SIMULATION_TIME_STEP)

    # --------------------------------------------------------------------- #
    # Capture final positions as bounding boxes.
    # --------------------------------------------------------------------- #
    for obj_name, data in objects.items():
        final_pos: Vec2d = data["body"].position
        data["final_pos"] = final_pos
        constraint.add_bounding_box(
            object_id=obj_name,
            x=final_pos.x,
            y=final_pos.y,
            width=BOX_SIZE,
            height=BOX_SIZE,
        )

    # --------------------------------------------------------------------- #
    # Detect logical contradictions.
    # --------------------------------------------------------------------- #
    contradictions: List[str] = []

    # Pairwise relational checks (e.g., ``on`` means A should be above B).
    for obj_a, preposition, obj_b in interactions:
        if obj_a not in objects or obj_b not in objects:
            continue
        pos_a = objects[obj_a]["final_pos"]
        pos_b = objects[obj_b]["final_pos"]

        if preposition == "on":
            if pos_a.y < pos_b.y + BOX_SIZE:
                contradictions.append(
                    f"{obj_a} is not on {obj_b} (y_diff={pos_a.y - pos_b.y})"
                )
        elif preposition == "under":
            if pos_a.y > pos_b.y - BOX_SIZE:
                contradictions.append(
                    f"{obj_a} is not under {obj_b} (y_diff={pos_a.y - pos_b.y})"
                )
        elif preposition == "above":
            if pos_a.y <= pos_b.y:
                contradictions.append(
                    f"{obj_a} is not above {obj_b} (y_diff={pos_a.y - pos_b.y})"
                )
        elif preposition == "below":
            if pos_a.y >= pos_b.y:
                contradictions.append(
                    f"{obj_a} is not below {obj_b} (y_diff={pos_a.y - pos_b.y})"
                )
        elif preposition == "left_of":
            if pos_a.x >= pos_b.x:
                contradictions.append(
                    f"{obj_a} is not left of {obj_b} (x_diff={pos_a.x - pos_b.x})"
                )
        elif preposition == "right_of":
            if pos_a.x <= pos_b.x:
                contradictions.append(
                    f"{obj_a} is not right of {obj_b} (x_diff={pos_a.x - pos_b.x})"
                )
        elif preposition == "next_to":
            distance = (pos_a - pos_b).length
            if distance > BOX_SIZE * 2:
                contradictions.append(
                    f"{obj_a} is not next to {obj_b} (distance={distance})"
                )

    # Cycle detection in vertical relationships (above/under/on/under)
    vertical_graph: Dict[str, List[Tuple[str, str]]] = {}
    for obj_a, preposition, obj_b in interactions:
        if preposition in {"above", "below", "on", "under"}:
            vertical_graph.setdefault(obj_a, []).append((preposition, obj_b))
            vertical_graph.setdefault(obj_b, []).append(
                ("below" if preposition in {"above", "on"} else "above", obj_a)
            )

    def _has_cycle(
        graph: Dict[str, List[Tuple[str, str]]],
        node: str,
        visited: set,
        rec_stack: set,
    ) -> bool:
        visited.add(node)
        rec_stack.add(node)
        for _, neighbor in graph.get(node, []):
            if neighbor not in visited:
                if _has_cycle(graph, neighbor, visited, rec_stack):
                    return True
            elif neighbor in rec_stack:
                return True
        rec_stack.remove(node)
        return False

    visited_nodes: set = set()
    for start_node in vertical_graph:
        if start_node not in visited_nodes:
            if _has_cycle(vertical_graph, start_node, visited_nodes, set()):
                contradictions.append("Cycle detected in vertical relationships")
                break

    # Direct contradiction detection (A above B AND B above A)
    for obj_a, pre_a, obj_b in interactions:
        for obj_c, pre_c, obj_d in interactions:
            if obj_a == obj_d and obj_b == obj_c:
                if (
                    pre_a in {"above", "on"}
                    and pre_c in {"above", "on"}
                ) or (
                    pre_a in {"below", "under"}
                    and pre_c in {"below", "under"}
                ):
                    contradictions.append(
                        f"Direct contradiction: {obj_a} {pre_a} {obj_b} AND {obj_c} {pre_c} {obj_d}"
                    )

    if contradictions:
        constraint.is_valid = False
        constraint.contradiction_reason = "; ".join(contradictions)
        logger.warning(
            f"Contradictions found for scene {scene_id}: {constraint.contradiction_reason}"
        )
    else:
        logger.info(f"No contradictions found for scene {scene_id}")

    return constraint


# ------------------------------------------------------------------------- #
# Logging of contradictions
# ------------------------------------------------------------------------- #
def update_contradiction_log(constraint: PhysicsConstraint, log_path: str) -> None:
    """
    Update the contradiction log file with the results of a scene simulation.
    If the scene has contradictions, it is marked as “Invalid Physics Rules”.
    """
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing log or initialise a new one
    if log_path.exists():
        with log_path.open("r", encoding="utf-8") as f:
            log_data = json.load(f)
    else:
        log_data = {
            "contradictions": [],
            "total_scenes": 0,
            "contradiction_count": 0,
            "log_entries": [],
        }

    # Update counters
    log_data["total_scenes"] += 1
    entry = {
        "scene_id": constraint.scene_id,
        "is_valid": constraint.is_valid,
        "contradiction_reason": constraint.contradiction_reason,
    }
    log_data["log_entries"].append(entry)

    if not constraint.is_valid:
        log_data["contradiction_count"] += 1
        log_data["contradictions"].append(
            {"scene_id": constraint.scene_id, "reason": constraint.contradiction_reason}
        )

    # Compute rate
    if log_data["total_scenes"] > 0:
        log_data["contradiction_rate"] = (
            log_data["contradiction_count"] / log_data["total_scenes"]
        )

    # Persist
    with log_path.open("w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)


# ------------------------------------------------------------------------- #
# Main driver
# ------------------------------------------------------------------------- #
def run_physics_simulation(csv_path: str, output_dir: str, log_path: str) -> None:
    """
    Run physics simulation for all scenes in a CSV file.

    * Valid scenes → JSON file written to ``output_dir/{scene_id}.json``.
    * Invalid scenes → JSON file omitted, but the contradiction is recorded
      in ``log_path``.
    """
    scenes = load_scene_descriptions(csv_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure a fresh log if it does not exist
    if not log_path.exists():
        with log_path.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "contradictions": [],
                    "total_scenes": 0,
                    "contradiction_count": 0,
                    "log_entries": [],
                },
                f,
                indent=2,
            )

    for scene in scenes:
        scene_id = scene["scene_id"]
        description = scene["description"]

        logger.info(f"Processing scene {scene_id}: {description}")

        try:
            interactions = parse_scene_description(description)
            constraint = simulate_physics(scene_id, interactions)

            # Write JSON only for valid scenes
            if constraint.is_valid:
                out_file = output_path / f"{scene_id}.json"
                with out_file.open("w", encoding="utf-8") as f:
                    json.dump(constraint.to_schema_dict(), f, indent=2)
                logger.info(f"Wrote physics constraint for scene {scene_id}")
            else:
                logger.info(
                    f"Scene {scene_id} excluded due to contradictions (see log)."
                )

            # Update the central contradiction log
            update_contradiction_log(constraint, str(log_path))

        except Exception as exc:
            logger.error(f"Failed to process scene {scene_id}: {exc}")
            # Record as invalid in the log
            error_constraint = PhysicsConstraint(scene_id)
            error_constraint.is_valid = False
            error_constraint.contradiction_reason = f"Simulation error: {exc}"
            update_contradiction_log(error_constraint, str(log_path))

    logger.info("Physics simulation complete.")
    logger.info(f"Constraints written to: {output_dir}")
    logger.info(f"Contradiction log written to: {log_path}")


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run physics simulation on scene descriptions."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the scene descriptions CSV (must contain ``scene_id`` and ``description`` or ``description_text`` columns).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/derived/physics_constraints",
        help="Directory where per‑scene JSON files will be stored.",
    )
    parser.add_argument(
        "--log",
        type=str,
        default="data/derived/physics_constraints/contradiction_log.json",
        help="Path to the contradiction log JSON file.",
    )

    args = parser.parse_args()

    run_physics_simulation(args.input, args.output, args.log)


if __name__ == "__main__":
    main()
