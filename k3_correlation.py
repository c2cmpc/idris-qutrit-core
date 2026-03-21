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

# K3 COMPLETE GRAPH CORRELATION -- Kottayil Triad
# K3 = complete graph on 3 vertices
# Every vertex connected to every other vertex simultaneously
# This is the minimal all-to-all topology
# Same topology as SYK model -- maximal scrambler
# Test: Does K3 entanglement produce unique correlation signature?

# K3 entanglement -- all three qubits connected to each other
qc_k3 = QuantumCircuit(3)
qc_k3.h(0)
qc_k3.cx(0, 1)
qc_k3.cx(0, 2)
qc_k3.cx(1, 2)  # K3 completion -- third edge
qc_k3.measure_all()

# K3 + Triad rotation
qc_k3_triad = QuantumCircuit(3)
qc_k3_triad.h(0)
qc_k3_triad.cx(0, 1)
qc_k3_triad.cx(0, 2)
qc_k3_triad.cx(1, 2)
for q in range(3):
    qc_k3_triad.ry(2 * np.pi / 3, q)
qc_k3_triad.measure_all()

# Linear chain -- not K3 (only two edges)
qc_chain = QuantumCircuit(3)
qc_chain.h(0)
qc_chain.cx(0, 1)
qc_chain.cx(1, 2)
qc_chain.measure_all()

# Star topology -- one center connected to two
qc_star = QuantumCircuit(3)
qc_star.h(0)
qc_star.cx(0, 1)
qc_star.cx(0, 2)
qc_star.measure_all()

# GHZ state -- maximum 3-qubit entanglement reference
qc_ghz = QuantumCircuit(3)
qc_ghz.h(0)
qc_ghz.cx(0, 1)
qc_ghz.cx(0, 2)
qc_ghz.measure_all()

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
circuits = [
    pm.run(qc_k3),
    pm.run(qc_k3_triad),
    pm.run(qc_chain),
    pm.run(qc_star),
    pm.run(qc_ghz)
]

print("K3 COMPLETE GRAPH CORRELATION -- Kottayil Triad")
print("Testing all-to-all connectivity SYK connection")
print()

sampler = Sampler(backend)
job = sampler.run(circuits, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting...")

result = job.result()

names = [
    "K3 (all-to-all)",
    "K3 + Triad rotation",
    "Linear chain",
    "Star topology",
    "GHZ reference"
]

print()
print("K3 CORRELATION RESULTS:")
print("=" * 55)

all_counts = []
for i, name in enumerate(names):
    counts = result[i].data.meas.get_counts()
    total = sum(counts.values())
    probs = {k: v/total for k, v in counts.items()}
    all_counts.append(probs)

    # Three-way correlation: P(000) + P(111) vs mixed states
    p_aligned = probs.get("000", 0) + probs.get("111", 0)
    p_mixed = 1 - p_aligned

    # Symmetry across all three qubits
    p0_excited = sum(v for k,v in probs.items() if k[2]=="1")
    p1_excited = sum(v for k,v in probs.items() if k[1]=="1")
    p2_excited = sum(v for k,v in probs.items() if k[0]=="1")
    symmetry_err = max(abs(p0_excited-p1_excited),
                      abs(p1_excited-p2_excited),
                      abs(p0_excited-p2_excited))

    print(name + ":")
    print("  Aligned (000+111): " + str(round(p_aligned*100,1)) + "%")
    print("  Mixed states:      " + str(round(p_mixed*100,1)) + "%")
    print("  3-qubit symmetry:  " + str(round((1-symmetry_err)*100,1)) + "%")

print()
print("TOPOLOGY COMPARISON:")
k3_aligned = all_counts[0].get("000",0) + all_counts[0].get("111",0)
k3t_aligned = all_counts[1].get("000",0) + all_counts[1].get("111",0)
chain_aligned = all_counts[2].get("000",0) + all_counts[2].get("111",0)
star_aligned = all_counts[3].get("000",0) + all_counts[3].get("111",0)
ghz_aligned = all_counts[4].get("000",0) + all_counts[4].get("111",0)

print("GHZ reference:    " + str(round(ghz_aligned*100,1)) + "%")
print("K3 topology:      " + str(round(k3_aligned*100,1)) + "%")
print("K3 + Triad:       " + str(round(k3t_aligned*100,1)) + "%")
print("Star topology:    " + str(round(star_aligned*100,1)) + "%")
print("Linear chain:     " + str(round(chain_aligned*100,1)) + "%")

if k3_aligned > star_aligned and k3_aligned > chain_aligned:
    print()
    print("K3 PRODUCES STRONGEST CORRELATION")
    print("All-to-all topology maximizes three-way correlation")
    print("SYK connection confirmed -- K3 is the minimal maximal scrambler")

output = {
    "experiment": "K3 Complete Graph Correlation",
    "backend": "ibm_fez",
    "job_id": job.job_id(),
    "shots": SHOTS,
    "date": datetime.now().isoformat(),
    "architect": "Sajid Haneefa Kassim",
    "mission": "CarbonToCosmos",
    "aligned_probabilities": {
        "k3": round(k3_aligned, 3),
        "k3_triad": round(k3t_aligned, 3),
        "chain": round(chain_aligned, 3),
        "star": round(star_aligned, 3),
        "ghz": round(ghz_aligned, 3)
    },
    "k3_beats_star": bool(k3_aligned > star_aligned),
    "k3_beats_chain": bool(k3_aligned > chain_aligned)
}
with open("k3_correlation_results.json", "w") as f:
    json.dump(output, f, indent=2)
print("Saved: k3_correlation_results.json")
