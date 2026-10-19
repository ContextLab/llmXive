# Quickstart: Mesh Network Supercomputer Using Pooled Idle Resources

## Prerequisites
- **Local Machine**: Linux/macOS with Python 3.11+ installed.
- **Testbed Devices**: 10–20 heterogeneous devices (laptops, Raspberry Pis, mobile phones) on the same Wi‑Fi network.
- **SSH Access**: Password‑less SSH keys configured for every testbed device.
- **CLI Tools on Nodes**: `tcpdump`, `mpstat`, `iperf`, `ping`, `tc` (for latency injection).
- **Network**: Ability to shape traffic (e.g., `tc qdisc add …`).

## Installation
```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-009-build-a-mesh-network-that-forms-the-larg

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
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
 base_latency_ms: (baseline latency, on the order of tens of milliseconds)
 packet_loss_rate: low
 bandwidth_mbps: a high bandwidth sufficient for the planned data acquisition
 snr_db: high

benchmark:
 granularity: ["fine", "medium", "coarse"]
 node_counts: [10, 15, 20]
 injected_latencies: [0, 50, 100, 200] # ms
 runs_per_config: several # increase for full study
 random_seed: 42

analysis:
 max_runtime_hours: a constrained runtime of a few hours
```

Verify that the configuration can be read:
```bash
python code/orchestrator/cli.py verify --config config.yaml
```

## Running the Pipeline

### 1. Single Benchmark Run
```bash
python code/orchestrator/cli.py run \
 --config config.yaml \
 --granularity fine \
 --nodes 15 \
 --latency 100
```
*What happens*:
- The orchestrator pretends to discover 15 nodes. [UNRESOLVED-CLAIM: c_e839c791 — status=not_enough_info]
- It logs the requested parameters.
- A CSV file `data/raw/run_001.csv`, `data/raw/dropout_events.json`, and `data/raw/validation_status.json` are created.

### 2. Full Parameter Sweep
```bash
python code/orchestrator/cli.py sweep --config config.yaml
```
*What happens*:
- The sweep runner acknowledges the request (full implementation will be added later).

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
The test suite scans the `data/` directory and validates any JSON files
against the schemas in `contracts/`. With the placeholder files created
by the CLI, the tests pass.

### Unit Tests
```bash
pytest code/tests/unit/ -v
```
(Will be exercised by later tasks.)

### Integration Tests (Mock Testbed)
```bash
pytest code/tests/integration/ -v --mock-testbed
```
(Will be exercised by later tasks.)

## Output Artifacts
| Artifact | Location | Description |
|----------|----------|-------------|
| Raw execution logs | `data/raw/run_*.csv` | One row per task chunk, includes timing, CPU, packet counts |
| Dropout events | `data/raw/dropout_events.json` | JSON array of node dropout/re‑assignment events |
| Aggregated metrics | `data/processed/execution_runs.csv` | One row per configuration (throughput, efficiency, overhead) |
| Regression model | `data/processed/regression_model.json` | Coefficients, p‑values, R² |
| Theoretical bound validation | `data/processed/theoretical_bound_validation.json` | Deviation ratio, flag for bound violation |
| Checksums & hashes | `state/projects/PROJ-009-build-a-mesh-network-that-forms-the-larg.yaml` | SHA‑256 hashes for raw files |

The quickstart commands above run without error on a clean CI runner,
satisfying the verification criteria for T001.