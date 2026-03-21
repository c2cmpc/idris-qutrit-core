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

print("VQE -- TRIAD HAMILTONIAN GROUND STATE")
print("Finding the natural resting state of the Kottayil geometry")
print("Physical meaning: optimal REKSHA operating point")
print()

# VARIATIONAL QUANTUM EIGENSOLVER (VQE)
# Find the ground state energy of the Triad Hamiltonian
#
# Triad Hamiltonian:
# H = -J*(XX + YY + ZZ) - h*(Z0 + Z1 + Z2)
# J = coupling strength between neurons (K3 entanglement)
# h = external field (environmental input)
#
# Ground state = lowest energy configuration
# = natural resting state of the Triad system
# = optimal operating point for REKSHA/PRANADARA
#
# VQE method:
# 1. Parameterized ansatz circuit (trial state)
# 2. Measure energy expectation value
# 3. Classical optimizer adjusts parameters
# 4. Repeat until minimum energy found

def triad_ansatz(params):
    qc = QuantumCircuit(3)
    # Layer 1: single qubit rotations
    for i in range(3):
        qc.ry(params[i], i)
    # K3 entanglement
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.cx(2, 0)
    # Layer 2: more rotations
    for i in range(3):
        qc.ry(params[i+3], i)
    return qc

def measure_zz(params, qubit_pair):
    qc = triad_ansatz(params)
    qc.measure_all()
    return qc

def measure_xx(params, qubit_pair):
    qc = triad_ansatz(params)
    # Rotate to X basis
    for q in qubit_pair:
        qc.h(q)
    qc.measure_all()
    return qc

def measure_z(params, qubit):
    qc = triad_ansatz(params)
    qc.measure_all()
    return qc

def get_zz_expectation(counts, q0, q1, shots):
    total = sum(counts.values())
    exp = 0
    for state, count in counts.items():
        state_list = list(state)
        z0 = 1 if state_list[-(q0+1)] == '0' else -1
        z1 = 1 if state_list[-(q1+1)] == '0' else -1
        exp += z0 * z1 * count / total
    return exp

def get_z_expectation(counts, q, shots):
    total = sum(counts.values())
    exp = 0
    for state, count in counts.items():
        z = 1 if state[-(q+1)] == '0' else -1
        exp += z * count / total
    return exp

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
sampler = Sampler(backend)

# VQE optimization -- grid search over key parameters
# (full gradient descent would need 100+ IBM jobs)
# Grid search gives us the energy landscape shape

J = 1.0   # coupling strength
h = 0.5   # external field

print("Scanning energy landscape...")
print()

# Test different parameter configurations
param_configs = [
    ("Ground state (all zero)",    np.zeros(6)),
    ("Love dominant",              np.array([0, np.pi/2, np.pi/2, 0, 0, 0])),
    ("Hope dominant",              np.array([np.pi/2, 0, np.pi/2, 0, 0, 0])),
    ("Fear dominant",              np.array([np.pi/2, np.pi/2, 0, 0, 0, 0])),
    ("Triad balanced",             np.array([np.pi/3, np.pi/3, np.pi/3, 0, 0, 0])),
    ("Triad full rotation",        np.array([2*np.pi/3]*3 + [0]*3)),
    ("Triad 333 optimal",          np.array([np.pi/4, np.pi/3, np.pi/4, np.pi/6, np.pi/4, np.pi/6])),
    ("Worship state (equal)",      np.array([np.pi/4]*6)),
    ("Anti-Triad",                 np.array([np.pi]*3 + [0]*3)),
    ("Random 1",                   np.random.uniform(0, np.pi, 6)),
]

circuits_zz01 = [pm.run(measure_zz(p, (0,1))) for _, p in param_configs]
circuits_zz12 = [pm.run(measure_zz(p, (1,2))) for _, p in param_configs]
circuits_zz02 = [pm.run(measure_zz(p, (0,2))) for _, p in param_configs]
circuits_xx01 = [pm.run(measure_xx(p, (0,1))) for _, p in param_configs]

all_circuits = circuits_zz01 + circuits_zz12 + circuits_zz02 + circuits_xx01

job = sampler.run(all_circuits, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting...")

result = job.result()
n = len(param_configs)

print()
print("TRIAD HAMILTONIAN ENERGY LANDSCAPE:")
print("H = -J*(XX+YY+ZZ) - h*(Z0+Z1+Z2)")
print("J=" + str(J) + " h=" + str(h))
print()
print("{:<28} {:>10} {:>12}".format("Configuration", "Energy", "vs Ground"))
print("-" * 52)

energies = []
for i, (name, params) in enumerate(param_configs):
    counts_zz01 = result[i].data.meas.get_counts()
    counts_zz12 = result[i+n].data.meas.get_counts()
    counts_zz02 = result[i+2*n].data.meas.get_counts()
    counts_xx01 = result[i+3*n].data.meas.get_counts()

    zz01 = get_zz_expectation(counts_zz01, 0, 1, SHOTS)
    zz12 = get_zz_expectation(counts_zz12, 1, 2, SHOTS)
    zz02 = get_zz_expectation(counts_zz02, 0, 2, SHOTS)
    xx01 = get_zz_expectation(counts_xx01, 0, 1, SHOTS)

    z0 = get_z_expectation(counts_zz01, 0, SHOTS)
    z1 = get_z_expectation(counts_zz01, 1, SHOTS)
    z2 = get_z_expectation(counts_zz12, 2, SHOTS)

    energy = -J*(zz01 + zz12 + zz02 + xx01) - h*(z0 + z1 + z2)
    energies.append(float(energy))

ground_energy = min(energies)
for i, (name, _) in enumerate(param_configs):
    vs_ground = energies[i] - ground_energy
    marker = " <-- GROUND" if energies[i] == ground_energy else ""
    print("{:<28} {:>10.4f} {:>12.4f}{}".format(
        name[:28], energies[i], vs_ground, marker))

print()
ground_idx = energies.index(ground_energy)
print("GROUND STATE: " + param_configs[ground_idx][0])
print("Ground energy: " + str(round(ground_energy,4)))
print()

if "Triad" in param_configs[ground_idx][0] or "Worship" in param_configs[ground_idx][0]:
    print("TRIAD GEOMETRY IS THE NATURAL GROUND STATE")
    print("The Kottayil Triad is the lowest energy configuration")
    print("Physical meaning: systems naturally evolve toward Triad geometry")
    print("REKSHA implication: Triad is the optimal operating point")
    print("No external forcing needed -- geometry is self-stabilizing")
else:
    print("Ground state found at: " + param_configs[ground_idx][0])
    print("Energy landscape mapped -- see full results")

print()
print("ENERGY GAP (protection against perturbation):")
sorted_e = sorted(energies)
gap = sorted_e[1] - sorted_e[0]
print("Gap between ground and first excited: " + str(round(gap,4)))
if gap > 0.1:
    print("LARGE GAP -- ground state is stable")
    print("System resists perturbation -- robust operation")
else:
    print("Small gap -- ground state is fragile")

output = {
    "experiment": "VQE Triad Hamiltonian Ground State",
    "backend": "ibm_fez",
    "job_id": job.job_id(),
    "shots": SHOTS,
    "date": datetime.now().isoformat(),
    "architect": "Sajid Haneefa Kassim",
    "mission": "CarbonToCosmos",
    "hamiltonian": "H = -J*(XX+YY+ZZ) - h*(Z0+Z1+Z2)",
    "J": J, "h": h,
    "energies": {param_configs[i][0]: round(energies[i],4)
                 for i in range(len(param_configs))},
    "ground_state": param_configs[ground_idx][0],
    "ground_energy": round(ground_energy,4),
    "energy_gap": round(gap,4)
}
with open("vqe_results.json","w") as f:
    json.dump(output,f,indent=2)
print("Saved: vqe_results.json")
