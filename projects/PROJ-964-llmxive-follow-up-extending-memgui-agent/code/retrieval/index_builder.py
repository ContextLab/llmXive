"""
Index Builder for Semantic Recall Module.

This module implements an in-memory index builder that constructs a searchable
index from an agent's folded history. The index maps step indices to their
corresponding state/action snippets for efficient retrieval during long-horizon
task execution.

The index is designed to be lightweight and fit within memory constraints
(<7GB RAM) while supporting fast lookups for the recall agent.
"""
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from utils.config import get_project_root, get_data_dir


@dataclass
class IndexEntry:
    """
    Represents a single entry in the retrieval index.

    Attributes:
        step_id: Unique identifier for the step (trajectory_id + step_index)
        trajectory_id: The ID of the trajectory this step belongs to
        step_index: The index of the step within the trajectory
        state_snippet: The state representation at this step
        action_snippet: The action taken at this step (if available)
        folded_context: The folded/summarized context at this step
        embedding_key: A key used to retrieve the embedding from the retriever
    """
    step_id: str
    trajectory_id: str
    step_index: int
    state_snippet: str
    action_snippet: Optional[str] = None
    folded_context: Optional[str] = None
    embedding_key: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary for serialization."""
        return {
            "step_id": self.step_id,
            "trajectory_id": self.trajectory_id,
            "step_index": self.step_index,
            "state_snippet": self.state_snippet,
            "action_snippet": self.action_snippet,
            "folded_context": self.folded_context,
            "embedding_key": self.embedding_key,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IndexEntry":
        """Create an entry from a dictionary."""
        return cls(
            step_id=data["step_id"],
            trajectory_id=data["trajectory_id"],
            step_index=data["step_index"],
            state_snippet=data["state_snippet"],
            action_snippet=data.get("action_snippet"),
            folded_context=data.get("folded_context"),
            embedding_key=data.get("embedding_key"),
        )


class IndexBuilder:
    """
    Builds and manages an in-memory index for semantic recall.

    This class processes trajectory data and creates an index that maps
    step identifiers to their corresponding content, enabling efficient
    retrieval during agent execution.

    The index supports:
    - Building from trajectory JSONL files
    - In-memory storage of all index entries
    - Serialization/deserialization for persistence
    - Querying by trajectory ID and step range
    """

    def __init__(self, trajectory_file: Optional[str] = None):
        """
        Initialize the IndexBuilder.

        Args:
            trajectory_file: Path to the JSONL file containing trajectories.
                             If None, the index starts empty.
        """
        self.entries: Dict[str, IndexEntry] = {}
        self.trajectory_index: Dict[str, List[str]] = {}  # trajectory_id -> [step_ids]
        self._built = False
        self._source_file: Optional[str] = trajectory_file

        if trajectory_file:
            self.build_from_file(trajectory_file)

    def _generate_step_id(self, trajectory_id: str, step_index: int) -> str:
        """Generate a unique step ID."""
        return f"{trajectory_id}_step_{step_index}"

    def _fold_context(self, state_snippet: str, action_snippet: Optional[str],
                      step_index: int) -> str:
        """
        Create a folded context representation.

        This creates a compact representation of the step that can be used
        for semantic similarity matching.

        Args:
            state_snippet: The state representation
            action_snippet: The action taken (optional)
            step_index: The step index for context

        Returns:
            A folded string representation of the step context
        """
        context_parts = [
            f"Step {step_index}:",
            f"State: {state_snippet}",
        ]
        if action_snippet:
            context_parts.append(f"Action: {action_snippet}")

        return " | ".join(context_parts)

    def build_from_file(self, file_path: str) -> None:
        """
        Build the index from a JSONL trajectory file.

        Args:
            file_path: Path to the JSONL file containing trajectories.

        Raises:
            FileNotFoundError: If the file does not exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Trajectory file not found: {file_path}")

        self.entries.clear()
        self.trajectory_index.clear()

        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    trajectory = json.loads(line)
                except json.JSONDecodeError as e:
                    raise json.JSONDecodeError(
                        f"Invalid JSON at line {line_num}: {e.msg}",
                        e.doc, e.pos
                    )

                trajectory_id = trajectory.get("trajectory_id", f"unknown_{line_num}")
                steps = trajectory.get("steps", [])

                if not steps:
                    continue

                self.trajectory_index[trajectory_id] = []

                for step in steps:
                    step_index = step.get("step_index", 0)
                    state = step.get("state", "")
                    action = step.get("action")

                    step_id = self._generate_step_id(trajectory_id, step_index)
                    folded = self._fold_context(state, action, step_index)

                    entry = IndexEntry(
                        step_id=step_id,
                        trajectory_id=trajectory_id,
                        step_index=step_index,
                        state_snippet=state,
                        action_snippet=action,
                        folded_context=folded,
                    )

                    self.entries[step_id] = entry
                    self.trajectory_index[trajectory_id].append(step_id)

        self._built = True

    def get_entries_for_trajectory(self, trajectory_id: str) -> List[IndexEntry]:
        """
        Retrieve all index entries for a specific trajectory.

        Args:
            trajectory_id: The ID of the trajectory

        Returns:
            List of IndexEntry objects for the trajectory, sorted by step_index
        """
        step_ids = self.trajectory_index.get(trajectory_id, [])
        entries = [self.entries[step_id] for step_id in step_ids if step_id in self.entries]
        return sorted(entries, key=lambda e: e.step_index)

    def get_entries_in_range(self, trajectory_id: str,
                             start_index: int, end_index: int) -> List[IndexEntry]:
        """
        Retrieve entries within a specific step range.

        Args:
            trajectory_id: The ID of the trajectory
            start_index: Start step index (inclusive)
            end_index: End step index (inclusive)

        Returns:
            List of IndexEntry objects within the range
        """
        all_entries = self.get_entries_for_trajectory(trajectory_id)
        return [
            entry for entry in all_entries
            if start_index <= entry.step_index <= end_index
        ]

    def get_entry_by_step_id(self, step_id: str) -> Optional[IndexEntry]:
        """
        Retrieve a specific entry by its step ID.

        Args:
            step_id: The unique step identifier

        Returns:
            The IndexEntry if found, None otherwise
        """
        return self.entries.get(step_id)

    def get_all_step_ids(self) -> List[str]:
        """
        Get all step IDs in the index.

        Returns:
            List of all step IDs
        """
        return list(self.entries.keys())

    def get_trajectory_ids(self) -> List[str]:
        """
        Get all trajectory IDs in the index.

        Returns:
            List of all trajectory IDs
        """
        return list(self.trajectory_index.keys())

    def get_entry_count(self) -> int:
        """
        Get the total number of entries in the index.

        Returns:
            Total count of index entries
        """
        return len(self.entries)

    def get_trajectory_count(self) -> int:
        """
        Get the number of trajectories in the index.

        Returns:
            Number of trajectories
        """
        return len(self.trajectory_index)

    def is_built(self) -> bool:
        """Check if the index has been built."""
        return self._built

    def save_index(self, output_path: str) -> None:
        """
        Save the index to a JSON file.

        Args:
            output_path: Path where the index will be saved
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "entries": {step_id: entry.to_dict() for step_id, entry in self.entries.items()},
            "trajectory_index": self.trajectory_index,
            "metadata": {
                "entry_count": self.get_entry_count(),
                "trajectory_count": self.get_trajectory_count(),
                "built": self._built,
            }
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_index(cls, file_path: str) -> "IndexBuilder":
        """
        Load an index from a JSON file.

        Args:
            file_path: Path to the saved index file

        Returns:
            A new IndexBuilder instance with loaded data
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Index file not found: {file_path}")

        builder = cls()

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        builder.entries = {
            step_id: IndexEntry.from_dict(entry_data)
            for step_id, entry_data in data["entries"].items()
        }
        builder.trajectory_index = data["trajectory_index"]
        builder._built = data["metadata"]["built"]

        return builder

    def __len__(self) -> int:
        """Return the number of entries in the index."""
        return self.get_entry_count()

    def __contains__(self, step_id: str) -> bool:
        """Check if a step_id exists in the index."""
        return step_id in self.entries

    def __repr__(self) -> str:
        return (
            f"IndexBuilder(entries={self.get_entry_count()}, "
            f"trajectories={self.get_trajectory_count()}, built={self._built})"
        )


def main():
    """
    Main function to demonstrate index building.

    This function loads the synthetic benchmark trajectories and builds
    an in-memory index, then prints summary statistics.
    """
    project_root = get_project_root()
    trajectory_file = project_root / "data" / "synthetic_benchmark" / "trajectories.jsonl"

    if not trajectory_file.exists():
        print(f"Error: Trajectory file not found at {trajectory_file}")
        print("Please run the synthetic benchmark generation first.")
        return

    print(f"Building index from: {trajectory_file}")
    builder = IndexBuilder(str(trajectory_file))

    print(f"\nIndex Statistics:")
    print(f"  Total entries: {builder.get_entry_count()}")
    print(f"  Total trajectories: {builder.get_trajectory_count()}")
    print(f"  Index built: {builder.is_built()}")

    # Save the index
    output_path = project_root / "data" / "retrieval" / "index.json"
    builder.save_index(str(output_path))
    print(f"\nIndex saved to: {output_path}")

    # Demonstrate retrieval
    if builder.get_trajectory_count() > 0:
        sample_traj_id = list(builder.trajectory_index.keys())[0]
        print(f"\nSample trajectory: {sample_traj_id}")

        entries = builder.get_entries_for_trajectory(sample_traj_id)
        print(f"  Steps in trajectory: {len(entries)}")

        if entries:
            first_entry = entries[0]
            print(f"  First step: {first_entry.step_id}")
            print(f"  State snippet: {first_entry.state_snippet[:100]}...")


if __name__ == "__main__":
    main()