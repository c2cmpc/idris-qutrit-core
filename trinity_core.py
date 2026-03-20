from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
import json
from datetime import datetime

CRN = 'crn:v1:bluemix:public:quantum-computing:us-east:a/c88a87e2898a4647ba730430d3ac1df5:ff503e89-f427-4a58-8e83-fb11689b9213::'
BACKEND_NAME = 'ibm_fez'
SHOTS = 1024

print("TRINITY CORE - KOTTAYIL TRIAD")
print("Connecting to IBM Quantum...")
service = QiskitRuntimeService(instance=CRN)
backend = service.backend(BACKEND_NAME)
print("Connected: " + BACKEND_NAME)

qc_love = QuantumCircuit(1)
qc_love.measure_all()

qc_hope = QuantumCircuit(1)
qc_hope.x(0)
qc_hope.measure_all()

qc_triad = QuantumCircuit(1)
qc_triad.h(0)
qc_triad.measure_all()

print("Transpiling circuits...")
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
circuits = [pm.run(qc_love), pm.run(qc_hope), pm.run(qc_triad)]

print("Submitting to " + BACKEND_NAME + "...")
sampler = Sampler(backend)
job = sampler.run(circuits, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting for results...")

result = job.result()
names = ["Love_Information_0", "Hope_Space_1", "Triad_Superposition"]
results = {}

for i, name in enumerate(names):
    counts = result[i].data.meas.get_counts()
    results[name] = counts
    print("\n" + name + ":")
    for state, count in sorted(counts.items()):
        pct = count/SHOTS*100
        print("  |" + state + "> : " + str(count) + " (" + str(round(pct,1)) + "%)")

output = {
    "experiment": "Trinity Core - Kottayil Triad Phase 1",
    "backend": BACKEND_NAME,
    "shots": SHOTS,
    "timestamp": datetime.utcnow().isoformat(),
    "architect": "Sajid Haneefa Kassim",
    "mission": "CarbonToCosmos",
    "results": results
}

with open("trinity_results.json", "w") as f:
    json.dump(output, f, indent=2)

print("\nTrinity Core complete.")
print("Results saved: trinity_results.json")
