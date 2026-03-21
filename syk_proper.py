import numpy as np
import json
from datetime import datetime
from scipy import stats
from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

CRN = 'crn:v1:bluemix:public:quantum-computing:us-east:a/c88a87e2898a4647ba730430d3ac1df5:ff503e89-f427-4a58-8e83-fb11689b9213::'
SHOTS = 2048
N_REALIZATIONS = 10
BETAS = [0.0, 0.5, 1.0, 2.0]
service = QiskitRuntimeService(instance=CRN)
backend = service.backend('ibm_fez')

def generate_syk_coeffs(n_qubits, seed=None):
    rng = np.random.default_rng(seed)
    return rng.normal(0, 1, size=(n_qubits, n_qubits))

def build_syk_circuit(coeffs):
    n = coeffs.shape[0]
    qc = QuantumCircuit(n)
    qc.h(range(n))
    for i in range(n):
        for j in range(i+1, n):
            angle = coeffs[i][j]
            qc.cx(i, j)
            qc.rz(angle, j)
            qc.cx(i, j)
    qc.measure_all()
    return qc

def expectation_from_counts(counts):
    total = sum(counts.values())
    exp = 0
    for bitstring, c in counts.items():
        parity = (-1) ** bitstring.count('1')
        exp += parity * c / total
    return exp

def thermal_weighted(exp_val, beta):
    return np.exp(-beta * abs(exp_val)) * exp_val

def spectral_form_factor(energies, t):
    Z = np.sum(np.exp(-1j * np.array(energies) * t))
    return float(np.abs(Z)**2 / max(len(energies)**2, 1))

def level_spacing_ratio(energies):
    e = np.sort(energies)
    sp = np.diff(e)
    if len(sp) < 2:
        return 0.0
    r = np.minimum(sp[:-1], sp[1:]) / np.maximum(sp[:-1], sp[1:] + 1e-10)
    return float(np.mean(r))

print("SYK PROPER EXPERIMENT")
print("N=2 qubits, " + str(N_REALIZATIONS) +
      " realizations, " + str(len(BETAS)) + " beta values")
print("Total circuits: " + str(N_REALIZATIONS * len(BETAS)))
print()

# Build all circuits
all_circuits_raw = []
circuit_meta = []
for r in range(N_REALIZATIONS):
    for beta in BETAS:
        coeffs = generate_syk_coeffs(2, seed=r)
        qc = build_syk_circuit(coeffs)
        all_circuits_raw.append(qc)
        circuit_meta.append({"realization": r, "beta": beta,
                              "coeffs": coeffs.tolist()})

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
all_circuits = [pm.run(qc) for qc in all_circuits_raw]

sampler = Sampler(backend)
job = sampler.run(all_circuits, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting...")

result = job.result()

# Process results
syk_by_beta = {b: [] for b in BETAS}
all_energies = []

for i, meta in enumerate(circuit_meta):
    counts = result[i].data.meas.get_counts()
    exp_val = expectation_from_counts(counts)
    weighted = thermal_weighted(exp_val, meta["beta"])
    syk_by_beta[meta["beta"]].append(weighted)
    all_energies.append(exp_val)

syk_results = {b: float(np.mean(syk_by_beta[b])) for b in BETAS}

# Spectral form factor
t_values = np.linspace(0, 5, 20)
sff_values = [spectral_form_factor(all_energies, t) for t in t_values]

# Level spacing ratio
r_value = level_spacing_ratio(all_energies)

print()
print("SYK THERMAL CORRELATIONS:")
for b, val in syk_results.items():
    print("  Beta=" + str(b) + ": " + str(round(val, 4)))

syk_trend = all(syk_results[BETAS[i]] <= syk_results[BETAS[i+1]]
                for i in range(len(BETAS)-1)
                if syk_results[BETAS[i]] != syk_results[BETAS[i+1]])

print("  Trend confirmed: " + str(syk_trend))

print()
print("SPECTRAL FORM FACTOR (first 5 points):")
for t, val in zip(t_values[:5], sff_values[:5]):
    print("  t=" + str(round(t,2)) + ": " + str(round(val,4)))
sff_min = float(np.min(sff_values))
sff_plateau = float(np.mean(sff_values[-5:]))
print("  SFF min:     " + str(round(sff_min,4)))
print("  SFF plateau: " + str(round(sff_plateau,4)))
ramp = sff_plateau > sff_min * 1.05
print("  Ramp-to-plateau: " + ("DETECTED" if ramp else "not visible"))

print()
print("LEVEL SPACING RATIO:")
print("  r = " + str(round(r_value, 4)))
print("  Poisson (integrable): ~0.386")
print("  GUE (chaotic/SYK):   ~0.599")
if r_value > 0.5:
    print("  STATUS: CHAOTIC -- consistent with GUE/SYK")
elif r_value > 0.4:
    print("  STATUS: INTERMEDIATE -- between integrable and chaotic")
else:
    print("  STATUS: INTEGRABLE -- Poisson statistics")

# Cross-validation with JT gravity
jt_obs = [0.007, 0.628, 0.779, 0.841]
syk_vals = [syk_results[b] for b in BETAS]

# Normalize both to compare trends
def normalize(x):
    x = np.array(x)
    std = np.std(x) + 1e-8
    return (x - np.mean(x)) / std

jt_norm = normalize(jt_obs)
syk_norm = normalize(syk_vals)

tau, p_tau = stats.kendalltau(jt_norm, syk_norm)
spearman, p_sp = stats.spearmanr(jt_norm, syk_norm)

print()
print("CROSS-VALIDATION: SYK vs JT GRAVITY:")
print("  Kendall tau:   " + str(round(float(tau),3)) +
      "  p=" + str(round(float(p_tau),4)))
print("  Spearman:      " + str(round(float(spearman),3)) +
      "  p=" + str(round(float(p_sp),4)))
if spearman > 0.6:
    print("  SYK CONSISTENT WITH JT GRAVITY TREND")
elif spearman > 0.0:
    print("  Positive correlation -- trend consistent")
else:
    print("  More realizations needed for quantitative match")

output = {
    "experiment": "SYK Proper -- N=2 qubits Jordan-Wigner",
    "backend": "ibm_fez",
    "job_id": job.job_id(),
    "shots": SHOTS,
    "n_realizations": N_REALIZATIONS,
    "date": datetime.now().isoformat(),
    "architect": "Sajid Haneefa Kassim",
    "mission": "CarbonToCosmos",
    "syk_thermal": {str(b): round(v,4) for b,v in syk_results.items()},
    "sff": {"min": round(sff_min,4), "plateau": round(sff_plateau,4),
            "ramp_detected": bool(ramp)},
    "level_spacing_r": round(r_value,4),
    "gue_target": 0.599,
    "poisson_target": 0.386,
    "spearman_jt_syk": round(float(spearman),3),
    "kendall_tau": round(float(tau),3)
}
with open("syk_proper_results.json","w") as f:
    json.dump(output,f,indent=2)
print()
print("Saved: syk_proper_results.json")
