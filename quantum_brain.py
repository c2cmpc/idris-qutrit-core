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

print("QUANTUM BRAIN SIMULATION")
print("Kottayil Triad as neural firing geometry")
print("Q0=Love neuron Q1=Hope neuron Q2=Fear neuron")
print()

# PHYSICAL MAPPING:
# Three neurons -- one per Triad vertex
# Love neuron:  fires on recognition (pattern match)
# Hope neuron:  fires on prediction (pattern completion)
# Fear neuron:  fires on threat (pattern mismatch)
#
# Biological basis:
# Recognition  = hippocampal place cells
# Prediction   = prefrontal cortex
# Threat       = amygdala
#
# Test 1: Lateral inhibition
#   When one neuron fires strongly the others suppress
#   This is the basis of attention and focus
#   Triad geometry should produce natural inhibition
#   via K3 entanglement
#
# Test 2: Pattern completion
#   Given partial input -- complete the pattern
#   Love neuron receives partial signal
#   Hope neuron predicts the rest
#   Fear neuron monitors for mismatch
#
# Test 3: Winner-take-all
#   Multiple stimuli compete
#   One neuron dominates
#   Others suppress
#   Tests whether Triad produces clean decisions

# ── TEST 1: LATERAL INHIBITION ──
# Strong input to Love neuron
# Does Fear and Hope suppress?

# Strong Love activation (full input)
qc_love_strong = QuantumCircuit(3)
qc_love_strong.x(0)           # Love fires strongly
qc_love_strong.cx(0, 1)       # Love inhibits Hope
qc_love_strong.cx(0, 2)       # Love inhibits Fear
qc_love_strong.cx(1, 2)       # K3 completion
qc_love_strong.measure_all()

# Strong Hope activation
qc_hope_strong = QuantumCircuit(3)
qc_hope_strong.x(1)           # Hope fires strongly
qc_hope_strong.cx(1, 0)       # Hope inhibits Love
qc_hope_strong.cx(1, 2)       # Hope inhibits Fear
qc_hope_strong.cx(0, 2)       # K3 completion
qc_hope_strong.measure_all()

# Strong Fear activation
qc_fear_strong = QuantumCircuit(3)
qc_fear_strong.x(2)           # Fear fires strongly
qc_fear_strong.cx(2, 0)       # Fear inhibits Love
qc_fear_strong.cx(2, 1)       # Fear inhibits Hope
qc_fear_strong.cx(0, 1)       # K3 completion
qc_fear_strong.measure_all()

# All three equal -- balanced brain state
qc_balanced = QuantumCircuit(3)
qc_balanced.h(0)
qc_balanced.h(1)
qc_balanced.h(2)
qc_balanced.cx(0, 1)
qc_balanced.cx(1, 2)
qc_balanced.cx(2, 0)
qc_balanced.measure_all()

# ── TEST 2: PATTERN COMPLETION ──
# Partial input to Love -- does Hope complete it?

# Half signal to Love -- Hope should predict
qc_partial = QuantumCircuit(3)
qc_partial.ry(np.pi/4, 0)     # Love half-activated
qc_partial.cx(0, 1)           # Love signals Hope
qc_partial.ry(np.pi/3, 1)     # Hope predicts
qc_partial.cx(1, 2)           # Hope signals Fear
qc_partial.cx(2, 0)           # Fear monitors Love
qc_partial.measure_all()

# Full signal to Love -- Hope confirms
qc_full = QuantumCircuit(3)
qc_full.ry(np.pi/2, 0)        # Love fully activated
qc_full.cx(0, 1)
qc_full.ry(np.pi/2, 1)        # Hope confirms
qc_full.cx(1, 2)
qc_full.cx(2, 0)
qc_full.measure_all()

# No signal -- resting state
qc_rest = QuantumCircuit(3)
qc_rest.ry(np.pi/6, 0)        # minimal Love
qc_rest.cx(0, 1)
qc_rest.ry(np.pi/6, 1)        # minimal Hope
qc_rest.cx(1, 2)
qc_rest.cx(2, 0)
qc_rest.measure_all()

# ── TEST 3: WINNER TAKE ALL ──
# Two competing stimuli -- which neuron dominates?

# Love vs Hope competition
qc_love_hope = QuantumCircuit(3)
qc_love_hope.ry(np.pi/2, 0)   # Love strong
qc_love_hope.ry(np.pi/3, 1)   # Hope moderate
qc_love_hope.cx(0, 1)         # Love suppresses Hope
qc_love_hope.cx(1, 2)
qc_love_hope.cx(2, 0)
qc_love_hope.measure_all()

# Hope vs Fear competition
qc_hope_fear = QuantumCircuit(3)
qc_hope_fear.ry(np.pi/2, 1)   # Hope strong
qc_hope_fear.ry(np.pi/3, 2)   # Fear moderate
qc_hope_fear.cx(1, 2)         # Hope suppresses Fear
qc_hope_fear.cx(0, 1)
qc_hope_fear.cx(2, 0)
qc_hope_fear.measure_all()

# Fear vs Love competition (threat overrides recognition)
qc_fear_love = QuantumCircuit(3)
qc_fear_love.ry(np.pi/2, 2)   # Fear strong (threat detected)
qc_fear_love.ry(np.pi/4, 0)   # Love moderate
qc_fear_love.cx(2, 0)         # Fear suppresses Love
qc_fear_love.cx(2, 1)         # Fear suppresses Hope
qc_fear_love.cx(0, 1)
qc_fear_love.measure_all()

configs = [
    ("Love neuron dominant",     qc_love_strong),
    ("Hope neuron dominant",     qc_hope_strong),
    ("Fear neuron dominant",     qc_fear_strong),
    ("Balanced brain state",     qc_balanced),
    ("Partial input (50%)",      qc_partial),
    ("Full input (100%)",        qc_full),
    ("Resting state",            qc_rest),
    ("Love vs Hope competition", qc_love_hope),
    ("Hope vs Fear competition", qc_hope_fear),
    ("Fear vs Love (threat)",    qc_fear_love),
]

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
circuits = [pm.run(c) for _, c in configs]

sampler = Sampler(backend)
job = sampler.run(circuits, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting...")

result = job.result()

print()
print("QUANTUM BRAIN SIMULATION RESULTS:")
print("=" * 65)
print("{:<30} {:>8} {:>8} {:>8} {:>10}".format(
    "State", "Love", "Hope", "Fear", "Dominant"))
print("-" * 65)

brain_data = []
for i, (name, _) in enumerate(configs):
    counts = result[i].data.meas.get_counts()
    total = sum(counts.values())

    # Firing probability per neuron
    # P(qubit=1) = neuron firing
    p_love = sum(v for k,v in counts.items() if k[2]=='1') / total
    p_hope = sum(v for k,v in counts.items() if k[1]=='1') / total
    p_fear = sum(v for k,v in counts.items() if k[0]=='1') / total

    # Dominant neuron
    firing = {"Love": p_love, "Hope": p_hope, "Fear": p_fear}
    dominant = max(firing, key=firing.get)

    brain_data.append({
        "state": name,
        "love": p_love,
        "hope": p_hope,
        "fear": p_fear,
        "dominant": dominant
    })

    print("{:<30} {:>8.3f} {:>8.3f} {:>8.3f} {:>10}".format(
        name[:30], p_love, p_hope, p_fear, dominant))

print()
print("NEUROSCIENCE ANALYSIS:")
print()

# Lateral inhibition check
love_dom = brain_data[0]
hope_dom = brain_data[1]
fear_dom = brain_data[2]

print("LATERAL INHIBITION:")
print("  Love dominant -- Hope suppressed to: " +
      str(round(love_dom["hope"],3)) +
      " Fear suppressed to: " + str(round(love_dom["fear"],3)))
print("  Hope dominant -- Love suppressed to: " +
      str(round(hope_dom["love"],3)) +
      " Fear suppressed to: " + str(round(hope_dom["fear"],3)))
print("  Fear dominant -- Love suppressed to: " +
      str(round(fear_dom["love"],3)) +
      " Hope suppressed to: " + str(round(fear_dom["hope"],3)))

love_inhibition = 1 - (love_dom["hope"] + love_dom["fear"])/2
hope_inhibition = 1 - (hope_dom["love"] + hope_dom["fear"])/2
fear_inhibition = 1 - (fear_dom["love"] + fear_dom["hope"])/2

print("  Love inhibition strength:  " + str(round(love_inhibition,3)))
print("  Hope inhibition strength:  " + str(round(hope_inhibition,3)))
print("  Fear inhibition strength:  " + str(round(fear_inhibition,3)))

if fear_inhibition > love_inhibition and fear_inhibition > hope_inhibition:
    print()
    print("FEAR DOMINATES INHIBITION")
    print("Threat detection overrides all other processing")
    print("Consistent with amygdala hijack in biological brains")
    print("Connection to Fear=Time: boundary enforcement is strongest")

# Pattern completion
partial = brain_data[4]
full = brain_data[5]
rest = brain_data[6]

print()
print("PATTERN COMPLETION:")
print("  Resting:  Love=" + str(round(rest["love"],3)) +
      " Hope=" + str(round(rest["hope"],3)))
print("  Partial:  Love=" + str(round(partial["love"],3)) +
      " Hope=" + str(round(partial["hope"],3)))
print("  Full:     Love=" + str(round(full["love"],3)) +
      " Hope=" + str(round(full["hope"],3)))

hope_completion = full["hope"] - partial["hope"]
print("  Hope gain from partial to full: " +
      str(round(hope_completion,3)))
if full["hope"] > partial["hope"] > rest["hope"]:
    print("  PATTERN COMPLETION CONFIRMED")
    print("  Hope neuron scales with input completeness")
    print("  Prediction strengthens as more information arrives")

# Winner take all
print()
print("WINNER TAKE ALL:")
wta1 = brain_data[7]
wta2 = brain_data[8]
wta3 = brain_data[9]

print("  Love vs Hope: dominant=" + wta1["dominant"])
print("  Hope vs Fear: dominant=" + wta2["dominant"])
print("  Fear vs Love: dominant=" + wta3["dominant"])

if wta3["dominant"] == "Fear":
    print()
    print("THREAT OVERRIDE CONFIRMED")
    print("Fear wins when competing with Love")
    print("Survival instinct overrides recognition")
    print("Consistent with biological amygdala override")
    print("Connection: Fear=Time=boundary=survival")

output = {
    "experiment": "Quantum Brain Simulation -- Triad Neural Firing",
    "backend": "ibm_fez",
    "job_id": job.job_id(),
    "shots": SHOTS,
    "date": datetime.now().isoformat(),
    "architect": "Sajid Haneefa Kassim",
    "mission": "CarbonToCosmos",
    "neuroscience_mapping": {
        "Love_neuron": "Hippocampus -- recognition",
        "Hope_neuron": "Prefrontal cortex -- prediction",
        "Fear_neuron": "Amygdala -- threat detection"
    },
    "results": brain_data,
    "lateral_inhibition": {
        "love_strength": round(love_inhibition,3),
        "hope_strength": round(hope_inhibition,3),
        "fear_strength": round(fear_inhibition,3)
    }
}
with open("quantum_brain_results.json","w") as f:
    json.dump(output,f,indent=2)
print()
print("Saved: quantum_brain_results.json")
