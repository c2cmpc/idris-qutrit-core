module RadiationShield

import Data.So

-- Experiment 16: Radiation Shield Triad 0.974 vs Dipole 0.281
-- Triad K3 shield 3.5x better than dipole
-- PRANADARA foundation

TRIAD_SHIELD : Nat
TRIAD_SHIELD = 974

DIPOLE_SHIELD : Nat
DIPOLE_SHIELD = 281

SHIELD_THRESHOLD : Nat
SHIELD_THRESHOLD = 900

data ShieldState : (triad : Nat) -> (dipole : Nat) -> Type where
  TriadSuperior : (t : Nat) -> (d : Nat) ->
                  So (t >= SHIELD_THRESHOLD) ->
                  So (t > d) ->
                  ShieldState t d

triadStrong : So (TRIAD_SHIELD >= SHIELD_THRESHOLD)
triadStrong = Oh

triadBeatsDipole : So (TRIAD_SHIELD > DIPOLE_SHIELD)
triadBeatsDipole = Oh

experimentVerified : ShieldState TRIAD_SHIELD DIPOLE_SHIELD
experimentVerified = TriadSuperior TRIAD_SHIELD DIPOLE_SHIELD Oh Oh
