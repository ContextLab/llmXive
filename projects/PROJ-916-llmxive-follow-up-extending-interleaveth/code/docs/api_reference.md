# API Reference

## Data Models

### `src/data_models.py`

- `ObjectNode`: Represents an object in a scene graph
- `RelationshipEdge`: Represents a relationship between objects
- `SceneGraph`: Container for objects and relationships
- `CritiqueStep`: Stores critique feedback
- `TrajectoryLog`: Logs the full agentic trajectory

## Simulator

### `src/simulator/parser.py`

- `parse_caption_to_scene_description(caption: str) -> SceneDescription`
- `parse_to_json(scene: SceneDescription) -> str`
- `parse_to_dict(scene: SceneDescription) -> dict`

### `src/simulator/noise_injector.py`

- `remove_objects(scene: SceneDescription, ratio: float) -> NoiseInjectionResult`
- `swap_relationships(scene: SceneDescription, ratio: float) -> NoiseInjectionResult`
- `inject_noise(scene: SceneDescription, mode: str) -> NoiseInjectionResult`
- `calculate_noise_ratio(original: SceneDescription, modified: SceneDescription) -> float`

### `src/simulator/validator.py`

- `validate_scene_description(scene: SceneDescription) -> ValidationResult`
- `validate_scene_graph(graph: SceneGraph) -> ValidationResult`
- `filter_ambiguous_samples(scenes: List[SceneDescription]) -> List[SceneDescription]`
- `detect_ambiguous_relationships(scene: SceneDescription) -> List[AmbiguityFlag]`

### `src/simulator/simulator.py`

- `run_simulation(prompt: str, mode: str) -> SimulationResult`

## Agents

### `src/agents/critic.py`

- `evaluate(generated: SceneDescription, prompt: str, ground_truth: SceneGraph) -> CritiqueStep`

### `src/agents/planner.py`

- `generate_intent(prompt: str, feedback: Optional[CritiqueStep]) -> str`
- `next_steps(intent: str) -> List[str]`

### `src/agents/generator.py`

- `reconstruct(prompt: str, intent: str) -> SceneDescription`

## Pipeline

### `src/pipeline/orchestrator.py`

- `run_loop(samples: List[SceneDescription], threshold: float) -> List[TrajectoryLog]`

## Metrics

### `src/stats/simulator_metrics.py`

- `calculate_graph_edit_distance(graph1: SceneGraph, graph2: SceneGraph) -> float`
- `calculate_error_rate(simulated: SceneGraph, ground_truth: SceneGraph) -> float`
- `verify_noise_injection_target(actual_ratio: float, target_range: Tuple[float, float]) -> bool`

### `src/stats/generator_metrics.py`

- `calculate_generator_error_rate(generated: SceneDescription, prompt: str) -> float`
- `evaluate_generator_against_prompt(generated: SceneDescription, prompt: str) -> GeneratorMetrics`

### `src/stats/analyzer.py`

- `paired_t_test(group1: List[float], group2: List[float]) -> Tuple[float, float]`
- `wilcoxon_test(group1: List[float], group2: List[float]) -> Tuple[float, float]`
- `cohens_d(group1: List[float], group2: List[float]) -> float`

### `src/stats/report_generator.py`

- `generate_report(results: Dict) -> str`

## Utils

### `src/utils/logging.py`

- `track_step(step_name: str) -> ContextManager`
- `start_tracing() -> None`
- `stop_tracing() -> MemorySnapshot`

### `src/utils/checksum.py`

- `verify_checksum(file_path: str, expected_hash: str) -> bool`
