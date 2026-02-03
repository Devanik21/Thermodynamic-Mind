import numpy as np
import torch
import torch.nn as nn
import random
import math

# ============================================================
# 🌌 DYNAMIC PHYSICS CONSTANTS
# ============================================================
GRID_SIZE = 40
SIGNAL_DIM = 16
MAX_ENERGY = 100.0
# "Easy mode" - metabolic cost is low, but stupidity kills
METABOLIC_COST = 0.2 
SEASON_LENGTH = 50 

# ============================================================
# 🔮 THE PHYSICS ORACLE (The Laws of Nature)
# ============================================================
class PhysicsOracle(nn.Module):
    """
    The Black Box of Reality.
    Maps User Will (21D) -> Physical Effect.
    Biased: 61% Positive, 39% Negative.
    """
    def __init__(self):
        super().__init__()
        # Input: 21 (Will) + 16 (Local Matter Signal) = 37 Dimensions
        self.layers = nn.Sequential(
            nn.Linear(37, 64),
            nn.Tanh(), # Non-linear chaotic mixing
            nn.Linear(64, 64),
            nn.SiLU(), # Complex activation
            nn.Linear(64, 5) # Output Effects
        )
        
        # Balanced Initialization for maximum Chaos
        for m in self.layers.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=1.5)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0.0)

        # Bias the "Energy" output (Index 0) SLIGHTLY positive
        # Was 0.5 (Too safe). Now 0.1 (Survival requires finding the peaks)
        with torch.no_grad():
            self.layers[-1].bias[0] = 0.1 
            self.layers[-1].bias[4] = -0.1 # Interaction Flavor bias towards "Drain" (Survival of fittest)
            
    def forward(self, vector_21, matter_signal_16):
        x = torch.cat([vector_21, matter_signal_16], dim=1)
        return self.layers(x)

# ============================================================
# ⚛️ ENTITIES
# ============================================================
class Entity:
    def __init__(self, x, y, entity_type):
        self.x = x
        self.y = y
        self.type = entity_type
        self.exists = True

class Resource(Entity):
    def __init__(self, x, y, is_type_a=True, signal_override=None):
        super().__init__(x, y, 'resource')
        self.is_type_a = is_type_a 
        
        if signal_override is not None:
             self.signal = signal_override
        else:
            self.signal = torch.zeros(SIGNAL_DIM)
            if is_type_a:
                self.signal[:8] = torch.rand(8) * 0.8 + 0.2
                self.signal[8:] = torch.rand(8) * 0.1
            else:
                self.signal[:8] = torch.rand(8) * 0.1
                self.signal[8:] = torch.rand(8) * 0.8 + 0.2
            self.signal = torch.nn.functional.normalize(self.signal, dim=0)

    def get_nutrition(self, current_season):
        # Base value can be modified by the signal itself?
        # For now, keep the season logic but allow signal complexity
        base_val = 20.0
        # If signal is "written" (complex), it might have different properties
        # Simple heuristic: Correlation with Season's "Ideal Vector"
        
        if current_season % 2 == 0:
            return base_val if self.is_type_a else -base_val * 2.0
        else:
            return -base_val * 2.0 if self.is_type_a else base_val
            
# ============================================================
# 🌍 THE QUANTUM WORLD
# ============================================================
class GenesisWorld:
    def __init__(self, size=GRID_SIZE):
        self.size = size
        self.grid = {} 
        self.agents = {} 
        self.time_step = 0
        self.current_season = 0
        self.season_timer = 0
        
        # The Laws of Physics
        self.oracle = PhysicsOracle()
        # Freeze the laws (God does not play dice twice)
        for p in self.oracle.parameters():
            p.requires_grad = False
            
    def spawn_resource(self):
        x, y = random.randint(0, self.size-1), random.randint(0, self.size-1)
        if (x, y) not in self.grid:
            self.grid[(x, y)] = Resource(x, y, random.random() < 0.5)

    def get_local_signal(self, x, y):
        if (x, y) in self.grid:
            return self.grid[(x, y)].signal
        return torch.zeros(SIGNAL_DIM)

    def resolve_quantum_state(self, agent, reality_vector):
        """
        The Agent casts a spell (Vector). The Oracle decides what happens.
        """
        # 1. Get Context
        loc = (agent.x, agent.y)
        local_sig = self.get_local_signal(*loc).unsqueeze(0) # [1, 16]
        
        # 2. Query Oracle
        # reality_vector is [1, 21]
        with torch.no_grad():
            effects = self.oracle(reality_vector, local_sig)[0] # [5]
        
        # 3. Decode Effects
        # [0]: Energy Flux (The "Biased" One)
        # [1]: Delta X
        # [2]: Delta Y
        # [3]: Transmutation Strength
        # [4]: Interaction Flavor (Shield/Damage)
        
        energy_flux = effects[0].item() * 10.0 # Scale up
        dx_raw = effects[1].item()
        dy_raw = effects[2].item()
        transmute = effects[3].item()
        flavor = effects[4].item()
        
        outcome_log = "✨ IDLE"
        
        # --- A. MOVEMENT (If flux is low, we assume it's just movement) ---
        if abs(energy_flux) < 2.0: 
            dx = 1 if dx_raw > 0.5 else (-1 if dx_raw < -0.5 else 0)
            dy = 1 if dy_raw > 0.5 else (-1 if dy_raw < -0.5 else 0)
            
            if dx != 0 or dy != 0:
                new_x = (agent.x + dx) % self.size
                new_y = (agent.y + dy) % self.size
                agent.x, agent.y = new_x, new_y
                agent.energy -= 0.1 # Friction
                outcome_log = "MOVE"
                
        # --- B. ENERGY INTERACTION (Eating / Bleeding) ---
        else:
            # Physical impact on Agent
            agent.energy += energy_flux
            
            # If positive, we might consume the resource
            if energy_flux > 0:
                outcome_log = "⚡ POSITIVE FLUX (+)"
                if loc in self.grid:
                    # Consumed existing matter
                    del self.grid[loc]
                    outcome_log = "😋 CONSUMED MATTER"
            else:
                 outcome_log = "🔥 NEGATIVE FLUX (-)"
        
        # --- C. ALCHEMY (Transmutation / Writing) ---
        # Very rare: needs high activation
        if abs(transmute) > 2.0:
            if transmute > 0:
                # Creation!
                if loc not in self.grid:
                    # WRITING: The Resource Signal is a projection of the Agent's Will
                    # Map 21D -> 16D
                    sig = reality_vector[0, :16].detach()
                    self.grid[loc] = Resource(agent.x, agent.y, True, signal_override=sig)
                    outcome_log = "💠 ALCHEMY: CREATION"
            else:
                # Destruction!
                if loc in self.grid:
                    del self.grid[loc]
                    outcome_log = "⚫ ALCHEMY: VOID"
                    
        return energy_flux, outcome_log

    def step(self):
        self.time_step += 1
        self.season_timer += 1
        
        if self.season_timer >= SEASON_LENGTH:
            self.current_season += 1
            self.season_timer = 0
            for _ in range(20): self.spawn_resource()
        
        if self.time_step % 2 == 0:
            for _ in range(5): self.spawn_resource()
