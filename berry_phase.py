import numpy as np
from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

CRN = 'crn:v1:bluemix:public:quantum-computing:us-east:a/c88a87e2898a4647ba730430d3ac1df5:ff503e89-f427-4a58-8e83-fb11689b9213::'
SHOTS = 4096

service = QiskitRuntimeService(instance=CRN)
backend = service.backend('ibm_fez')

# BERRY PHASE EXPERIMENT
# Rotate state vector through triangular path in Bloch sphere
# Path: Love(0) -> Hope(+1) -> Fear(-1) -> Love(0)
# Information stored in the geometric phase accumulated

# Reference circuit -- no rotation
qc_ref = QuantumCircuit(1)
qc_ref.h(0)
qc_ref.measure_all()

# Berry phase circuit -- triangular path
# RY(2pi/3) rotates through 120 degrees -- one vertex of equilateral triangle
qc_berry = QuantumCircuit(1)
qc_berry.h(0)
qc_berry.ry(2 * np.pi / 3, 0)   # Love -> Hope (120 degrees)
qc_berry.ry(2 * np.pi / 3, 0)   # Hope -> Fear (120 degrees)
qc_berry.ry(2 * np.pi / 3, 0)   # Fear -> Love (120 degrees, full rotation)
qc_berry.h(0)
qc_berry.measure_all()

# Phase shifted circuit -- half rotation
qc_half = QuantumCircuit(1)
qc_half.h(0)
qc_half.ry(np.pi / 3, 0)        # Half triangle rotation
qc_half.h(0)
qc_half.measure_all()

print("BERRY PHASE EXPERIMENT -- Kottayil Triad Geometric Gate")
print("Triangular path: Love -> Hope -> Fear -> Love")
print()

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
circuits = [pm.run(qc_ref), pm.run(qc_berry), pm.run(qc_half)]

sampler = Sampler(backend)
job = sampler.run(circuits, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting for results...")

result = job.result()

names = ["Reference (no rotation)", "Full triangle (Berry phase)", "Half triangle"]
for i, name in enumerate(names):
    counts = result[i].data.meas.get_counts()
    total = sum(counts.values())
    zero = counts.get("0", 0) / total * 100
    one = counts.get("1", 0) / total * 100
    print(name + ":")
    print("  |0>: " + str(round(zero,1)) + "%  |1>: " + str(round(one,1)) + "%")

print()
print("If Berry phase accumulated:")
print("Full triangle should differ from reference")
print("This is the geometric phase of the Kottayil Triad rotation")
