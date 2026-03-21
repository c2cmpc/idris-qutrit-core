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

print("PHASE COHERENCE + SPIN DYNAMICS IN AC TRIAD FIELD")
print("Dynamic phase vs Geometric phase comparison")
print("Radiation trapping efficiency prediction")
print()

# PHYSICAL MAPPING:
# One qubit = spin of incoming charged particle (proton)
# RZ(theta) = dynamic phase from AC field (time-dependent)
# RY(theta) = geometric phase from field geometry (path-dependent)
# Sequence of rotations = particle traversing rotating field
# P(|0>) at end = probability particle is TRAPPED (not deflected)
# High P(|0>) = particle returns to original spin state = trapped
# Low P(|0>) = particle spin flipped = deflected

# AC FREQUENCY STEPS
# Each step = one quarter cycle of AC field
# Triad: 120 degree offset between three coil phases
# At each step the field rotates and the particle spin precesses

def make_ac_dipole(n_cycles, field_strength):
    qc = QuantumCircuit(1)
    # Dipole AC: field oscillates on one axis only
    # Linear oscillation -- two dead directions
    for _ in range(n_cycles):
        qc.ry(field_strength * np.pi / 2, 0)   # field up
        qc.rz(field_strength * np.pi / 4, 0)   # dynamic phase
        qc.ry(-field_strength * np.pi / 2, 0)  # field down
        qc.rz(field_strength * np.pi / 4, 0)   # dynamic phase
    qc.measure_all()
    return qc

def make_ac_triad(n_cycles, field_strength):
    qc = QuantumCircuit(1)
    # Triad AC: field rotates continuously
    # Three phases 120 degrees apart
    # Continuous rotation -- no dead directions
    phase_step = 2 * np.pi / 3  # 120 degrees per step
    for _ in range(n_cycles):
        # Phase 1: Love/Information axis (0 degrees)
        qc.ry(field_strength * np.sin(0), 0)
        qc.rz(field_strength * np.cos(0), 0)
        # Phase 2: Hope/Space axis (120 degrees)
        qc.ry(field_strength * np.sin(phase_step), 0)
        qc.rz(field_strength * np.cos(phase_step), 0)
        # Phase 3: Fear/Time axis (240 degrees)
        qc.ry(field_strength * np.sin(2*phase_step), 0)
        qc.rz(field_strength * np.cos(2*phase_step), 0)
    qc.measure_all()
    return qc

def make_dc_triad(field_strength):
    qc = QuantumCircuit(1)
    # DC Triad: static field -- Berry phase only
    # No dynamic phase
    qc.ry(2 * np.pi / 3, 0)   # geometric only
    qc.ry(2 * np.pi / 3, 0)
    qc.ry(2 * np.pi / 3, 0)
    qc.measure_all()
    return qc

def make_resonant_triad(n_cycles):
    qc = QuantumCircuit(1)
    # Resonant Triad: field frequency matches Larmor frequency
    # Maximum energy transfer to particle
    # This is the trapping condition
    phase_step = 2 * np.pi / 3
    for _ in range(n_cycles):
        qc.ry(np.pi / 2 * np.sin(0), 0)
        qc.rz(np.pi / 2 * np.cos(0), 0)
        qc.ry(np.pi / 2 * np.sin(phase_step), 0)
        qc.rz(np.pi / 2 * np.cos(phase_step), 0)
        qc.ry(np.pi / 2 * np.sin(2*phase_step), 0)
        qc.rz(np.pi / 2 * np.cos(2*phase_step), 0)
    qc.measure_all()
    return qc

# Build circuit set
# Test at different cycle counts (particle transit times)
# and different field strengths
circuits_raw = []
labels = []

# Reference
qc_ref = QuantumCircuit(1)
qc_ref.measure_all()
circuits_raw.append(qc_ref)
labels.append("Reference (no field)")

# DC Triad (Berry phase only -- Exp 4 baseline)
circuits_raw.append(make_dc_triad(1.0))
labels.append("DC Triad (geometric phase)")

# AC Dipole at different cycle counts
for n in [1, 2, 3]:
    circuits_raw.append(make_ac_dipole(n, 0.5))
    labels.append("AC Dipole " + str(n) + " cycles")

# AC Triad at different cycle counts
for n in [1, 2, 3]:
    circuits_raw.append(make_ac_triad(n, 0.5))
    labels.append("AC Triad " + str(n) + " cycles")

# Resonant Triad (Larmor resonance condition)
for n in [1, 2, 3]:
    circuits_raw.append(make_resonant_triad(n))
    labels.append("Resonant Triad " + str(n) + " cycles")

# High field strength comparison
circuits_raw.append(make_ac_dipole(2, 1.0))
labels.append("AC Dipole high field")
circuits_raw.append(make_ac_triad(2, 1.0))
labels.append("AC Triad high field")

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
circuits = [pm.run(qc) for qc in circuits_raw]

sampler = Sampler(backend)
job = sampler.run(circuits, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting...")

result = job.result()

print()
print("SPIN DYNAMICS RESULTS:")
print("P(|0>) = particle in original spin state")
print("High = trapped  Low = deflected")
print("=" * 60)

ground_probs = []
for i, label in enumerate(labels):
    counts = result[i].data.meas.get_counts()
    total = sum(counts.values())
    p0 = counts.get("0", 0) / total
    ground_probs.append(p0)
    print("{:<35} {:>8.3f}".format(label[:35], p0))

print()
print("PHASE COHERENCE ANALYSIS:")
print()

ref = ground_probs[0]
dc_triad = ground_probs[1]

ac_dipole = [ground_probs[2], ground_probs[3], ground_probs[4]]
ac_triad = [ground_probs[5], ground_probs[6], ground_probs[7]]
res_triad = [ground_probs[8], ground_probs[9], ground_probs[10]]

print("Dynamic phase buildup (AC Dipole across cycles):")
for i, p in enumerate(ac_dipole):
    print("  Cycle " + str(i+1) + ": " + str(round(p,3)))

print()
print("Geometric + Dynamic (AC Triad across cycles):")
for i, p in enumerate(ac_triad):
    print("  Cycle " + str(i+1) + ": " + str(round(p,3)))

print()
print("Resonant condition (Triad at Larmor frequency):")
for i, p in enumerate(res_triad):
    print("  Cycle " + str(i+1) + ": " + str(round(p,3)))

print()
print("DC Triad (Berry/geometric phase only): " +
      str(round(dc_triad,3)))

# Compare AC vs DC Triad
# AC Triad at 3 cycles vs DC Triad
ac_triad_3 = ac_triad[2]
if ac_triad_3 > dc_triad:
    print()
    print("AC TRIAD > DC TRIAD")
    print("Dynamic phase ADDS to geometric phase")
    print("Rotating field ENHANCES trapping vs static field")
elif ac_triad_3 < dc_triad:
    print()
    print("DC TRIAD > AC TRIAD")
    print("Geometric phase dominates")
    print("Static field more efficient for this particle energy")

# Resonance check
res_max = max(res_triad)
ac_max = max(ac_triad)
if res_max > ac_max:
    print()
    print("RESONANT CONDITION SUPERIOR TO OFF-RESONANCE AC")
    print("Larmor frequency matching improves trapping")
    print("Design implication: tune AC frequency to particle energy")

# Dipole vs Triad comparison at same cycles
print()
print("AC TRIAD vs AC DIPOLE (equal cycles, equal field):")
for i in range(3):
    diff = ac_triad[i] - ac_dipole[i]
    better = "Triad" if diff > 0 else "Dipole"
    print("  Cycle " + str(i+1) + ": Triad=" +
          str(round(ac_triad[i],3)) +
          " Dipole=" + str(round(ac_dipole[i],3)) +
          " Advantage: " + better +
          " (" + str(round(abs(diff)*100,1)) + "%)")

# High field comparison
hf_dipole = ground_probs[11]
hf_triad = ground_probs[12]
print()
print("HIGH FIELD STRENGTH COMPARISON:")
print("  AC Dipole: " + str(round(hf_dipole,3)))
print("  AC Triad:  " + str(round(hf_triad,3)))

output = {
    "experiment": "Phase Coherence Spin Dynamics AC Triad Shield",
    "backend": "ibm_fez",
    "job_id": job.job_id(),
    "shots": SHOTS,
    "date": datetime.now().isoformat(),
    "architect": "Sajid Haneefa Kassim",
    "mission": "CarbonToCosmos PRANADARA ECLSS",
    "physical_mapping": {
        "qubit": "spin of incoming charged particle (proton)",
        "RZ": "dynamic phase from AC field (time-dependent)",
        "RY": "geometric phase from field geometry (path-dependent)",
        "P0_high": "particle trapped",
        "P0_low": "particle deflected"
    },
    "results": {labels[i]: round(ground_probs[i],3)
                for i in range(len(labels))},
    "key_comparisons": {
        "dc_triad_geometric_only": round(dc_triad,3),
        "ac_triad_3cycles": round(ac_triad[2],3),
        "ac_dipole_3cycles": round(ac_dipole[2],3),
        "resonant_triad_3cycles": round(res_triad[2],3),
        "ac_triad_vs_dipole_advantage": round(
            ac_triad[2] - ac_dipole[2], 3)
    }
}
with open("ac_shield_results.json","w") as f:
    json.dump(output,f,indent=2)
print()
print("Saved: ac_shield_results.json")
