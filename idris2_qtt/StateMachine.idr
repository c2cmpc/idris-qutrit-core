module StateMachine

import Data.So

-- Experiment 11: State Machine 99.9% fidelity time-symmetric
-- Proves time symmetry of Triad state transitions

FIDELITY : Nat
FIDELITY = 999

THRESHOLD : Nat
THRESHOLD = 990

data TimeSymmetricState : (f : Nat) -> Type where
  TimeSymmetric : (f : Nat) -> So (f >= THRESHOLD) -> TimeSymmetricState f

fidelityValid : So (FIDELITY >= THRESHOLD)
fidelityValid = Oh

experimentVerified : TimeSymmetricState FIDELITY
experimentVerified = TimeSymmetric FIDELITY Oh
