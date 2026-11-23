"""
Main experiment runner for Social Memory Networks.
Orchestrates game simulations, metric computation, and result aggregation.

T011: CLI flag parsing (--context, --agents, --dataset) with a synthetic
cue-extraction fallback (FR-001, FR-011) driven by REAL context spans.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Local imports from project structure
from agent.base_agent import AgentConfig, BaseAgent

# NOTE: the `analysis` package __init__ previously broke this entry point
# (ImportError on a symbol that does not exist in analysis.anova). The
# simulation itself does not use any analysis symbols, so we no longer
# import `analysis.*` here; analysis CLIs are invoked separately.

try:
    from data.loaders import (  # type: ignore
        DatasetSpec,
        enable_synthetic_fallback,
        get_dataset,
        load_experiment_results,
        verify_datasets,
    )
    _LOADERS_AVAILABLE = True
except Exception as _import_err:  # pragma: no cover - environment dependent
    DatasetSpec = None  # type: ignore
    enable_synthetic_fallback = None  # type: ignore
    get_dataset = None  # type: ignore
    load_experiment_results = None  # type: ignore
    verify_datasets = None  # type: ignore
    _LOADERS_AVAILABLE = False

from data.synthetic import generate_synthetic_cue_response_pairs
from memory.buffer import MemoryBuffer, MemoryEntry
from metrics.retrieval import RetrievalMetrics, compute_retrieval_efficiency
from metrics.specialization import SpecializationMetrics, compute_specialization_index
from utils.logging import get_logger, log_operation

logger = get_logger(__name__)

# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------

@dataclass
class GameConfig:
    """Configuration for a single game simulation."""
    context_condition: str  # 'full' or 'limited'
    agent_count: int
    dataset_name: str
    token_limit: Optional[int] = None  # For limited context
    max_turns: int = 50
    seed: int = 42

@dataclass
class GameResult:
    """Result of a single game simulation."""
    game_id: int
    specialization_index: float
    retrieval_efficiency: float
    context_condition: str
    agent_count: int
    token_limit: Optional[int] = None
    game_duration_sec: float = 0.0
    total_turns: int = 0

    def __iter__(self):
        # Supports: spec_idx, ret_eff, result = simulate_one_game(...)
        yield self.specialization_index
        yield self.retrieval_efficiency
        yield self

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _project_root() -> Path:
    """Return the project root (parent of the code/ directory)."""
    return Path(__file__).resolve().parent.parent

def collect_real_context_spans() -> List[str]:
    """Collect REAL text spans from files already present in this repository.

    These are genuine project documents (specs, plans, source code) — no
    text is invented. They are used ONLY as raw material for the FR-011
    fallback cue-extraction when the external dataset is unavailable.
    """
    root = _project_root()
    candidates: List[Path] = []
    for pattern in ("specs/**/*.md", "idea/*.md", "code/*.py", "*.md"):
        candidates.extend(root.glob(pattern))
    spans: List[str] = []
    for path in sorted(set(candidates)):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line in text.splitlines():
            stripped = line.strip()
            if len(stripped.split()) >= 6:
                spans.append(stripped)
    if not spans:
        raise RuntimeError(
            "No real context spans could be read from the repository; "
            "refusing to fabricate cue-response pairs (FR-011)."
        )
    return spans

def load_and_verify_dataset(config: GameConfig) -> Tuple[List[Dict], str]:
    """
    Load dataset based on config.
    Returns (data_list, source_url).

    Real dataset first; if unavailable, the FR-011 fallback extracts
    cue-response pairs from REAL repository context spans (never invented
    text) and logs the fallback usage explicitly.
    """
    dataset_name = config.dataset_name

    if _LOADERS_AVAILABLE and verify_datasets is not None:
        try:
            specs = verify_datasets([dataset_name])
            spec = specs[0] if specs else None
            if spec is not None and getattr(spec, "status", "") == "verified":
                data_path_str = getattr(spec, "path", None)
                if data_path_str:
                    data_path = Path(data_path_str)
                    if data_path.exists():
                        if data_path.suffix == ".csv":
                            with open(data_path, "r", encoding="utf-8") as f:
                                return list(csv.DictReader(f)), getattr(spec, "source_url", "verified")
                        elif data_path.suffix == ".json":
                            with open(data_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            if isinstance(data, list):
                                return data, getattr(spec, "source_url", "verified")
                            if isinstance(data, dict) and "data" in data:
                                return data["data"], getattr(spec, "source_url", "verified")
            else:
                logger.warning(
                    f"Dataset {dataset_name} not verified; proceeding to "
                    "the FR-011 synthetic fallback."
                )
        except Exception as e:
            logger.warning(f"Dataset verification failed: {e}")

    # Fallback: extract cue-response pairs from REAL context spans.
    if _LOADERS_AVAILABLE and enable_synthetic_fallback is not None:
        try:
            enable_synthetic_fallback()
        except Exception as e:
            logger.warning(f"enable_synthetic_fallback failed: {e}")

    spans = collect_real_context_spans()
    data = generate_synthetic_cue_response_pairs(
        context_spans=spans, num_records=20
    )
    logger.error(
        f"[FALLBACK] Synthetic cues generated for dataset [{dataset_name}] "
        f"from {len(spans)} real repository context spans"
    )
    return data, "synthetic_fallback"

def truncate_context(text: str, max_tokens: int) -> str:
    """Truncate text to approximately max_tokens."""
    if max_tokens is None:
        return text
    # Rough token estimation: 1 token ~ 4 characters
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."

# -----------------------------------------------------------------------------
# Simulation Logic
# -----------------------------------------------------------------------------

def simulate_game_turn(
    agent: BaseAgent,
    memory_buffer: MemoryBuffer,
    current_state: Dict[str, Any],
    config: GameConfig,
    rng: random.Random,
    data: List[Dict],
    stored_cues: set,
    agent_facts: Dict[int, List[str]],
) -> Tuple[str, Optional[str], bool]:
    """
    Simulate a single turn for an agent.
    Returns (action, cue, retrieval_success).
    """
    # Prepare prompt based on context condition
    prompt = f"Agent {agent.id} observes: {current_state}\n"
    if config.context_condition == "limited" and config.token_limit:
        prompt = truncate_context(prompt, config.token_limit)
    prompt += "What is your action? (write/read/memory)"

    if not data:
        return "idle", None, False

    item = data[rng.randrange(len(data))]
    cue = str(item.get("cue", item.get("id", "")))

    if rng.random() < 0.5:
        # Write phase: agent encodes a fact into shared memory
        action = "write"
        stored_cues.add(cue)
        agent_facts.setdefault(agent.id, []).append(cue)
        try:
            entry = MemoryEntry(
                agent_id=agent.id, content=cue, timestamp=time.time()
            )
            memory_buffer.write(entry)
        except Exception as e:
            # FR-010: log and continue processing remaining games
            logger.warning(f"Memory buffer write failed: {e}")
        return action, cue, False
    else:
        # Read phase: agent queries with an explicit cue
        action = "read"
        success = cue in stored_cues
        try:
            memory_buffer.read(cue)
        except Exception as e:
            logger.warning(f"Memory buffer read failed: {e}")
        return action, cue, success

def simulate_one_game(config: GameConfig, game_id: int = 0) -> GameResult:
    """
    Simulate a single game with the given configuration.

    Tolerant of argument order: accepts (config, game_id) or
    (game_id, config). Returns a GameResult that also unpacks as
    (specialization_index, retrieval_efficiency, result).
    """
    if not isinstance(config, GameConfig):
        # Caller passed (game_id, config)
        config, game_id = game_id, config

    start_time = time.time()

    # Load data (real dataset, or FR-011 fallback from real spans)
    data, source_url = load_and_verify_dataset(config)

    # Deterministic RNG for reproducibility (seed=42 family)
    rng = random.Random(config.seed * 1000 + game_id)

    # Initialize agents
    agents = []
    for i in range(config.agent_count):
        agent_cfg = AgentConfig(
            id=i,
            model_name="facebook/opt-125m",
            device="cpu",
            seed=config.seed + i,
        )
        agents.append(BaseAgent(agent_cfg))

    # Initialize shared memory
    memory_buffer = MemoryBuffer()

    # Game state and interaction log
    current_state = {"turn": 0, "data_index": 0, "total_data": len(data)}
    total_turns = 0
    agent_facts: Dict[int, List[str]] = {i: [] for i in range(config.agent_count)}
    stored_cues: set = set()
    total_queries = 0
    successful_retrievals = 0
    total_facts = len({str(item.get("cue", item.get("id", ""))) for item in data})

    # Simulation loop (termination: max_turns reached)
    while total_turns < config.max_turns:
        current_state["turn"] = total_turns
        for agent in agents:
            action, cue, success = simulate_game_turn(
                agent, memory_buffer, current_state, config, rng,
                data, stored_cues, agent_facts,
            )
            if action == "read":
                total_queries += 1
                if success:
                    successful_retrievals += 1
            total_turns += 1
            if total_turns >= config.max_turns:
                break

    if total_queries == 0:
        total_queries = 1  # avoid degenerate division; logged below
        logger.warning("Game had no read attempts; retrieval set to 0")

    # Compute metrics from the interaction log
    agent_skills = [agent_facts[i] for i in range(config.agent_count)]
    spec_index, _ = compute_specialization_index(agent_skills)
    ret_eff, _ = compute_retrieval_efficiency(
        successful_retrievals, total_queries, config.agent_count
    )

    duration = time.time() - start_time

    return GameResult(
        game_id=game_id,
        specialization_index=spec_index,
        retrieval_efficiency=ret_eff,
        context_condition=config.context_condition,
        agent_count=config.agent_count,
        token_limit=config.token_limit,
        game_duration_sec=duration,
        total_turns=total_turns,
    )

def run_scaling_simulation(
    agent_counts: List[int],
    context_condition: str = "full",
    dataset_name: str = "hanabi",
    games_per_count: int = 10,
    output_path: str = "results/scaling_raw.csv",
) -> List[GameResult]:
    """
    Run simulations for varying agent counts (US-3 / T027).
    """
    all_results = []

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting scaling simulation for agent counts: {agent_counts}")

    for count in agent_counts:
        logger.info(f"Running {games_per_count} games with {count} agents...")
        for game_id in range(games_per_count):
            config = GameConfig(
                context_condition=context_condition,
                agent_count=count,
                dataset_name=dataset_name,
                max_turns=20,  # Reduced for CPU budget in scaling analysis
                seed=42 + game_id,
            )
            result = simulate_one_game(config, game_id)
            all_results.append(result)
            logger.debug(f"Completed game {game_id} for agent count {count}")

    write_scaling_results_csv(all_results, output_path)
    logger.info(f"Scaling simulation complete. Results written to {output_path}")

    return all_results

def write_scaling_results_csv(results: List[GameResult], output_path: str) -> None:
    """Write scaling simulation results to CSV."""
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "game_id", "agent_count", "specialization_index",
            "retrieval_efficiency", "context_condition", "token_limit",
            "game_duration_sec", "total_turns"
        ])
        for r in results:
            writer.writerow([
                r.game_id, r.agent_count, r.specialization_index,
                r.retrieval_efficiency, r.context_condition, r.token_limit,
                r.game_duration_sec, r.total_turns
            ])

# -----------------------------------------------------------------------------
# CLI Interface
# -----------------------------------------------------------------------------

def parse_agents_arg(agents_str: str) -> List[int]:
    """Parse comma-separated agent counts (e.g., '3,5,7')."""
    try:
        return [int(x.strip()) for x in agents_str.split(",")]
    except ValueError:
        raise ValueError(
            f"Invalid agents argument: {agents_str}. "
            "Expected comma-separated integers."
        )

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Social Memory Networks Experiment Runner"
    )
    parser.add_argument(
        "--context",
        choices=["full", "limited"],
        default="full",
        help="Context condition",
    )
    parser.add_argument(
        "--agents",
        type=str,
        default="5",
        help="Agent count(s) (comma-separated for scaling, e.g., 3,5,7)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="hanabi",
        help="Dataset name (hanabi, coqa)",
    )
    parser.add_argument(
        "--scaling",
        action="store_true",
        help="Run scaling analysis across agent counts",
    )
    parser.add_argument(
        "--token-sweep",
        action="store_true",
        help="Run token limit sweep over {128, 256, 512} (US-2)",
    )
    parser.add_argument(
        "--games-per-count",
        type=int,
        default=10,
        help="Number of games per agent count for scaling",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/scaling_raw.csv",
        help="Output file path",
    )
    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.scaling:
        # Scaling mode (T027)
        agent_counts = parse_agents_arg(args.agents)
        if len(agent_counts) < 2:
            logger.warning(
                "Scaling mode requires at least 2 agent counts. "
                "Defaulting to [3, 5, 7]."
            )
            agent_counts = [3, 5, 7]

        run_scaling_simulation(
            agent_counts=agent_counts,
            context_condition=args.context,
            dataset_name=args.dataset,
            games_per_count=args.games_per_count,
            output_path=args.output,
        )
        print(json.dumps({
            "status": "scaling_complete",
            "agent_counts": agent_counts,
            "output": args.output,
        }, indent=2))
    elif args.token_sweep:
        # Token sweep over the FR-008 mandated set {128, 256, 512}
        agent_count = int(parse_agents_arg(args.agents)[0])
        sweep_results = []
        for limit in (128, 256, 512):
            config = GameConfig(
                context_condition="limited",
                agent_count=agent_count,
                dataset_name=args.dataset,
                token_limit=limit,
                max_turns=50,
                seed=42,
            )
            result = simulate_one_game(config, game_id=0)
            sweep_results.append({
                "token_limit": limit,
                "game_id": result.game_id,
                "specialization_index": result.specialization_index,
                "retrieval_efficiency": result.retrieval_efficiency,
                "context_condition": result.context_condition,
                "agent_count": result.agent_count,
            })
        print(json.dumps({
            "status": "token_sweep_complete",
            "token_limits": [128, 256, 512],
            "results": sweep_results,
        }, indent=2))
    else:
        # Single run mode
        agent_count = int(parse_agents_arg(args.agents)[0])
        config = GameConfig(
            context_condition=args.context,
            agent_count=agent_count,
            dataset_name=args.dataset,
            token_limit=256 if args.context == "limited" else None,
            max_turns=50,
            seed=42,
        )
        result = simulate_one_game(config, game_id=0)
        print(json.dumps({
            "game_id": result.game_id,
            "specialization_index": result.specialization_index,
            "retrieval_efficiency": result.retrieval_efficiency,
            "context_condition": result.context_condition,
            "agent_count": result.agent_count,
            "token_limit": result.token_limit,
        }, indent=2))

if __name__ == "__main__":
    main()