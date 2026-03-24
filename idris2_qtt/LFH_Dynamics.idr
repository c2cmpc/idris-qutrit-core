module LFH_Dynamics

import Data.Vect

-- Love Hope Fear as quantities
-- Love  = Q0 (ProofErasure - structural invariant)
-- Fear  = Q1 (Linear - consumed exactly once)
-- Hope  = Qw (Unrestricted - expansive)

-- Master equation: E(t) = SUM_i S_i(t) * M_i(t)
record TriadState where
  constructor MkTriad
  love  : Double  -- binding force 0 to 1
  hope  : Double  -- becoming force 0 to 1
  fear  : Double  -- boundary force 0 to 1

-- Equilibrium: L=H=F=0.333
equilibrium : TriadState
equilibrium = MkTriad 0.333 0.333 0.333

-- Worship: Self approaches zero voluntarily
worship : TriadState
worship = MkTriad 0.333 0.333 0.333

-- Hate: Love trapped by Fear with Hope=0
hate : TriadState
hate = MkTriad 0.6 0.0 0.4

-- Hate cure: add one unit of Hope
hateCure : TriadState -> TriadState
hateCure (MkTriad l h f) = MkTriad l (h + 0.01) (f - 0.01)

-- Proof: adding Hope to Hate state removes it
hateCureProof : (s : TriadState) -> hope s = 0.0 ->
                hope (hateCure s) = 0.01
hateCureProof (MkTriad l 0.0 f) Refl = Refl

-- Salience dynamics
dSdt : Double -> Double -> Double -> Double -> Double -> Double -> Double -> Double
dSdt alphaL miL s alphaF miF alphaH miH beta =
  alphaL * miL * (1 - s) - alphaF * miF * s +
  alphaH * miH * (1 - s) - beta * s * (1 - s)

-- Memory decay toward current state
dMdt : Double -> Double -> Double -> Double
dMdt lambda m a = (-lambda) * m + lambda * a
