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

# TIME DILATION ANALOG -- Kottayil Triad
# Special relativity: moving clocks run slow
# Quantum analog: fast evolution accumulates phase faster
# Test: Full speed Triad vs half speed Triad vs quarter speed Triad
# If Fear/Time = irreversibility is correct:
# faster rotation = more phase = more time experienced
# slower rotation = less phase = less time experienced
# The phase difference IS the time dilation

# Full speed -- one complete Triad triangle (3 x 120 degrees)
qc_full = QuantumCircuit(1)
qc_full.h(0)
qc_full.ry(2 * np.pi / 3, 0)
qc_full.ry(2 * np.pi / 3, 0)
qc_full.ry(2 * np.pi / 3, 0)
qc_full.h(0)
qc_full.measure_all()

# Half speed -- same total angle in 6 steps
qc_half = QuantumCircuit(1)
qc_half.h(0)
for _ in range(6):
    qc_half.ry(np.pi / 3, 0)
qc_half.h(0)
qc_half.measure_all()

# Quarter speed -- same total angle in 12 steps
qc_quarter = QuantumCircuit(1)
qc_quarter.h(0)
for _ in range(12):
    qc_quarter.ry(np.pi / 6, 0)
qc_quarter.h(0)
qc_quarter.measure_all()

# Double speed -- 6 triangles (6 x 360 degrees)
qc_double = QuantumCircuit(1)
qc_double.h(0)
for _ in range(6):
    qc_double.ry(2 * np.pi / 3, 0)
qc_double.h(0)
qc_double.measure_all()

# Reference -- no rotation
qc_ref = QuantumCircuit(1)
qc_ref.h(0)
qc_ref.h(0)
qc_ref.measure_all()

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
circuits = [
    pm.run(qc_ref),
    pm.run(qc_quarter),
    pm.run(qc_half),
    pm.run(qc_full),
    pm.run(qc_double)
]

print("TIME DILATION ANALOG -- Kottayil Triad")
print("Fear/Time = irreversibility mapping")
print("Same total rotation angle, different speeds")
print()

sampler = Sampler(backend)
job = sampler.run(circuits, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting...")

result = job.result()

names = [
    "Reference (no rotation)",
    "Quarter speed (12 steps)",
    "Half speed (6 steps)",
    "Full speed (3 steps)",
    "Double speed (6 triangles)"
]

speeds = [0, 0.25, 0.5, 1.0, 2.0]

print()
print("TIME DILATION RESULTS:")
print("=" * 60)

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
print("PHASE ACCUMULATION ANALYSIS:")
print("Speed    Ground prob    Phase signal")
print("-" * 45)
for i, speed in enumerate(speeds):
    phase_signal = ground_probs[i]
    bar = "#" * int(phase_signal * 40)
    print(str(speed) + "x       " + str(round(phase_signal*100,1)) + "%          " + bar)

# Time dilation signature:
# If faster rotation = more phase = different ground state probability
# The spread between full speed and half speed is the dilation signal
dilation_signal = abs(ground_probs[3] - ground_probs[2])
speed_effect = abs(ground_probs[3] - ground_probs[1])

print()
print("Dilation signal (full vs half speed): " + str(round(dilation_signal*100,1)) + "%")
print("Speed effect (full vs quarter speed): " + str(round(speed_effect*100,1)) + "%")

if dilation_signal > 0.05:
    print()
    print("TIME DILATION ANALOG DETECTED")
    print("Different rotation speeds produce different phase accumulation")
    print("Fear/Time = irreversibility mapping confirmed")
    print("Faster Triad rotation = more phase = more time experienced")
else:
    print()
    print("Speed effect below noise threshold")
    print("All speeds produce similar phase -- geometry dominates over speed")

output = {
    "experiment": "Time Dilation Analog -- Kottayil Triad",
    "backend": "ibm_fez",
    "job_id": job.job_id(),
    "shots": SHOTS,
    "date": datetime.now().isoformat(),
    "architect": "Sajid Haneefa Kassim",
    "mission": "CarbonToCosmos",
    "ground_probabilities": {
        "reference": round(ground_probs[0], 3),
        "quarter_speed": round(ground_probs[1], 3),
        "half_speed": round(ground_probs[2], 3),
        "full_speed": round(ground_probs[3], 3),
        "double_speed": round(ground_probs[4], 3)
    },
    "dilation_signal_pct": round(dilation_signal*100, 1),
    "speed_effect_pct": round(speed_effect*100, 1),
    "dilation_detected": bool(dilation_signal > 0.05)
}
with open("time_dilation_results.json", "w") as f:
    json.dump(output, f, indent=2)
print("Saved: time_dilation_results.json")
