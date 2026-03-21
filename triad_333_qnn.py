import numpy as np
import json
from datetime import datetime
from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

CRN = 'crn:v1:bluemix:public:quantum-computing:us-east:a/c88a87e2898a4647ba730430d3ac1df5:ff503e89-f427-4a58-8e83-fb11689b9213::'
SHOTS = 2048
service = QiskitRuntimeService(instance=CRN)
backend = service.backend('ibm_fez')

print("TRIAD 333 QUANTUM NEURAL NETWORK")
print("Space[Time] = 333[3] architecture")
print("3 layers x 3 qubits x 3 params = 27 parameters")
print("Love layer -> Hope layer -> Fear layer")
print()

def build_333_qnn(params, input_x, input_y):
    """
    333 Triad QNN:
    Layer 1: Love  -- information encoding (RY rotations)
    Layer 2: Hope  -- pattern expansion (RZ rotations)
    Layer 3: Fear  -- output selection (RY+RZ combined)
    Each layer: 3 qubits, K3 entanglement between layers
    Total params: 27
    """
    qc = QuantumCircuit(3, 1)

    # Input encoding
    if input_x: qc.x(0)
    if input_y: qc.x(1)
    qc.h(2)

    # LAYER 1: LOVE -- Information (RY rotations)
    # What IS -- grounding in input
    qc.ry(params[0], 0)
    qc.ry(params[1], 1)
    qc.ry(params[2], 2)
    # K3 entanglement
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.cx(2, 0)

    # LAYER 2: HOPE -- Space expansion (RZ rotations)
    # What COULD BE -- exploring possibility space
    qc.rz(params[3], 0)
    qc.rz(params[4], 1)
    qc.rz(params[5], 2)
    # K3 entanglement
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.cx(2, 0)

    # LAYER 3: FEAR -- Time selection (RY+RZ)
    # What IS SELECTED -- irreversible output
    qc.ry(params[6], 0)
    qc.rz(params[7], 1)
    qc.ry(params[8], 2)
    # Final K3
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.cx(2, 0)

    qc.measure(0, 0)
    return qc

def build_333_standard(params, input_x, input_y):
    """Standard 3-layer QNN without Triad geometry"""
    qc = QuantumCircuit(3, 1)
    if input_x: qc.x(0)
    if input_y: qc.x(1)
    qc.h(2)
    # Layer 1
    qc.ry(params[0], 0)
    qc.ry(params[1], 1)
    qc.ry(params[2], 2)
    qc.cx(0, 1)
    qc.cx(1, 2)  # linear -- not K3
    # Layer 2
    qc.rz(params[3], 0)
    qc.rz(params[4], 1)
    qc.rz(params[5], 2)
    qc.cx(0, 1)
    qc.cx(1, 2)
    # Layer 3
    qc.ry(params[6], 0)
    qc.rz(params[7], 1)
    qc.ry(params[8], 2)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.measure(0, 0)
    return qc

training_data = {
    "AND": [(0,0,0),(0,1,0),(1,0,0),(1,1,1)],
    "OR":  [(0,0,0),(0,1,1),(1,0,1),(1,1,1)],
    "XOR": [(0,0,0),(0,1,1),(1,0,1),(1,1,0)],
}

def get_expectation(counts, shots):
    return counts.get("1", 0) / shots

def mse_loss(predictions, targets):
    return float(np.mean([(p-t)**2 for p,t in zip(predictions,targets)]))

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
sampler = Sampler(backend)

results_all = {}

for gate_name, data in training_data.items():
    print("Training 333 QNN on " + gate_name + "...")

    np.random.seed(42)
    params_333 = np.random.uniform(0, 2*np.pi, 9)
    params_std = np.random.uniform(0, 2*np.pi, 9)

    lr = 0.4
    epsilon = 0.15

    losses_333 = []
    losses_std = []

    for step in range(5):  # 5 steps -- more training
        # Build all circuits
        circuits_333 = [pm.run(build_333_qnn(params_333, x, y))
                        for x,y,_ in data]
        circuits_std = [pm.run(build_333_standard(params_std, x, y))
                        for x,y,_ in data]

        all_circuits = circuits_333 + circuits_std
        job = sampler.run(all_circuits, shots=SHOTS)
        result = job.result()

        preds_333 = [get_expectation(
            result[i].data.c.get_counts(), SHOTS) for i in range(4)]
        preds_std = [get_expectation(
            result[i+4].data.c.get_counts(), SHOTS) for i in range(4)]
        targets = [t for _,_,t in data]

        loss_333 = mse_loss(preds_333, targets)
        loss_std = mse_loss(preds_std, targets)
        losses_333.append(loss_333)
        losses_std.append(loss_std)

        print("  Step " + str(step+1) +
              " | 333 loss: " + str(round(loss_333,4)) +
              " | Standard loss: " + str(round(loss_std,4)))

        # Gradient update -- all parameters
        for i in range(9):
            p_plus = params_333.copy()
            p_plus[i] += epsilon
            qc_g = pm.run(build_333_qnn(p_plus, 1, 1))
            job_g = sampler.run([qc_g], shots=SHOTS)
            res_g = job_g.result()
            p_val = get_expectation(
                res_g[0].data.c.get_counts(), SHOTS)
            grad = (p_val - preds_333[-1]) / epsilon
            params_333[i] -= lr * grad * (preds_333[-1] - targets[-1])

    # Final evaluation
    final_circuits = [pm.run(build_333_qnn(params_333, x, y))
                      for x,y,_ in data]
    job_f = sampler.run(final_circuits, shots=SHOTS)
    res_f = job_f.result()

    print()
    print("  333 QNN FINAL -- " + gate_name + ":")
    correct = 0
    final_preds = []
    for i, (x, y, target) in enumerate(data):
        counts = res_f[i].data.c.get_counts()
        pred = get_expectation(counts, SHOTS)
        pred_b = 1 if pred > 0.5 else 0
        if pred_b == target: correct += 1
        final_preds.append(float(pred))
        print("  (" + str(x) + "," + str(y) + ") pred=" +
              str(round(pred,3)) + " target=" + str(target) +
              " " + ("CORRECT" if pred_b==target else "wrong"))

    accuracy = correct / 4 * 100
    print("  Accuracy: " + str(accuracy) + "%")
    print()

    results_all[gate_name] = {
        "accuracy": float(accuracy),
        "losses_333": losses_333,
        "losses_standard": losses_std,
        "333_beats_standard": bool(losses_333[-1] < losses_std[-1]),
        "final_predictions": final_preds,
        "final_targets": [int(t) for _,_,t in data]
    }

print("=" * 55)
print("333 QNN FINAL SUMMARY:")
for gate, res in results_all.items():
    print(gate + ": " + str(res['accuracy']) + "% | 333 beats standard: " +
          str(res['333_beats_standard']))

output = {
    "experiment": "Triad 333 QNN -- Space[Time]=333[3] architecture",
    "backend": "ibm_fez",
    "shots": SHOTS,
    "date": datetime.now().isoformat(),
    "architect": "Sajid Haneefa Kassim",
    "mission": "CarbonToCosmos",
    "architecture": {
        "layers": 3,
        "qubits": 3,
        "params_per_layer": 3,
        "total_params": 9,
        "layer_1": "Love -- RY rotations -- information",
        "layer_2": "Hope -- RZ rotations -- expansion",
        "layer_3": "Fear -- RY+RZ -- selection",
        "entanglement": "K3 complete graph between all layers"
    },
    "results": results_all
}
with open("triad_333_qnn_results.json","w") as f:
    json.dump(output,f,indent=2)
print("Saved: triad_333_qnn_results.json")
