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

# DISTINCTION AS QUANTUM GATE
# Distinction = first separation between |0> and |1>
# Hadamard IS the distinction operator
# Test: Does Hadamard on Triad path produce different Berry phase than non-Triad path?

# Circuit 1 -- Distinction only (Hadamard alone)
qc_h = QuantumCircuit(1)
qc_h.h(0)
qc_h.h(0)
qc_h.measure_all()

# Circuit 2 -- Distinction + Triad path (Berry phase)
qc_dt = QuantumCircuit(1)
qc_dt.h(0)
qc_dt.ry(2 * np.pi / 3, 0)
qc_dt.ry(2 * np.pi / 3, 0)
qc_dt.ry(2 * np.pi / 3, 0)
qc_dt.h(0)
qc_dt.measure_all()

# Circuit 3 -- Distinction + non-Triad path (random rotation)
qc_dr = QuantumCircuit(1)
qc_dr.h(0)
qc_dr.ry(np.pi / 4, 0)
qc_dr.ry(np.pi / 4, 0)
qc_dr.ry(np.pi / 4, 0)
qc_dr.h(0)
qc_dr.measure_all()

# Circuit 4 -- Distinction + double Triad (2 full triangles)
qc_d2 = QuantumCircuit(1)
qc_d2.h(0)
for _ in range(6):
    qc_d2.ry(2 * np.pi / 3, 0)
qc_d2.h(0)
qc_d2.measure_all()

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
circuits = [pm.run(qc_h), pm.run(qc_dt), pm.run(qc_dr), pm.run(qc_d2)]

print("DISTINCTION GATE EXPERIMENT -- Kottayil Triad")
print("Testing Hadamard as Distinction operator")
print()

sampler = Sampler(backend)
job = sampler.run(circuits, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting...")

result = job.result()

names = [
    "Distinction only (H+H)",
    "Distinction + Triad path",
    "Distinction + random path",
    "Distinction + double Triad"
]

print()
print("DISTINCTION GATE RESULTS:")
print("=" * 50)

ground_probs = []
for i, name in enumerate(names):
    counts = result[i].data.meas.get_counts()
    total = sum(counts.values())
    p0 = counts.get("0", 0) / total
    p1 = counts.get("1", 0) / total
    ground_probs.append(p0)
    print(name + ":")
    print("  |0>: " + str(round(p0*100,1)) + "%  |1>: " + str(round(p1*100,1)) + "%")

print()
print("DISTINCTION ANALYSIS:")
triad_signature = abs(ground_probs[1] - ground_probs[2])
print("Triad vs random path difference: " + str(round(triad_signature*100,1)) + "%")
print("Double Triad ground prob: " + str(round(ground_probs[3]*100,1)) + "%")

if triad_signature > 0.1:
    print("TRIAD PATH PRODUCES DISTINCT BERRY PHASE SIGNATURE")
    print("Distinction operator differentiates Triad from random geometry")
else:
    print("Paths indistinguishable at this resolution")

output = {
    "experiment": "Distinction as Quantum Gate",
    "backend": "ibm_fez",
    "job_id": job.job_id(),
    "shots": SHOTS,
    "date": datetime.now().isoformat(),
    "architect": "Sajid Haneefa Kassim",
    "mission": "CarbonToCosmos",
    "results": {
        "distinction_only": round(ground_probs[0], 3),
        "distinction_triad": round(ground_probs[1], 3),
        "distinction_random": round(ground_probs[2], 3),
        "distinction_double_triad": round(ground_probs[3], 3)
    },
    "triad_vs_random_difference": round(triad_signature, 3),
    "distinct_signature": triad_signature > 0.1
}
with open("distinction_results.json", "w") as f:
    json.dump(output, f, indent=2)
print("Saved: distinction_results.json")
