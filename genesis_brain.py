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

    # ============================================================
    # 📜 SCIENTIFIC NOMENCLATURE GENERATOR
    # ============================================================
    def generate_phenomenon_name(self, vector, flux, context_type="VOID"):
        """
        Generates a "Nobel-Worthy" scientific name for a physical event.
        Based on Vector properties (Dimensions) and Flux magnitude.
        """
        # 1. Analyze Vector Dominance
        # Split 21 dims into 3 sectors: [0-6] Thermodynamic, [7-13] Quantum, [14-20] Exotic
        v_thermo = vector[0, :7].abs().mean().item()
        v_quantum = vector[0, 7:14].abs().mean().item()
        v_exotic = vector[0, 14:].abs().mean().item()
        
        dominant = "Thermodynamic"
        if v_quantum > v_thermo and v_quantum > v_exotic: dominant = "Quantum"
        if v_exotic > v_thermo and v_exotic > v_quantum: dominant = "Exotic"
        
        # 2. Determine Action Verb
        verb = "Fluctuation"
        if abs(flux) > 5.0: verb = "Surge"
        if abs(flux) > 20.0: verb = "Resonance"
        if abs(flux) > 50.0: verb = "Singularity"
        
        # 3. Construct Name
        if context_type == "MOVE":
            return f"Kinetic {dominant} Shift"
        elif context_type == "CONSUME":
            return f"{dominant} Matter Assimilation"
        elif context_type == "CREATE":
            return f"Spontaneous {dominant} Nucleation"
        elif context_type == "DESTROY":
            return f"{dominant} State Collapse"
            
        # Fallback for pure energy flux
        sign = "Exothermic" if flux > 0 else "Endothermic"
        return f"{sign} {dominant} {verb}"

    def resolve_quantum_state(self, agent, reality_vector, emit_strength=0.0):
        """
        The Agent casts a spell (Vector). The Oracle decides what happens.
        """
        # 1. Get Context
        loc = (agent.x, agent.y)
        local_sig = self.get_local_signal(*loc).unsqueeze(0) # [1, 16]
        
        # 🧪 EMIT SCENT (Action)
        if emit_strength > 0.1:
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
        
        outcome_data = {
            "type": "IDLE",
            "name": "Vacuum Fluctuation",
            "flux": energy_flux,
            "details": {}
        }
        
        # --- A. MOVEMENT ---
        if abs(energy_flux) < 2.0: 
            dx = 1 if dx_raw > 0.5 else (-1 if dx_raw < -0.5 else 0)
            dy = 1 if dy_raw > 0.5 else (-1 if dy_raw < -0.5 else 0)
            
            if dx != 0 or dy != 0:
                new_x = (agent.x + dx) % self.size
                new_y = (agent.y + dy) % self.size
                agent.x, agent.y = new_x, new_y
                agent.energy -= 0.1 # Friction
                
                outcome_data["type"] = "MOVE"
                outcome_data["name"] = self.generate_phenomenon_name(reality_vector, energy_flux, "MOVE")
                outcome_data["details"] = {"dx": dx, "dy": dy}
                
        # --- B. ENERGY INTERACTION ---
        else:
            agent.energy += energy_flux
            if energy_flux > 0:
                outcome_data["type"] = "FEED"
                if loc in self.grid:
                    del self.grid[loc]
                    outcome_data["name"] = self.generate_phenomenon_name(reality_vector, energy_flux, "CONSUME")
                    outcome_data["details"] = {"source": "Matter"}
                else:
                    outcome_data["name"] = self.generate_phenomenon_name(reality_vector, energy_flux, "FLUX")
                    outcome_data["details"] = {"source": "Zero Point"}
            else:
                 outcome_data["type"] = "DRAIN"
                 outcome_data["name"] = self.generate_phenomenon_name(reality_vector, energy_flux, "FLUX")
        
        # --- C. ALCHEMY ---
        if abs(transmute) > 2.0:
            if transmute > 0:
                if loc not in self.grid:
                    sig = reality_vector[0, :16].detach()
                    self.grid[loc] = Resource(agent.x, agent.y, True, signal_override=sig)
                    outcome_data["type"] = "CREATE"
                    outcome_data["name"] = self.generate_phenomenon_name(reality_vector, energy_flux, "CREATE")
            else:
                if loc in self.grid:
                    del self.grid[loc]
                    outcome_data["type"] = "DESTROY"
                    outcome_data["name"] = self.generate_phenomenon_name(reality_vector, energy_flux, "DESTROY")
                    
        return energy_flux, outcome_data

    def step(self):
        self.time_step += 1
        self.season_timer += 1
        
        # Phase 13: Biology Update
        self.update_pheromones()
        
        if self.season_timer >= SEASON_LENGTH:
            self.current_season += 1
            self.season_timer = 0
            for _ in range(20): self.spawn_resource()
        
        if self.time_step % 2 == 0:
            for _ in range(5): self.spawn_resource()
