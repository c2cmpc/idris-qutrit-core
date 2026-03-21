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

def triad_forward(qc, reps):
    for _ in range(reps):
        qc.ry(2 * np.pi / 3, 0)
        qc.ry(2 * np.pi / 3, 1)

def triad_backward(qc, reps):
    for _ in range(reps):
        qc.ry(-2 * np.pi / 3, 1)
        qc.ry(-2 * np.pi / 3, 0)

def build_otoc(reps):
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.x(0)
    triad_forward(qc, reps)
    qc.z(0)
    triad_backward(qc, reps)
    qc.x(0)
    qc.cx(0, 1)
    qc.h(0)
    qc.measure_all()
    return qc

qc_ref = QuantumCircuit(2)
qc_ref.h(0)
qc_ref.cx(0, 1)
qc_ref.measure_all()

circuits_raw = [qc_ref, build_otoc(1), build_otoc(2), build_otoc(3)]
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
circuits = [pm.run(qc) for qc in circuits_raw]

print("OTOC EXPERIMENT -- Kottayil Triad")
sampler = Sampler(backend)
job = sampler.run(circuits, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting...")

result = job.result()
names = ["Reference", "1 rotation", "2 rotations", "Full triangle"]
otoc_values = []

print()
print("OTOC RESULTS:")
print("=" * 50)
for i, name in enumerate(names):
    counts = result[i].data.meas.get_counts()
    total = sum(counts.values())
    overlap = counts.get("00", 0) / total
    otoc_values.append(overlap)
    print(name + ": OTOC = " + str(round(overlap, 3)))

decay = otoc_values[0] - otoc_values[3]
print()
print("Total OTOC decay: " + str(round(decay, 3)))

if otoc_values[3] < 0.1:
    print("MAXIMAL SCRAMBLING CONFIRMED")
elif otoc_values[3] < 0.3:
    print("STRONG SCRAMBLING detected")
elif decay > 0.2:
    print("PARTIAL SCRAMBLING -- OTOC decaying with time")
else:
    print("WEAK SCRAMBLING")

output = {"experiment":"OTOC Kottayil Triad","backend":"ibm_fez","job_id":job.job_id(),"shots":SHOTS,"date":datetime.now().isoformat(),"architect":"Sajid Haneefa Kassim","mission":"CarbonToCosmos","otoc_values":{"reference":round(otoc_values[0],3),"1_rotation":round(otoc_values[1],3),"2_rotations":round(otoc_values[2],3),"full_triangle":round(otoc_values[3],3)},"total_decay":round(decay,3),"maximal_scrambling":otoc_values[3]<0.1}
with open("otoc_results.json","w") as f:
    json.dump(output,f,indent=2)
print("Saved: otoc_results.json")
