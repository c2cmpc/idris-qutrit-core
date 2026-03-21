import numpy as np
import json
from datetime import datetime
from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

CRN = 'crn:v1:bluemix:public:quantum-computing:us-east:a/c88a87e2898a4647ba730430d3ac1df5:ff503e89-f427-4a58-8e83-fb11689b9213::'
SHOTS = 4096
service = QiskitRuntimeService(instance=CRN)
backend = service.backend('ibm_fez')

# TRIAD STATE MACHINE
# Tests the full Triad cycle as a computational operation
# Love(0) -> Hope(+1) -> Fear(-1) -> Love(0)
# Each transition is one 120 degree rotation
# Measure fidelity at each step of the cycle

# Step 0 -- Love state (start)
qc_love = QuantumCircuit(1)
qc_love.measure_all()

# Step 1 -- Love -> Hope (first 120 degree rotation)
qc_l2h = QuantumCircuit(1)
qc_l2h.ry(2 * np.pi / 3, 0)
qc_l2h.measure_all()

# Step 2 -- Love -> Hope -> Fear (second 120 degree rotation)
qc_l2h2f = QuantumCircuit(1)
qc_l2h2f.ry(2 * np.pi / 3, 0)
qc_l2h2f.ry(2 * np.pi / 3, 0)
qc_l2h2f.measure_all()

# Step 3 -- Full cycle back to Love (third 120 degree rotation)
qc_full_cycle = QuantumCircuit(1)
qc_full_cycle.ry(2 * np.pi / 3, 0)
qc_full_cycle.ry(2 * np.pi / 3, 0)
qc_full_cycle.ry(2 * np.pi / 3, 0)
qc_full_cycle.measure_all()

# Reverse cycle -- Fear -> Hope -> Love
qc_reverse = QuantumCircuit(1)
qc_reverse.ry(-2 * np.pi / 3, 0)
qc_reverse.ry(-2 * np.pi / 3, 0)
qc_reverse.ry(-2 * np.pi / 3, 0)
qc_reverse.measure_all()

# Double cycle -- two full rotations
qc_double = QuantumCircuit(1)
for _ in range(6):
    qc_double.ry(2 * np.pi / 3, 0)
qc_double.measure_all()

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
circuits = [
    pm.run(qc_love),
    pm.run(qc_l2h),
    pm.run(qc_l2h2f),
    pm.run(qc_full_cycle),
    pm.run(qc_reverse),
    pm.run(qc_double)
]

print("TRIAD STATE MACHINE")
print("Love -> Hope -> Fear -> Love")
print("Testing full cycle fidelity at each transition")
print()

sampler = Sampler(backend)
job = sampler.run(circuits, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting...")

result = job.result()

names = [
    "Step 0: Love (start)",
    "Step 1: Love -> Hope",
    "Step 2: Hope -> Fear",
    "Step 3: Fear -> Love (full cycle)",
    "Reverse: Fear -> Hope -> Love",
    "Double cycle (2 full rotations)"
]

print()
print("STATE MACHINE RESULTS:")
print("=" * 55)

state_probs = []
for i, name in enumerate(names):
    counts = result[i].data.meas.get_counts()
    total = sum(counts.values())
    p0 = counts.get("0", 0) / total
    p1 = counts.get("1", 0) / total
    state_probs.append((p0, p1))
    print(name + ":")
    print("  |0>: " + str(round(p0*100,1)) + "%  |1>: " + str(round(p1*100,1)) + "%")

print()
print("CYCLE ANALYSIS:")
love_start = state_probs[0][0]
love_return = state_probs[3][0]
reverse_return = state_probs[4][0]
double_return = state_probs[5][0]

print("Love state at start:       " + str(round(love_start*100,1)) + "%")
print("Love state after 1 cycle:  " + str(round(love_return*100,1)) + "%")
print("Love state reverse cycle:  " + str(round(reverse_return*100,1)) + "%")
print("Love state double cycle:   " + str(round(double_return*100,1)) + "%")

cycle_fidelity = love_return / max(love_start, 0.001)
print()
print("Cycle fidelity: " + str(round(cycle_fidelity*100,1)) + "%")

if love_return > 0.95:
    print()
    print("TRIAD STATE MACHINE CONFIRMED")
    print("Full Love->Hope->Fear->Love cycle returns to Love with high fidelity")
    print("The rotating triangle is a valid computational state machine")
elif love_return > 0.85:
    print()
    print("TRIAD CYCLE FUNCTIONAL")
    print("Cycle returns to Love state with good fidelity")
else:
    print()
    print("Cycle degraded -- hardware noise accumulating")

# Check forward vs reverse symmetry
forward_mid = state_probs[1][1]  # Hope state probability during forward
reverse_mid = state_probs[4][0]  # Love return via reverse
print()
print("Forward cycle return: " + str(round(love_return*100,1)) + "%")
print("Reverse cycle return: " + str(round(reverse_return*100,1)) + "%")
if abs(love_return - reverse_return) < 0.05:
    print("FORWARD = REVERSE -- Triad cycle is time-symmetric")

output = {
    "experiment": "Triad State Machine",
    "backend": "ibm_fez",
    "job_id": job.job_id(),
    "shots": SHOTS,
    "date": datetime.now().isoformat(),
    "architect": "Sajid Haneefa Kassim",
    "mission": "CarbonToCosmos",
    "state_probabilities": {
        "love_start": round(state_probs[0][0], 3),
        "after_love_to_hope": round(state_probs[1][1], 3),
        "after_hope_to_fear": round(state_probs[2][1], 3),
        "after_full_cycle": round(state_probs[3][0], 3),
        "reverse_cycle": round(state_probs[4][0], 3),
        "double_cycle": round(state_probs[5][0], 3)
    },
    "cycle_fidelity": round(cycle_fidelity*100,1),
    "time_symmetric": bool(abs(love_return - reverse_return) < 0.05)
}
with open("state_machine_results.json", "w") as f:
    json.dump(output, f, indent=2)
print("Saved: state_machine_results.json")
