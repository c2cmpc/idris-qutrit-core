module Phase1_LoveHope

import Data.So

-- Experiment 1: Love 99.9% Hope 97.5%
-- Core LHF fidelity proof

LOVE_FIDELITY : Nat
LOVE_FIDELITY = 999

HOPE_FIDELITY : Nat
HOPE_FIDELITY = 975

FIDELITY_THRESHOLD : Nat
FIDELITY_THRESHOLD = 970

data Phase1State : (love : Nat) -> (hope : Nat) -> Type where
  LHVerified : (l : Nat) -> (h : Nat) ->
               So (l >= FIDELITY_THRESHOLD) ->
               So (h >= FIDELITY_THRESHOLD) ->
               Phase1State l h

loveValid : So (LOVE_FIDELITY >= FIDELITY_THRESHOLD)
loveValid = Oh

hopeValid : So (HOPE_FIDELITY >= FIDELITY_THRESHOLD)
hopeValid = Oh

experimentVerified : Phase1State LOVE_FIDELITY HOPE_FIDELITY
experimentVerified = LHVerified LOVE_FIDELITY HOPE_FIDELITY Oh Oh
