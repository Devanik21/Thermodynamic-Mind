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
METABOLIC_COST = 0.1 
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
            self.layers[-1].bias[0] = 0.0 
            self.layers[-1].bias[4] = -0.3 # Harsher drain on interaction
            
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
    def __init__(self, x, y):
        super().__init__(x, y, 'resource')
        # Level 2.8: Trade Emergence (Resource Types)
        # 0: Red (Standard), 1: Green (Rich), 2: Blue (Rare/Catalyst)
        self.type = np.random.choice([0, 1, 2], p=[0.7, 0.2, 0.1])
        
        # Signal Spectrum based on type
        self.signal = torch.zeros(SIGNAL_DIM)
        start_ch = self.type * 4
        self.signal[start_ch:start_ch+4] = torch.rand(4) * 0.8 + 0.2
        self.signal = torch.nn.functional.normalize(self.signal, dim=0)

    def get_nutrition(self, current_season):
        # Summer (Even) favors Red/Green, Winter (Odd) favors Blue
        base = 30.0
        if current_season % 2 == 0:
            if self.type == 0: return base
            if self.type == 1: return base * 2.0
            return -base # Blue is toxic in summer
        else:
            if self.type == 2: return base * 5.0 # Blue is winter-survival fuel
            return -base # Red/Green die in winter
            
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
        
        # 🌐 PHASE 13: "TURING" UPGRADE (16D Pheromone Grid)
        self.pheromone_grid = np.zeros((size, size, SIGNAL_DIM))
        
        # 3.3 Environmental Marking (Stigmergy)
        # Channels: 0:Danger(Red), 1:Resource(Green), 2:Sacred(Blue)
        self.meme_grid = np.zeros((size, size, 3)) 
        
        # 🔗 PHASE 15: "SYMBIOGENESIS" UPGRADE (Elastic Bonds)
        self.bonds = set() # Set of tuples (frozenset of agent IDs)
        
        # 1.4 Scarcity Scaling
        self.scarcity_lambda = 0.01
        self.base_spawn_rate = 5
        
        # 1.10 Entropy Tracking
        self.system_entropy = 0.0
        self.agent_entropy = 0.0
        self.dissipated_energy = 0.0
        self.oracle = PhysicsOracle()
        # Freeze the laws (God does not play dice twice)
        for p in self.oracle.parameters():
            p.requires_grad = False
            
    def spawn_resource(self):
        x, y = random.randint(0, self.size-1), random.randint(0, self.size-1)
        if (x, y) not in self.grid:
            self.grid[(x, y)] = Resource(x, y)

    def get_local_signal(self, x, y):
        if (x, y) in self.grid:
            return self.grid[(x, y)].signal
        return torch.zeros(SIGNAL_DIM)

    def get_pheromone(self, x, y):
        # Read the chemical signal at this location (16D Vector)
        return torch.tensor(self.pheromone_grid[x, y], dtype=torch.float32)

    def get_energy_gradient(self, x, y):
        """1.7 Stress Response: Detect energy flux gradient."""
        # Check neighbors
        gradients = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = (x + dx) % self.size, (y + dy) % self.size
                if (nx, ny) in self.grid:
                    # Positive for food, negative for poison (based on current season)
                    gradients.append(self.grid[(nx, ny)].get_nutrition(self.current_season))
                else:
                    gradients.append(0.0)
        return torch.tensor([np.mean(gradients)], dtype=torch.float32)

    def update_pheromones(self):
        """
        Simulates diffusion and evaporation of 16D chemical signals.
        """
        grid = self.pheromone_grid
        
        # Vectorized diffusion using numpy rolling for all channels
        up = np.roll(grid, 1, axis=0)
        down = np.roll(grid, -1, axis=0)
        left = np.roll(grid, 1, axis=1)
        right = np.roll(grid, -1, axis=1)
        
        diffused = (grid + up + down + left + right) / 5.0
        
        # Evaporation (Decay)
        self.pheromone_grid = diffused * 0.95 

    def metabolic_osmosis(self):
        """
        Level 2.5 Resource Sharing & Level 2.7 Punishment.
        Agents sharing a bond transfer energy to equalize gradients, modulated by Trust.
        """
        active_bonds = list(self.bonds)
        
        for bond in active_bonds:
            id_a, id_b = list(bond)
            if id_a not in self.agents or id_b not in self.agents:
                self.bonds.remove(bond)
                continue
                
            a, b = self.agents[id_a], self.agents[id_b]
            
            # 1. Kinship & Trust
            kinship = 1.0 - np.linalg.norm(a.tag - b.tag)
            kinship = np.clip(kinship, 0, 1)
            
            # Flow High -> Low
            if a.energy > b.energy: donor, receiver = a, b
            else: donor, receiver = b, a
            
            delta = (donor.energy - receiver.energy) * 0.05 # 5% per tick
            efficiency = 0.5 + (0.5 * kinship) # 100% efficient if same tribe
            
            if donor.energy > delta:
                donor.energy -= delta
                receiver.energy += delta * efficiency
                self.dissipated_energy += delta * (1.0 - efficiency)
                
                # Trust Gain
                receiver.social_memory[donor.id] = receiver.social_memory.get(donor.id, 0) + 0.1

    def resolve_quantum_state(self, agent, reality_vector, emit_vector=None, adhesion=0.0, punish=0.0, trade=0.0):
        """
        The Agent casts a spell (Vector). The Oracle decides what happens.
        Includes Level 2 Social Logic.
        """
        # 1. 2.3 Costly Signaling
        if emit_vector is not None:
            # Signaling costs energy proportional to signal complexity (variance)
            signal_cost = float(torch.var(emit_vector).item()) * 2.0
            agent.energy -= signal_cost
            self.pheromone_grid[agent.x, agent.y] += emit_vector.detach().numpy()
            np.clip(self.pheromone_grid[agent.x, agent.y], 0, 1.0, out=self.pheromone_grid[agent.x, agent.y])

        # 2. 2.4 Coalition & 2.5 Resource Sharing: BOND LOGIC
        if adhesion > 0.5:
            for other_id, other in self.agents.items():
                if other_id != agent.id:
                    dist = math.sqrt((agent.x - other.x)**2 + (agent.y - other.y)**2)
                    if dist < 1.5:
                        # Bonding with different tribes is costly (2.4)
                        tag_dist = np.linalg.norm(agent.tag - other.tag)
                        bond_cost = 0.5 + tag_dist * 2.0
                        if agent.energy > bond_cost:
                            agent.energy -= bond_cost
                            self.bonds.add(frozenset([agent.id, other_id]))
        elif adhesion < 0.2:
            to_remove = [b for b in self.bonds if agent.id in b]
            for b in to_remove:
                self.bonds.remove(b)
                agent.energy -= 1.0 

        # 3. 2.7 Punishment
        outcome_log = "✨ IDLE"
        if punish > 0.7:
             # Find a neighbor to punish
             for other_id, other in self.agents.items():
                if other_id != agent.id:
                    dist = math.sqrt((agent.x - other.x)**2 + (agent.y - other.y)**2)
                    if dist < 1.5:
                        cost = 5.0
                        damage = 15.0
                        if agent.energy > cost:
                            agent.energy -= cost
                            other.energy -= damage
                            other.social_memory[agent.id] = other.social_memory.get(agent.id, 0) - 1.0 # Trust loss
                            outcome_log = f"⚔️ PUNISHED {other_id[:4]}"
                            break

        # 4. 2.8 Trade
        if trade > 0.7:
            # Look for trade partners
            for b in self.bonds:
                if agent.id in b:
                    other_id = list(b - {agent.id})[0]
                    if other_id in self.agents:
                        partner = self.agents[other_id]
                        # Swap tokens if they have different types
                        for i in range(3):
                            for j in range(3):
                                if i != j and agent.inventory[i] > 0 and partner.inventory[j] > 0:
                                    agent.inventory[i] -= 1
                                    agent.inventory[j] += 1
                                    partner.inventory[j] -= 1
                                    partner.inventory[i] += 1
                                    agent.social_memory[other_id] = agent.social_memory.get(other_id, 0) + 0.5 # Trust gain
                                    outcome_log = f"🤝 TRADED with {other_id[:4]}"
                                    break

        # 5. Query Oracle
        loc = (agent.x, agent.y)
        local_sig = self.get_local_signal(*loc).unsqueeze(0)
        with torch.no_grad():
            effects = self.oracle(reality_vector, local_sig)[0] 
        
        # 6. Decode Effects
        energy_flux = effects[0].item() * 15.0 
        dx_raw = effects[1].item()
        dy_raw = effects[2].item()
        transmute = effects[3].item()
        
        # --- A. MOVEMENT ---
        if abs(energy_flux) < 2.0: 
            dx = 1 if dx_raw > 0.5 else (-1 if dx_raw < -0.5 else 0)
            dy = 1 if dy_raw > 0.5 else (-1 if dy_raw < -0.5 else 0)
            if dx != 0 or dy != 0:
                agent.x, agent.y = (agent.x + dx) % self.size, (agent.y + dy) % self.size
                agent.energy -= 0.1 
                outcome_log = "MOVE"
                
        # --- B. ENERGY & RECOURSES ---
        else:
            agent.energy += energy_flux
            if energy_flux > 0:
                outcome_log = "⚡ POSITIVE FLUX (+)"
                if loc in self.grid:
                    res = self.grid[loc]
                    # 2.8 Token Collection
                    agent.inventory[res.type] += 1
                    # Synergy Bonus: Complete set (R,G,B) gives +30 Energy
                    if all(count > 0 for count in agent.inventory):
                        agent.energy += 30.0
                        for i in range(3): agent.inventory[i] -= 1
                        outcome_log = "🌟 SYNERGY BONUS!"
                    else:
                        outcome_log = f"😋 CONSUMED {['Red','Green','Blue'][res.type]}"
                    del self.grid[loc]
            else: outcome_log = "🔥 NEGATIVE FLUX (-)"
        
        return energy_flux, outcome_log

    def step(self):
        self.time_step += 1
        self.season_timer += 1
        
        # 1.4 Scarcity: Exponential decay of spawn rate
        current_spawn_prob = np.exp(-self.scarcity_lambda * self.time_step)
        
        # 1.6 Circadian Rhythms: Environment Phase
        self.env_phase = (self.time_step / SEASON_LENGTH) * 2 * np.pi
        
        # Phase 13: Biology Update
        self.update_pheromones()
        
        # Phase 15: Symbiosis Update
        self.metabolic_osmosis()
        self._update_entropy_metrics()
        
        if self.season_timer >= SEASON_LENGTH:
            self.current_season += 1
            self.season_timer = 0
            # 1.4 Scarcity applied to seasonal spawn
            for _ in range(int(20 * current_spawn_prob)): 
                self.spawn_resource()
        
        if self.time_step % 2 == 0:
            for _ in range(5): self.spawn_resource()

    def _update_entropy_metrics(self):
        """1.10 Complete Entropy Defiance: Track system-wide entropy changes."""
        # 1. Agent Weight Entropy (Neural Compression)
        if self.agents:
            weights = []
            for a in self.agents.values():
                weights.append(a.calculate_weight_entropy())
            self.agent_entropy = np.mean(weights)
        
        # 2. Environmental Entropy (Resource Distribution)
        # Using a simple grid occupancy entropy
        occ = np.zeros(self.size * self.size)
        for loc in self.grid:
            idx = loc[0] * self.size + loc[1]
            occ[idx] = 1
        p = (occ.sum() + 1e-8) / len(occ)
        self.system_entropy = -(p * np.log2(p + 1e-8) + (1-p) * np.log2(1-p + 1e-8))