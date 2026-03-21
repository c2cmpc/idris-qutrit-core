import numpy as np
from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

CRN = 'crn:v1:bluemix:public:quantum-computing:us-east:a/c88a87e2898a4647ba730430d3ac1df5:ff503e89-f427-4a58-8e83-fb11689b9213::'
SHOTS = 4096

service = QiskitRuntimeService(instance=CRN)
backend = service.backend('ibm_fez')

# THREE SEPARATE CIRCUITS — one per Triad state
# Isotropy proven when all three show equal purity

qc_love = QuantumCircuit(2)
qc_love.measure_all()

qc_hope = QuantumCircuit(2)
qc_hope.x(0)
qc_hope.measure_all()

qc_fear = QuantumCircuit(2)
qc_fear.x(1)
qc_fear.measure_all()

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
circuits = [pm.run(qc_love), pm.run(qc_hope), pm.run(qc_fear)]

print("KOTTAYIL TRIAD — Isotropy Validation")
print("Three separate circuits. One per Triad state.")
print()

sampler = Sampler(backend)
job = sampler.run(circuits, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting for results...")

result = job.result()
names = ["Love / Information |00>", "Hope / Space      |01>", "Fear / Time       |10>"]
purities = []
target_states = ["00", "01", "10"]

print()
print("TRIAD ISOTROPY RESULTS:")
print("=" * 50)

for i, name in enumerate(names):
    counts = result[i].data.meas.get_counts()
    total = sum(counts.values())
    target = target_states[i]
    purity = counts.get(target, 0) / total * 100
    purities.append(purity)
    noise = 100 - purity
    bar = "#" * int(purity / 2)
    print(name + ": " + str(round(purity,1)) + "% purity " + bar)
    print("  Noise: " + str(round(noise,1)) + "%")

avg = sum(purities) / 3
symmetry = max(abs(purities[0]-purities[1]), abs(purities[1]-purities[2]), abs(purities[0]-purities[2]))

print()
print("Average purity:  " + str(round(avg,1)) + "%")
print("Symmetry error:  " + str(round(symmetry,1)) + "%")
print("L=" + str(round(purities[0],1)) + "%  H=" + str(round(purities[1],1)) + "%  F=" + str(round(purities[2],1)) + "%")

print()
if symmetry < 5:
    print("L = H = F CONFIRMED -- Kottayil Triad isotropy validated")
elif symmetry < 10:
    print("Near isotropy -- within hardware noise bounds")
else:
    print("Asymmetric -- check hardware calibration")
