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

def build_circuit(encoding, error_qubit):
    qc = QuantumCircuit(3)
    qc.cx(0, 1)
    qc.cx(0, 2)
    if encoding == "triad":
        for q in range(3):
            qc.ry(2 * np.pi / 3, q)
    elif encoding == "random":
        qc.ry(np.pi / 5, 0)
        qc.ry(np.pi / 7, 1)
        qc.ry(np.pi / 3, 2)
    if error_qubit >= 0:
        qc.x(error_qubit)
    if encoding == "triad":
        for q in range(3):
            qc.ry(-2 * np.pi / 3, q)
    elif encoding == "random":
        qc.ry(-np.pi / 3, 2)
        qc.ry(-np.pi / 7, 1)
        qc.ry(-np.pi / 5, 0)
    qc.measure_all()
    return qc

circuits_raw = []
circuit_names = []
for encoding in ["standard", "triad", "random"]:
    for error_qubit in [-1, 0, 1, 2]:
        circuits_raw.append(build_circuit(encoding, error_qubit))
        label = "no_error" if error_qubit < 0 else "error_Q" + str(error_qubit)
        circuit_names.append(encoding + "_" + label)

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
circuits = [pm.run(qc) for qc in circuits_raw]

print("TRIAD QEC v2 -- Encode -> Error -> Decode -> Majority vote")
sampler = Sampler(backend)
job = sampler.run(circuits, shots=SHOTS)
print("Job ID: " + job.job_id())
print("Waiting...")
result = job.result()

results_data = {}
for i, name in enumerate(circuit_names):
    counts = result[i].data.meas.get_counts()
    total = sum(counts.values())
    correct = sum(count for state, count in counts.items() if state.count("0") >= 2)
    results_data[name] = round(correct / total, 3)

print()
for encoding in ["standard", "triad", "random"]:
    avg = np.mean([results_data[encoding+"_error_Q"+str(q)] for q in range(3)])
    print(encoding.capitalize() + ": no_error=" + str(round(results_data[encoding+"_no_error"]*100,1)) + "% avg_correction=" + str(round(avg*100,1)) + "%")
    for q in range(3):
        print("  Q"+str(q)+": " + str(round(results_data[encoding+"_error_Q"+str(q)]*100,1)) + "%")

triad_avg = np.mean([results_data["triad_error_Q"+str(q)] for q in range(3)])
standard_avg = np.mean([results_data["standard_error_Q"+str(q)] for q in range(3)])
random_avg = np.mean([results_data["random_error_Q"+str(q)] for q in range(3)])
triad_sym = max([results_data["triad_error_Q"+str(q)] for q in range(3)]) - min([results_data["triad_error_Q"+str(q)] for q in range(3)])
std_sym = max([results_data["standard_error_Q"+str(q)] for q in range(3)]) - min([results_data["standard_error_Q"+str(q)] for q in range(3)])

print()
print("Standard: " + str(round(standard_avg*100,1)) + "%")
print("Triad:    " + str(round(triad_avg*100,1)) + "%")
print("Random:   " + str(round(random_avg*100,1)) + "%")
print("Triad symmetry error: " + str(round(triad_sym*100,1)) + "%")
print("Standard symmetry error: " + str(round(std_sym*100,1)) + "%")

if triad_avg > standard_avg:
    print("TRIAD OUTPERFORMS STANDARD")
elif triad_avg >= standard_avg * 0.95:
    print("TRIAD MATCHES STANDARD")
else:
    print("Standard outperforms Triad")

output = {"experiment":"Triad QEC v2","backend":"ibm_fez","job_id":job.job_id(),"shots":SHOTS,"date":datetime.now().isoformat(),"architect":"Sajid Haneefa Kassim","mission":"CarbonToCosmos","results":results_data,"summary":{"triad_avg_pct":round(triad_avg*100,1),"standard_avg_pct":round(standard_avg*100,1),"random_avg_pct":round(random_avg*100,1),"triad_beats_standard":bool(triad_avg>standard_avg),"triad_symmetry_pct":round(triad_sym*100,1),"standard_symmetry_pct":round(std_sym*100,1)}}
with open("triad_qec_v2_results.json","w") as f:
    json.dump(output,f,indent=2)
print("Saved: triad_qec_v2_results.json")
