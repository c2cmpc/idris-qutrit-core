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

print("BELL INEQUALITY v3 -- TRIAD ADJUSTED ANGLES")
print("Measurement angles compensate for Triad rotation")
print()

def chsh_corr(counts):
    total = sum(counts.values())
    c = 0
    for state, count in counts.items():
        b0 = 1 if state[1]=='0' else -1
        b1 = 1 if state[0]=='0' else -1
        c += b0*b1*count/total
    return c

def build_standard_bell(ta, tb):
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.ry(ta, 0)
    qc.ry(tb, 1)
    qc.measure_all()
    return qc

def build_triad_bell(ta, tb):
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    # Triad rotation applied to entangled state
    qc.ry(2*np.pi/3, 0)
    qc.ry(2*np.pi/3, 1)
    # Measurement angles adjusted by Triad phase offset
    offset = 2*np.pi/3
    qc.ry(ta + offset, 0)
    qc.ry(tb + offset, 1)
    qc.measure_all()
    return qc

# Optimal CHSH angles
a  = 0
a_ = np.pi/2
b  = np.pi/4
b_ = 3*np.pi/4

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
sampler = Sampler(backend)

# Standard Bell circuits
std = [pm.run(build_standard_bell(ta, tb))
       for ta,tb in [(a,b),(a,b_),(a_,b),(a_,b_)]]

# Triad Bell circuits -- angles compensated
tri = [pm.run(build_triad_bell(ta, tb))
       for ta,tb in [(a,b),(a,b_),(a_,b),(a_,b_)]]

all_c = std + tri
job = sampler.run(all_c, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting...")
result = job.result()

std_c = [chsh_corr(result[i].data.meas.get_counts()) for i in range(4)]
tri_c = [chsh_corr(result[i].data.meas.get_counts()) for i in range(4,8)]

S_std = abs(std_c[0] - std_c[1] + std_c[2] + std_c[3])
S_tri = abs(tri_c[0] - tri_c[1] + tri_c[2] + tri_c[3])

print()
print("CHSH RESULTS:")
print("Classical limit:   2.000")
print("Tsirelson bound:   2.828")
print()
print("Standard Bell S:   " + str(round(S_std,3)) +
      " | Violates: " + str(S_std > 2.0))
print("Triad Bell S:      " + str(round(S_tri,3)) +
      " | Violates: " + str(S_tri > 2.0))
print()

if S_tri > S_std:
    print("TRIAD STRONGER THAN STANDARD BELL")
    print("Triad rotation enhances quantum nonlocality")
    print("K3 geometry produces stronger entanglement than Bell")
elif S_std > S_tri:
    diff = S_std - S_tri
    print("Standard stronger by: " + str(round(diff,3)))
    if S_tri > 2.0:
        print("BOTH VIOLATE CLASSICAL LIMIT")
        print("Triad is genuinely nonlocal -- slightly less than optimal Bell")

output = {
    "experiment": "Bell CHSH v3 Triad adjusted angles",
    "backend": "ibm_fez",
    "job_id": job.job_id(),
    "shots": SHOTS,
    "date": datetime.now().isoformat(),
    "architect": "Sajid Haneefa Kassim",
    "mission": "CarbonToCosmos",
    "standard_S": round(S_std,3),
    "triad_S": round(S_tri,3),
    "standard_violates": bool(S_std>2.0),
    "triad_violates": bool(S_tri>2.0),
    "triad_beats_standard": bool(S_tri>S_std)
}
with open("bell_v3_results.json","w") as f:
    json.dump(output,f,indent=2)
print("Saved: bell_v3_results.json")
