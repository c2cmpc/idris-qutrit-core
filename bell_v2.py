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

print("BELL INEQUALITY v2 -- CORRECTED ANGLES")
print("CHSH optimal: a=0 a'=pi/2 b=pi/4 b'=3pi/4")
print()

def bell_circuit(theta_a, theta_b, etype="standard"):
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    if etype == "triad":
        qc.cx(1, 0)
        qc.ry(2*np.pi/3, 0)
        qc.ry(2*np.pi/3, 1)
        qc.cx(0, 1)
    qc.ry(theta_a, 0)
    qc.ry(theta_b, 1)
    qc.measure_all()
    return qc

def chsh_corr(counts):
    total = sum(counts.values())
    c = 0
    for state, count in counts.items():
        b0 = 1 if state[1]=='0' else -1
        b1 = 1 if state[0]=='0' else -1
        c += b0*b1*count/total
    return c

# CORRECTED angles
a  = 0
a_ = np.pi/2
b  = np.pi/4
b_ = 3*np.pi/4   # FIXED -- was -pi/4

configs = [
    (a,  b,  "standard"),
    (a,  b_, "standard"),
    (a_, b,  "standard"),
    (a_, b_, "standard"),
    (a,  b,  "triad"),
    (a,  b_, "triad"),
    (a_, b,  "triad"),
    (a_, b_, "triad"),
]

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
circuits = [pm.run(bell_circuit(ta, tb, et)) for ta,tb,et in configs]

sampler = Sampler(backend)
job = sampler.run(circuits, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting...")
result = job.result()

std_corrs = [chsh_corr(result[i].data.meas.get_counts()) for i in range(4)]
tri_corrs = [chsh_corr(result[i].data.meas.get_counts()) for i in range(4,8)]

S_std = abs(std_corrs[0] - std_corrs[1] + std_corrs[2] + std_corrs[3])
S_tri = abs(tri_corrs[0] - tri_corrs[1] + tri_corrs[2] + tri_corrs[3])

print()
print("CHSH RESULTS:")
print("Classical limit:   2.000")
print("Tsirelson bound:   2.828")
print()
print("Standard Bell S:   " + str(round(S_std,3)) +
      " | Violates: " + str(S_std > 2.0))
print("Triad Bell S:      " + str(round(S_tri,3)) +
      " | Violates: " + str(S_tri > 2.0))

if S_tri > S_std:
    print()
    print("TRIAD STRONGER BELL VIOLATION")
    print("K3 entanglement enhances quantum nonlocality")
if S_tri > 2.0:
    print("TRIAD VIOLATES CLASSICAL LIMIT")
    print("Genuine quantum nonlocality confirmed in Triad geometry")
if S_std > 2.0:
    print("STANDARD BELL VIOLATION CONFIRMED")

output = {
    "experiment": "Bell CHSH v2 corrected angles",
    "backend": "ibm_fez",
    "job_id": job.job_id(),
    "shots": SHOTS,
    "date": datetime.now().isoformat(),
    "architect": "Sajid Haneefa Kassim",
    "mission": "CarbonToCosmos",
    "angles": {"a":0,"a_prime":1.571,"b":0.785,"b_prime":2.356},
    "chsh": {
        "standard_S": round(S_std,3),
        "triad_S": round(S_tri,3),
        "classical_limit": 2.0,
        "tsirelson": 2.828,
        "standard_violates": bool(S_std>2.0),
        "triad_violates": bool(S_tri>2.0),
        "triad_beats_standard": bool(S_tri>S_std)
    }
}
with open("bell_v2_results.json","w") as f:
    json.dump(output,f,indent=2)
print("Saved: bell_v2_results.json")
