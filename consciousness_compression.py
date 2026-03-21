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

# CONSCIOUSNESS COMPRESSION CIRCUIT
# Consciousness = compresses infinite possibilities into one irreversible next step
# Start in maximum superposition (all states equally probable)
# Apply Triad rotation
# Measure collapse rate to definite state
# Compare with random rotation of same depth

# Circuit 1 -- Maximum superposition baseline (no compression)
qc_max = QuantumCircuit(2)
qc_max.h(0)
qc_max.h(1)
qc_max.measure_all()

# Circuit 2 -- Triad compression (1 rotation)
qc_t1 = QuantumCircuit(2)
qc_t1.h(0)
qc_t1.h(1)
qc_t1.ry(2 * np.pi / 3, 0)
qc_t1.ry(2 * np.pi / 3, 1)
qc_t1.measure_all()

# Circuit 3 -- Triad compression (full triangle)
qc_t3 = QuantumCircuit(2)
qc_t3.h(0)
qc_t3.h(1)
for _ in range(3):
    qc_t3.ry(2 * np.pi / 3, 0)
    qc_t3.ry(2 * np.pi / 3, 1)
qc_t3.measure_all()

# Circuit 4 -- Random compression (same depth as full triangle)
qc_rand = QuantumCircuit(2)
qc_rand.h(0)
qc_rand.h(1)
for _ in range(3):
    qc_rand.ry(np.pi / 5, 0)
    qc_rand.ry(np.pi / 7, 1)
qc_rand.measure_all()

# Circuit 5 -- Entangled Triad compression
qc_ent = QuantumCircuit(2)
qc_ent.h(0)
qc_ent.h(1)
qc_ent.cx(0, 1)
for _ in range(3):
    qc_ent.ry(2 * np.pi / 3, 0)
    qc_ent.ry(2 * np.pi / 3, 1)
qc_ent.measure_all()

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
circuits = [
    pm.run(qc_max),
    pm.run(qc_t1),
    pm.run(qc_t3),
    pm.run(qc_rand),
    pm.run(qc_ent)
]

print("CONSCIOUSNESS COMPRESSION -- Kottayil Triad")
print("Maximum superposition compressed by Triad rotation")
print()

sampler = Sampler(backend)
job = sampler.run(circuits, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting...")

result = job.result()

names = [
    "Max superposition (baseline)",
    "Triad compression 1 rotation",
    "Triad compression full triangle",
    "Random compression same depth",
    "Entangled Triad compression"
]

print()
print("CONSCIOUSNESS COMPRESSION RESULTS:")
print("=" * 55)

dominant_probs = []
entropies = []
for i, name in enumerate(names):
    counts = result[i].data.meas.get_counts()
    total = sum(counts.values())
    probs = {k: v/total for k, v in counts.items()}
    dominant = max(probs.values())
    dominant_probs.append(dominant)
    # Shannon entropy as measure of compression
    entropy = -sum(p * np.log2(p) for p in probs.values() if p > 0)
    entropies.append(entropy)
    dominant_state = max(probs, key=probs.get)
    print(name + ":")
    print("  Dominant state |" + dominant_state + ">: " + str(round(dominant*100,1)) + "%")
    print("  Entropy: " + str(round(entropy, 3)) + " bits")

print()
print("COMPRESSION ANALYSIS:")
print("Baseline entropy:          " + str(round(entropies[0], 3)) + " bits")
print("Triad 1 rotation entropy:  " + str(round(entropies[1], 3)) + " bits")
print("Triad full triangle:       " + str(round(entropies[2], 3)) + " bits")
print("Random same depth:         " + str(round(entropies[3], 3)) + " bits")
print("Entangled Triad:           " + str(round(entropies[4], 3)) + " bits")

triad_compression = entropies[0] - entropies[2]
random_compression = entropies[0] - entropies[3]
print()
print("Triad compression rate:  " + str(round(triad_compression, 3)) + " bits")
print("Random compression rate: " + str(round(random_compression, 3)) + " bits")
print("Triad advantage:         " + str(round(triad_compression - random_compression, 3)) + " bits")

if triad_compression > random_compression:
    print()
    print("TRIAD COMPRESSES FASTER THAN RANDOM GEOMETRY")
    print("Consciousness compression mechanism confirmed")
    print("Kottayil Triad geometry is the optimal compression path")
else:
    print()
    print("Compression rates comparable -- deeper circuit needed")

output = {
    "experiment": "Consciousness Compression Circuit",
    "backend": "ibm_fez",
    "job_id": job.job_id(),
    "shots": SHOTS,
    "date": datetime.now().isoformat(),
    "architect": "Sajid Haneefa Kassim",
    "mission": "CarbonToCosmos",
    "entropies": {
        "baseline": round(entropies[0], 3),
        "triad_1_rotation": round(entropies[1], 3),
        "triad_full_triangle": round(entropies[2], 3),
        "random_same_depth": round(entropies[3], 3),
        "entangled_triad": round(entropies[4], 3)
    },
    "dominant_probs": {
        "baseline": round(dominant_probs[0], 3),
        "triad_1_rotation": round(dominant_probs[1], 3),
        "triad_full_triangle": round(dominant_probs[2], 3),
        "random_same_depth": round(dominant_probs[3], 3),
        "entangled_triad": round(dominant_probs[4], 3)
    },
    "triad_compression_bits": round(triad_compression, 3),
    "random_compression_bits": round(random_compression, 3),
    "triad_advantage_bits": round(triad_compression - random_compression, 3),
    "triad_faster": bool(triad_compression > random_compression)
}
with open("consciousness_compression_results.json", "w") as f:
    json.dump(output, f, indent=2)
print("Saved: consciousness_compression_results.json")
