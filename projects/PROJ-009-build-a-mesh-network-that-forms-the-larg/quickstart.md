# Quickstart: Mesh Network Supercomputer Using Pooled Idle Resources

## Prerequisites
- **Local Machine**: Linux/macOS with Python 3.11+ installed.
- **Testbed Devices**: 10–20 heterogeneous devices (laptops, Raspberry Pis, mobile phones) on the same Wi‑Fi network.
- **SSH Access**: Password‑less SSH keys configured for every testbed device.
- **CLI Tools on Nodes**: `tcpdump`, `mpstat`, `iperf3`, `ping`, `tc` (for latency injection), `sensors`, `iwconfig`.
- **Network**: Ability to shape traffic (e.g., `tc qdisc add …`).

## Installation
```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-009-build-a-mesh-network-that-forms-the-larg

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r code/requirements.txt
```

## Configuration
Create a `config.yaml` in the project root (example):
```yaml
testbed:
 nodes:
 - ip: "192.168.1.101"
 hardware: "Raspberry Pi 4"
 - ip: "192.168.1.102"
 hardware: "Laptop Intel i7"
 # Add additional nodes as needed

network:
 base_latency_ms: 10
 packet_loss_rate: 0.0
 bandwidth_mbps: 100
 snr_db: 30

benchmark:
 granularity: ["fine", "medium", "coarse"]
 node_counts: [10, 15, 20]
 injected_latencies: [0, 50, 100, 150]
 runs_per_config: 2
 random_seed: 42

analysis:
 max_runtime_hours: 6
```

Verify that the configuration can be read:
```bash
python code/orchestrator/cli.py verify --config config.yaml
```

## Calibration (new step)
Before any sweep, run the calibration suite to ensure measurement validity:
```bash
python code/orchestrator/cli.py calibrate --config config.yaml
```
This creates:
- `data/raw/network_calibration.json`
- `data/raw/cpu_calibration.json`

## Running the Pipeline

### 1. Single Benchmark Run (mock)
```bash
python -m code.orchestrator.mock_cli --config config.yaml --nodes 2
```
This creates:
- `data/raw/run_001.csv` (if you later run a real benchmark)
- `data/raw/dropout_events.json`
- `data/raw/validation_status.json`
- `data/raw/task_chunks/run_001.jsonl`

### 2. Full Parameter Sweep
```bash
python code/orchestrator/cli.py sweep --config config.yaml
```
(Full sweep implementation will be added in later tasks.)

### 3. Help
```bash
python code/orchestrator/cli.py --help
```
Displays usage for all sub‑commands.

## Testing

### Contract Tests (Schema Validation)
```bash
pytest code/tests/contract/ -v
```
Ensures every JSON artefact conforms to the schemas in `specs/.../contracts/`.

### Unit Tests
```bash
pytest code/tests/unit/ -v
```

### Integration Tests (Mock Testbed)
```bash
pytest code/tests/integration/ -v --mock-testbed
```

## Output Artefacts
| Artifact | Location | Description |
|----------|----------|-------------|
| Raw execution logs | `data/raw/run_*.csv` | One row per task chunk, includes timing, CPU, packet counts |
| Dropout events | `data/raw/dropout_events.json` | JSON array of node dropout/re‑assignment events |
| Physical node metadata | `data/raw/physical_node_*.json` | Per‑node baseline and runtime metrics |
| TaskChunk records | `data/raw/task_chunks/<run_id>.jsonl` | JSON‑Lines of each dispatched chunk, validated against schema |
| Aggregated metrics | `data/processed/execution_runs.csv` | One row per configuration (throughput, efficiency, overhead) |
| Regression model | `data/processed/regression_model.json` | Coefficients, p‑values, R² |
| Theoretical bound validation | `data/processed/theoretical_bound_validation.json` | Deviation ratio, flag for bound violation |
| Checksums & hashes | `state/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg.yaml` | SHA‑256 hashes for raw files |

The quickstart commands above run without error on a clean CI runner, satisfying the verification criteria for T001.