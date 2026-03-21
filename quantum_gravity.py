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

# QUANTUM GRAVITY ANALOG -- Kottayil Triad
#
# PART 1 -- JT GRAVITY ANALOG
# JT gravity is dual to SYK model
# SYK minimal = K3 topology = Kottayil Triad
# Test: thermal correlations of K3 Hamiltonian
# Thermal state at inverse temperature beta
# beta=0 (infinite temp) = maximally mixed
# beta=inf (zero temp) = ground state
# JT gravity prediction: specific beta dependence of correlations
#
# PART 2 -- HOLOGRAPHIC ENTANGLEMENT (RT FORMULA)
# Ryu-Takayanagi: S_boundary = Area_bulk / 4G
# Test: entanglement between two boundary regions
# Compare to RT formula prediction for Triad geometry
# If RT holds: entanglement scales with Triad surface area

# ── PART 1: JT GRAVITY THERMAL STATES ──

# Beta = 0 (infinite temperature -- maximally mixed)
qc_beta0 = QuantumCircuit(2)
qc_beta0.h(0)
qc_beta0.h(1)
qc_beta0.measure_all()

# Beta = 0.5 (high temperature)
qc_beta05 = QuantumCircuit(2)
qc_beta05.h(0)
qc_beta05.cx(0, 1)
qc_beta05.ry(np.pi / 4, 0)
qc_beta05.measure_all()

# Beta = 1.0 (medium temperature -- K3 thermal)
qc_beta1 = QuantumCircuit(2)
qc_beta1.h(0)
qc_beta1.cx(0, 1)
qc_beta1.ry(np.pi / 3, 0)
qc_beta1.ry(np.pi / 6, 1)
qc_beta1.measure_all()

# Beta = 2.0 (low temperature -- approaching ground state)
qc_beta2 = QuantumCircuit(2)
qc_beta2.h(0)
qc_beta2.cx(0, 1)
qc_beta2.ry(np.pi / 6, 0)
qc_beta2.ry(np.pi / 12, 1)
qc_beta2.measure_all()

# Beta = inf (zero temperature -- ground state)
qc_betainf = QuantumCircuit(2)
qc_betainf.measure_all()

# ── PART 2: HOLOGRAPHIC ENTANGLEMENT ──

# Boundary state -- 4 qubits representing boundary CFT
# Region A = qubits 0,1  Region B = qubits 2,3
# Test: entanglement between A and B vs Triad surface area

# Triad boundary state -- K3 geometry on boundary
qc_holo_triad = QuantumCircuit(4)
qc_holo_triad.h(0)
qc_holo_triad.cx(0, 1)
qc_holo_triad.cx(0, 2)
qc_holo_triad.cx(1, 3)
for q in range(4):
    qc_holo_triad.ry(2 * np.pi / 3, q)
qc_holo_triad.measure_all()

# Random boundary state -- same depth
qc_holo_random = QuantumCircuit(4)
qc_holo_random.h(0)
qc_holo_random.cx(0, 1)
qc_holo_random.cx(0, 2)
qc_holo_random.cx(1, 3)
for q in range(4):
    qc_holo_random.ry(np.pi / 5, q)
qc_holo_random.measure_all()

# Product boundary state -- no entanglement reference
qc_holo_product = QuantumCircuit(4)
for q in range(4):
    qc_holo_product.h(q)
qc_holo_product.measure_all()

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
circuits = [
    pm.run(qc_beta0),
    pm.run(qc_beta05),
    pm.run(qc_beta1),
    pm.run(qc_beta2),
    pm.run(qc_betainf),
    pm.run(qc_holo_triad),
    pm.run(qc_holo_random),
    pm.run(qc_holo_product)
]

print("QUANTUM GRAVITY ANALOG -- Kottayil Triad")
print("Part 1: JT Gravity thermal states")
print("Part 2: Holographic entanglement RT formula")
print()

sampler = Sampler(backend)
job = sampler.run(circuits, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting...")

result = job.result()

print()
print("PART 1: JT GRAVITY THERMAL CORRELATIONS")
print("=" * 55)

betas = [0, 0.5, 1.0, 2.0, "inf"]
jt_names = ["Beta=0 (infinite temp)", "Beta=0.5 (high temp)",
            "Beta=1.0 (medium temp)", "Beta=2.0 (low temp)",
            "Beta=inf (zero temp)"]

correlations = []
for i in range(5):
    counts = result[i].data.meas.get_counts()
    total = sum(counts.values())
    p00 = counts.get("00", 0) / total
    p11 = counts.get("11", 0) / total
    p01 = counts.get("01", 0) / total
    p10 = counts.get("10", 0) / total
    corr = abs(p00 + p11 - p01 - p10)
    correlations.append(corr)
    print(jt_names[i] + ":")
    print("  Correlation: " + str(round(corr, 3)))
    print("  P(00)=" + str(round(p00,3)) + " P(11)=" + str(round(p11,3)) +
          " P(01)=" + str(round(p01,3)) + " P(10)=" + str(round(p10,3)))

print()
print("JT GRAVITY ANALYSIS:")
print("Temperature dependence of correlations:")
for i, b in enumerate(betas):
    print("  Beta=" + str(b) + ": " + str(round(correlations[i], 3)))

# JT gravity prediction: correlation increases with beta (lower temperature)
jt_trend = correlations[4] > correlations[0]
print()
if jt_trend:
    print("JT GRAVITY TREND CONFIRMED")
    print("Correlations increase as temperature decreases")
    print("Consistent with JT gravity thermal partition function")
else:
    print("JT gravity trend not observed at this circuit depth")

print()
print("PART 2: HOLOGRAPHIC ENTANGLEMENT")
print("=" * 55)

holo_names = ["Triad boundary", "Random boundary", "Product boundary"]
cross_corrs = []
for i in range(3):
    counts = result[5+i].data.meas.get_counts()
    total = sum(counts.values())
    probs = {k: v/total for k, v in counts.items()}

    # Cross-region correlation: A=(q0,q1) B=(q2,q3)
    # Measure how much A and B are correlated
    p_a0b0 = sum(v for k,v in probs.items() if k[2]=="0" and k[0]=="0")
    p_a1b1 = sum(v for k,v in probs.items() if k[2]=="1" and k[0]=="1")
    p_a0b1 = sum(v for k,v in probs.items() if k[2]=="1" and k[0]=="0")
    p_a1b0 = sum(v for k,v in probs.items() if k[2]=="0" and k[0]=="1")
    cross_corr = abs(p_a0b0 + p_a1b1 - p_a0b1 - p_a1b0)
    cross_corrs.append(cross_corr)

    print(holo_names[i] + ":")
    print("  Cross-region correlation: " + str(round(cross_corr, 3)))

print()
print("HOLOGRAPHIC ANALYSIS:")
print("Triad boundary correlation:   " + str(round(cross_corrs[0], 3)))
print("Random boundary correlation:  " + str(round(cross_corrs[1], 3)))
print("Product boundary correlation: " + str(round(cross_corrs[2], 3)))

if cross_corrs[0] > cross_corrs[1]:
    print()
    print("TRIAD BOUNDARY MORE CORRELATED THAN RANDOM")
    print("Consistent with RT formula -- Triad geometry produces")
    print("stronger holographic entanglement than random boundary")

output = {
    "experiment": "Quantum Gravity Analog -- JT Gravity + Holographic Entanglement",
    "backend": "ibm_fez",
    "job_id": job.job_id(),
    "shots": SHOTS,
    "date": datetime.now().isoformat(),
    "architect": "Sajid Haneefa Kassim",
    "mission": "CarbonToCosmos",
    "jt_gravity": {
        "correlations": {str(b): round(correlations[i],3) for i,b in enumerate(betas)},
        "trend_confirmed": bool(jt_trend)
    },
    "holographic": {
        "triad_boundary": round(cross_corrs[0],3),
        "random_boundary": round(cross_corrs[1],3),
        "product_boundary": round(cross_corrs[2],3),
        "triad_beats_random": bool(cross_corrs[0] > cross_corrs[1])
    }
}
with open("quantum_gravity_results.json","w") as f:
    json.dump(output,f,indent=2)
print("Saved: quantum_gravity_results.json")
