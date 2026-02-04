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
        
        # 🌐 PHASE 13: "TURING" UPGRADE (Pheromone Grid)
        self.pheromone_grid = np.zeros((size, size))
        
        # 🔗 PHASE 15: "SYMBIOGENESIS" UPGRADE (Elastic Bonds)
        self.bonds = set() # Set of tuples (frozenset of agent IDs)
        
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

    def get_pheromone(self, x, y):
        # Read the chemical signal at this location
        return float(self.pheromone_grid[x, y])

    def update_pheromones(self):
        """
        Simulates diffusion and evaporation of chemical signals.
        Grid = Grid * Decay + Diffusion
        """
        grid = self.pheromone_grid
        
        # Diffusion (Simple average of neighbors)
        # Shift Up, Down, Left, Right
        up = np.roll(grid, 1, axis=0)
        down = np.roll(grid, -1, axis=0)
        left = np.roll(grid, 1, axis=1)
        right = np.roll(grid, -1, axis=1)
        
        diffused = (grid + up + down + left + right) / 5.0
        
        # Evaporation (Decay)
        self.pheromone_grid = diffused * 0.95 

    def metabolic_osmosis(self):
        """
        Energy sharing between bonded agents (Gap Junctions).
        """
        for bond in list(self.bonds):
            id_a, id_b = list(bond)
            if id_a in self.agents and id_b in self.agents:
                a = self.agents[id_a]
                b = self.agents[id_b]
                
                # Osmotic flow (10% equalization per tick)
                diff = a.energy - b.energy
                flow = diff * 0.1
                
                a.energy -= flow
                b.energy += flow
            else:
                self.bonds.remove(bond)

    def resolve_quantum_state(self, agent, reality_vector, emit_strength=0.0, adhesion=0.0):
        """
        The Agent casts a spell (Vector). The Oracle decides what happens.
        """
        # 🔗 SYMBIOGENESIS: BOND LOGIC
        # Scan for neighbors to bond with
        if adhesion > 0.5:
            for other_id, other in self.agents.items():
                if other_id != agent.id:
                    dist = math.sqrt((agent.x - other.x)**2 + (agent.y - other.y)**2)
                    if dist < 1.5:
                        # Multi-cellular bond formation
                        self.bonds.add(frozenset([agent.id, other_id]))
        elif adhesion < 0.2:
            # Break bonds if adhesion is low
            to_remove = [b for b in self.bonds if agent.id in b]
            for b in to_remove:
                self.bonds.remove(b)
                agent.energy -= 2.0 # Tearing pain
        
        # 1. Get Context
        loc = (agent.x, agent.y)
        local_sig = self.get_local_signal(*loc).unsqueeze(0) # [1, 16]
        
        # 🧪 EMIT SCENT (Action)
        # Updates the pheromone grid at agent's location
        if emit_strength > 0.1:
            # Add to grid, capped at 1.0
            self.pheromone_grid[agent.x, agent.y] = min(1.0, self.pheromone_grid[agent.x, agent.y] + emit_strength * 0.5)
        
        # 2. Query Oracle
        with torch.no_grad():
            effects = self.oracle(reality_vector, local_sig)[0] 
        
        # 3. Decode Effects
        energy_flux = effects[0].item() * 10.0 # Scale up
        dx_raw = effects[1].item()
        dy_raw = effects[2].item()
        transmute = effects[3].item()
        flavor = effects[4].item()
        
        outcome_log = "✨ IDLE"
        
        # --- A. MOVEMENT ---
        if abs(energy_flux) < 2.0: 
            dx = 1 if dx_raw > 0.5 else (-1 if dx_raw < -0.5 else 0)
            dy = 1 if dy_raw > 0.5 else (-1 if dy_raw < -0.5 else 0)
            
            if dx != 0 or dy != 0:
                new_x = (agent.x + dx) % self.size
                new_y = (agent.y + dy) % self.size
                agent.x, agent.y = new_x, new_y
                agent.energy -= 0.1 # Friction
                outcome_log = "MOVE"
                
        # --- B. ENERGY INTERACTION ---
        else:
            agent.energy += energy_flux
            if energy_flux > 0:
                outcome_log = "⚡ POSITIVE FLUX (+)"
                if loc in self.grid:
                    del self.grid[loc]
                    outcome_log = "😋 CONSUMED MATTER"
            else:
                 outcome_log = "🔥 NEGATIVE FLUX (-)"
        
        # --- C. ALCHEMY ---
        if abs(transmute) > 2.0:
            if transmute > 0:
                if loc not in self.grid:
                    sig = reality_vector[0, :16].detach()
                    self.grid[loc] = Resource(agent.x, agent.y, True, signal_override=sig)
                    outcome_log = "💠 ALCHEMY: CREATION"
            else:
                if loc in self.grid:
                    del self.grid[loc]
                    outcome_log = "⚫ ALCHEMY: VOID"
                    
        return energy_flux, outcome_log

    def step(self):
        self.time_step += 1
        self.season_timer += 1
        
        # Phase 13: Biology Update
        self.update_pheromones()
        
        # Phase 15: Symbiosis Update
        self.metabolic_osmosis()
        
        if self.season_timer >= SEASON_LENGTH:
            self.current_season += 1
            self.season_timer = 0
            for _ in range(20): self.spawn_resource()
        
        if self.time_step % 2 == 0:
            for _ in range(5): self.spawn_resource()
