from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
import json
from datetime import datetime

CRN = 'crn:v1:bluemix:public:quantum-computing:us-east:a/c88a87e2898a4647ba730430d3ac1df5:ff503e89-f427-4a58-8e83-fb11689b9213::'
BACKEND_NAME = 'ibm_fez'
SHOTS = 1024

print("TRINITY CORE PHASE 2 - KOTTAYIL TRIAD")
print("Two-qubit encoding of three Triad states")
print("|00> = Love/Information  |01> = Hope/Space  |10> = Fear/Time")
print("Connecting to IBM Quantum...")

service = QiskitRuntimeService(instance=CRN)
backend = service.backend(BACKEND_NAME)
print("Connected: " + BACKEND_NAME)

# STATE |00> - Love / Information / Equilibrium
qc_love = QuantumCircuit(2)
qc_love.measure_all()

# STATE |01> - Hope / Space / Peak
qc_hope = QuantumCircuit(2)
qc_hope.x(0)
qc_hope.measure_all()

# STATE |10> - Fear / Time / Trough
qc_fear = QuantumCircuit(2)
qc_fear.x(1)
qc_fear.measure_all()

# FULL TRIAD - Equal superposition of all three states
qc_triad = QuantumCircuit(2)
qc_triad.h(0)
qc_triad.cx(0, 1)
qc_triad.h(0)
qc_triad.measure_all()

# LFH EQUILIBRIUM - L=H=F balanced state
qc_lfh = QuantumCircuit(2)
from qiskit.circuit.library import RYGate
import numpy as np
qc_lfh.ry(2 * np.arccos(1/np.sqrt(3)), 0)
qc_lfh.cx(0, 1)
qc_lfh.h(0)
qc_lfh.measure_all()

print("Transpiling circuits...")
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
circuits = [
    pm.run(qc_love),
    pm.run(qc_hope),
    pm.run(qc_fear),
    pm.run(qc_triad),
    pm.run(qc_lfh)
]

print("Submitting to " + BACKEND_NAME + "...")
sampler = Sampler(backend)
job = sampler.run(circuits, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting for results...")

result = job.result()

names = [
    "Love_Information_00",
    "Hope_Space_01",
    "Fear_Time_10",
    "Triad_Superposition",
    "LFH_Equilibrium"
]

results = {}
print("\nRESULTS:")
print("=" * 50)

for i, name in enumerate(names):
    counts = result[i].data.meas.get_counts()
    results[name] = counts
    print("\n" + name + ":")
    for state, count in sorted(counts.items()):
        pct = count/SHOTS*100
        bar = "#" * int(pct/2)
        print("  |" + state + "> : " + str(count) + " (" + str(round(pct,1)) + "%) " + bar)

print("\n" + "=" * 50)
print("KOTTAYIL TRIAD ANALYSIS:")

love_counts = results["Love_Information_00"]
hope_counts = results["Hope_Space_01"]
fear_counts = results["Fear_Time_10"]

love_purity = love_counts.get("00", 0) / SHOTS * 100
hope_purity = hope_counts.get("01", 0) / SHOTS * 100
fear_purity = fear_counts.get("10", 0) / SHOTS * 100

print("Love state purity:  " + str(round(love_purity, 1)) + "%")
print("Hope state purity:  " + str(round(hope_purity, 1)) + "%")
print("Fear state purity:  " + str(round(fear_purity, 1)) + "%")
print("Average purity:     " + str(round((love_purity + hope_purity + fear_purity)/3, 1)) + "%")

triad_counts = results["Triad_Superposition"]
total = sum(triad_counts.values())
print("\nTriad superposition distribution:")
for state, count in sorted(triad_counts.items()):
    print("  |" + state + ">: " + str(round(count/total*100, 1)) + "%")

output = {
    "experiment": "Trinity Core Phase 2 - Kottayil Triad Full Encoding",
    "backend": BACKEND_NAME,
    "shots": SHOTS,
    "encoding": "|00>=Love/Info  |01>=Hope/Space  |10>=Fear/Time",
    "timestamp": datetime.now().isoformat(),
    "architect": "Sajid Haneefa Kassim",
    "mission": "CarbonToCosmos",
    "job_id": job.job_id(),
    "state_purities": {
        "Love_Information": round(love_purity, 2),
        "Hope_Space": round(hope_purity, 2),
        "Fear_Time": round(fear_purity, 2),
        "average": round((love_purity + hope_purity + fear_purity)/3, 2)
    },
    "results": results
}

with open("trinity_results_phase2.json", "w") as f:
    json.dump(output, f, indent=2)

print("\nPhase 2 complete.")
print("All three Triad states measured on IBM quantum hardware.")
print("Love | Hope | Fear - physically real and measurable.")
print("Results saved: trinity_results_phase2.json")
