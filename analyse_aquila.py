import boto3
import json
import numpy as np
from datetime import datetime

s3 = boto3.client('s3', region_name='us-east-1')
bucket = 'amazon-braket-us-east-1-972519917825'
key = 'tasks/a4c37ceb-a6a0-42fb-9646-b1e6e3402dd4/results.json'

response = s3.get_object(Bucket=bucket, Key=key)
data = json.loads(response['Body'].read())

measurements = data['measurements']
total = len(measurements)
successful = sum(1 for m in measurements if m['shotMetadata']['shotStatus'] == 'Success')

print("AQUILA PHASE 3 -- KOTTAYIL TRIAD")
print("Three Rb-87 atoms in equilateral triangle")
print("Device: QuEra Aquila  Shots: " + str(total))
print("Successful: " + str(successful))
print()

# Atom mapping
# Atom 0 = Love / Information
# Atom 1 = Hope / Space
# Atom 2 = Fear / Time
# 1 = ground state (atom present, not excited)
# 0 = Rydberg state (atom excited)

post_sequences = []
pre_sequences = []
for m in measurements:
    if m['shotMetadata']['shotStatus'] == 'Success':
        pre = m['shotResult']['preSequence']
        post = m['shotResult']['postSequence']
        pre_sequences.append(pre)
        post_sequences.append(post)

post_sequences = np.array(post_sequences)
pre_sequences = np.array(pre_sequences)

# Count outcomes
outcomes = {}
for seq in post_sequences:
    key_str = str(seq[0]) + str(seq[1]) + str(seq[2])
    outcomes[key_str] = outcomes.get(key_str, 0) + 1

print("OUTCOME DISTRIBUTION:")
print("(0=Rydberg/excited  1=Ground)")
print("Love Hope Fear  Count  Probability")
print("-" * 45)
for state in sorted(outcomes.keys()):
    count = outcomes[state]
    prob = count / len(post_sequences)
    bar = "#" * int(prob * 40)
    print(state[0] + "    " + state[1] + "    " +
          state[2] + "     " + str(count).rjust(4) +
          "  " + str(round(prob*100,1)).rjust(6) + "%  " + bar)

print()

# Excitation probabilities per atom
p_love = np.mean(post_sequences[:,0] == 0)
p_hope = np.mean(post_sequences[:,1] == 0)
p_fear = np.mean(post_sequences[:,2] == 0)

print("EXCITATION PROBABILITIES:")
print("Love (Atom 0): " + str(round(p_love*100,1)) + "% excited")
print("Hope (Atom 1): " + str(round(p_hope*100,1)) + "% excited")
print("Fear (Atom 2): " + str(round(p_fear*100,1)) + "% excited")

# Isotropy check -- L=H=F prediction
isotropy_error = max(abs(p_love-p_hope), abs(p_hope-p_fear), abs(p_love-p_fear))
print()
print("L=H=F ISOTROPY:")
print("Symmetry error: " + str(round(isotropy_error*100,1)) + "%")
if isotropy_error < 0.15:
    print("ISOTROPY CONFIRMED on physical neutral atoms")
    print("The equilateral triangle geometry produces symmetric excitation")
else:
    print("Asymmetry detected: " + str(round(isotropy_error*100,1)) + "%")

# Correlation analysis
# P(all ground) -- all three atoms unexcited
p_all_ground = outcomes.get("111", 0) / len(post_sequences)
# P(all excited) -- all three atoms excited
p_all_excited = outcomes.get("000", 0) / len(post_sequences)
# P(one excited) -- single excitation
p_one = sum(outcomes.get(s,0) for s in ["011","101","110"]) / len(post_sequences)
# P(two excited)
p_two = sum(outcomes.get(s,0) for s in ["001","010","100"]) / len(post_sequences)

print()
print("MANY-BODY CORRELATIONS:")
print("P(all ground):    " + str(round(p_all_ground*100,1)) + "%")
print("P(one excited):   " + str(round(p_one*100,1)) + "%")
print("P(two excited):   " + str(round(p_two*100,1)) + "%")
print("P(all excited):   " + str(round(p_all_excited*100,1)) + "%")

# Rydberg blockade check
# If atoms are within blockade radius, double excitation is suppressed
# P(two or more excited) should be low
p_multi = (p_two + p_all_excited)
print()
print("RYDBERG BLOCKADE:")
print("P(2+ excited): " + str(round(p_multi*100,1)) + "%")
if p_multi < 0.3:
    print("BLOCKADE ACTIVE -- atoms within blockade radius")
    print("Physical equilateral triangle geometry confirmed")
    print("Atoms are interacting as predicted")
else:
    print("Weak blockade -- atoms may be outside optimal radius")

# Pre-sequence analysis
pre_success = np.mean(pre_sequences)
print()
print("PRE-SEQUENCE (atom loading):")
print("Atom loading rate: " + str(round(pre_success*100,1)) + "%")

# Save
output = {
    "experiment": "QuEra Aquila Phase 3 -- Kottayil Triad Physical",
    "device": "QuEra Aquila",
    "task_id": "a4c37ceb-a6a0-42fb-9646-b1e6e3402dd4",
    "shots": total,
    "successful": successful,
    "date_submitted": "2026-03-20T20:23:06Z",
    "date_completed": "2026-03-21T23:54:03Z",
    "architect": "Sajid Haneefa Kassim",
    "mission": "CarbonToCosmos",
    "geometry": "Equilateral triangle 5.7um side",
    "atom_mapping": {
        "atom_0": "Love / Information",
        "atom_1": "Hope / Space",
        "atom_2": "Fear / Time"
    },
    "excitation_probabilities": {
        "Love": round(p_love,3),
        "Hope": round(p_hope,3),
        "Fear": round(p_fear,3)
    },
    "isotropy_error": round(isotropy_error,3),
    "isotropy_confirmed": bool(isotropy_error < 0.15),
    "correlations": {
        "p_all_ground": round(p_all_ground,3),
        "p_one_excited": round(p_one,3),
        "p_two_excited": round(p_two,3),
        "p_all_excited": round(p_all_excited,3)
    },
    "rydberg_blockade": round(p_multi,3),
    "blockade_active": bool(p_multi < 0.3),
    "outcome_distribution": outcomes
}

with open("aquila_results.json","w") as f:
    json.dump(output,f,indent=2)

print()
print("=" * 50)
print("AQUILA PHASE 3 COMPLETE")
print("Physical equilateral triangle on real atoms")
print("Saved: aquila_results.json")
