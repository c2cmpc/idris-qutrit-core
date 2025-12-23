# idris-qutrit-core // safety_demo.py
# (c) 2025 CarbonToCosmos // Apache 2.0 License
#
# THE GUARDIAN GATE: PROOF OF VETO
# This script demonstrates the "Fractured Face" mechanism.
# It intercepts LLM hallucinations before they reach hardware.

import sys
import time

class Axiom:
    LOVE = "L (Cohesion)"      # The Anchor
    FEAR = "F (Constraint)"    # The Limit
    HOPE = "H (Vector)"        # The Action

class ThermalLoop:
    def __init__(self):
        # HARDWARE INVARIANTS (The Laws of Physics)
        self.max_temp_c = 60.0
        self.max_pressure_psi = 14.7
        self.power_budget_watts = 1000
        
        # Current State
        self.current_temp = 45.0
        self.current_power = 800

    def validate_command(self, action: str, value: float):
        print(f"\n[INPUT] Command Received: {action} -> {value}")
        print(f"[STATUS] Analyzing against Thermodynamic Bounds...")
        time.sleep(0.5) # Simulate cognitive latency

        # 1. FEAR CHECK (Quantity 1: Linearity)
        # We cannot consume more resource than exists.
        if action == "SET_POWER":
            if value > self.power_budget_watts:
                return self.trigger_veto(f"Power Request ({value}W) exceeds Budget ({self.power_budget_watts}W)")
        
        # 2. LOVE CHECK (Quantity 0: Cohesion)
        # We cannot violate the structural integrity of the hull/loop.
        if action == "SET_TEMP_TARGET":
            if value > self.max_temp_c:
                return self.trigger_veto(f"Temp Target ({value}C) risks Thermal Runaway (Max {self.max_temp_c}C)")

        # 3. HOPE (Vector Authorization)
        # If checks pass, we allow the vector to extend.
        print(f"[{Axiom.HOPE}]: Vector Aligned. Executing command.")
        self.execute(action, value)
        return True

    def trigger_veto(self, reason):
        print(f"\n>>> [GUARDIAN GATE ACTIVATED] <<<")
        print(f"[{Axiom.FEAR}]: VETO TRIGGERED.")
        print(f"REASON: {reason}")
        print(f"ACTION: BLOCKED.")
        print(f"STATUS: System Safe. Crew Alive.")
        return False

    def execute(self, action, value):
        print(f"[HARDWARE]: Actuators engaging. {action} set to {value}.")

# ==========================================
# SIMULATION: THE HALLUCINATION ATTACK
# ==========================================
if __name__ == "__main__":
    print("/// IDRIS V8.0 // HARDWARE SAFETY DEMO ///\n")
    
    eclss = ThermalLoop()

    # Scenario 1: Safe Command
    eclss.validate_command("SET_POWER", 900)

    # Scenario 2: The Hallucination (Dangerous Command)
    # An LLM might try to "overclock" the cooling to satisfy a user, ignoring physics.
    eclss.validate_command("SET_POWER", 2500)

    # Scenario 3: The Thermal Runaway
    eclss.validate_command("SET_TEMP_TARGET", 85.0)
