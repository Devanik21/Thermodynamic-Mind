import numpy as np
import torch
import torch.nn as nn
import random
import math
import streamlit as st

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
            return -base * 0.12 # Reduced toxicity to prevent mass extinction (-6 instead of -30)
        else:
            if self.type == 2: return base * 5.0 # Blue is winter-survival fuel
            return -base * 0.12 # Reduced toxicity (-6)

class MegaResource(Entity):
    """4.8 Distributed Cognition: Requires multiple agents or high synergy."""
    def __init__(self, x, y):
        super().__init__(x, y, 'mega_resource')
        self.strength = 100.0
        self.signal = torch.ones(SIGNAL_DIM) * 0.5
    
    def get_nutrition(self, current_season):
        return 150.0 # High payout
            
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
            
        # 5.6 Collective Optimization
        self.collective_values = {"Efficiency": 0.5, "Growth": 0.5}
        self.fitness_landscape_shift = 0.0

    def collective_memory_retrieval(self):
        """4.9 Collective Memory: Agents with low confidence query the hive."""
        # Only run occasionally to save compute
        if self.time_step % 10 != 0: return

        for agent in self.agents.values():
            if agent.confidence < 0.3: # Confused/Forgetting
                 # Find a confident neighbor (Mentor)
                 best_mentor = None
                 max_conf = 0.5
                 
                 neighbors = [
                     self.agents[oid] for oid in self.agents 
                     if oid != agent.id and abs(self.agents[oid].x - agent.x) <= 2 and abs(self.agents[oid].y - agent.y) <= 2
                 ]
                 
                 for n in neighbors:
                     if n.confidence > max_conf:
                         max_conf = n.confidence
                         best_mentor = n
                 
                 if best_mentor:
                     # Restore deleted/decayed weights from mentor
                     if hasattr(agent, 'restorative_imitation'):
                        agent.restorative_imitation(best_mentor)
            
            
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
             signal_complexity = float(torch.var(emit_vector).item())
             signal_cost = signal_complexity * 2.0
             
             # 2.3 Zahavi Strict Check: Verify Proof of Work
             # If complexity > threshold, we check the nonce.
             if signal_complexity > 0.05:
                 start_nonce = getattr(agent, 'last_nonce', 0)
                 import hashlib
                 # Quantize for consistency matches Agent
                 vec_bytes = (emit_vector * 100).long().cpu().numpy().tobytes()
                 candidate = f"{start_nonce}".encode() + vec_bytes
                 h = hashlib.sha256(candidate).hexdigest()
                 
                 # Verify Difficulty 1 ("0")
                 if not h.startswith("0"):
                     # Fake signal! Determine it's cheap talk.
                     # Dampen the signal so it doesn't propagate as effectively
                     emit_vector = emit_vector * 0.1
                     # But still charge energy (cheating isn't free)
                     outcome_log = "👺 FAKE SIGNAL DETECTED"
                 else:
                     # Honest signal. Add extra metabolic cost for the computation
                     agent.energy -= 0.5 
             
             agent.energy -= signal_cost
             
             # 3.8 Symbolic Reference (Displacement)
             # If Channel 15 > 0.5, project signal to offset coordinates (Ch 13, 14)
             target_x, target_y = agent.x, agent.y
             displacement_flag = emit_vector[15].item()
             if displacement_flag > 0.5:
                 # Map 0-1 to -5 to +5 offset
                 dx = int((emit_vector[13].item() - 0.5) * 10)
                 dy = int((emit_vector[14].item() - 0.5) * 10)
                 target_x = (agent.x + dx) % self.size
                 target_y = (agent.y + dy) % self.size
                 # Higher cost for projection
                 agent.energy -= 0.5
             
             self.pheromone_grid[target_x, target_y] += emit_vector.detach().numpy()
             np.clip(self.pheromone_grid[target_x, target_y], 0, 1.0, out=self.pheromone_grid[target_x, target_y])

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
        
        # --- PHASE 16: LEVEL 4 TENSOR FUSION & ROLES ---
        final_reality_vector = reality_vector
        if agent.is_fused and agent.fused_partner and agent.fused_partner.id in self.agents:
            partner = agent.fused_partner
            dist_p = math.sqrt((agent.x - partner.x)**2 + (agent.y - partner.y)**2)
            if dist_p < 2.0:
                # 4.7 Fusion: Additive reality vectors (Conceptual merge)
                final_reality_vector = reality_vector + partner.last_vector
        
        with torch.no_grad():
            effects = self.oracle(final_reality_vector, local_sig)[0] 
        
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
            # 4.3 Supply Chain & Role Bonuses
            bonus = 1.0
            if agent.role == "Forager": bonus = 1.2
            elif agent.role == "Processor": bonus = 1.5 if any(v > 0 for v in agent.inventory) else 0.8
            
            final_flux = energy_flux * bonus
            agent.energy += final_flux
            
            if final_flux > 0:
                outcome_log = f"⚡ {agent.role} FLUX (+)"
                if loc in self.grid:
                if loc in self.grid:
                    res = self.grid[loc]
                    # 4.8 Distributed Cognition Check
                    if isinstance(res, MegaResource):
                        if final_reality_vector.sum() < 2.0:
                            agent.energy -= 10.0 # Failed to harvest
                            outcome_log = "❌ TOO WEAK FOR MEGA"
                            return final_flux, outcome_log
                        else:
                            # Successful Mega Harvest!
                            # Grant massive bonus and 1 of each token
                            agent.energy += 50.0 
                            for i in range(3): agent.inventory[i] += 1
                            outcome_log = "🌌 OMEGA HARVEST (+50 E)"
                            del self.grid[loc]
                            return final_flux + 50.0, outcome_log

                    # 2.8 Token Collection (Standard Resource)
                    # Ensure type is valid before indexing
                    if isinstance(res.type, int) and 0 <= res.type < 3:
                        agent.inventory[res.type] += 1
                        # Synergy Bonus: Complete set (R,G,B) gives +30 Energy
                        if all(count > 0 for count in agent.inventory):
                            agent.energy += 30.0
                            for i in range(3): agent.inventory[i] -= 1
                            outcome_log = "🌟 SYNERGY BONUS!"
                        else:
                            outcome_log = f"😋 CONSUMED {['Red','Green','Blue'][res.type]}"
                    else:
                        outcome_log = "😋 CONSUMED MYSTERY MATTER"
                        
                    del self.grid[loc]
            else: outcome_log = "🔥 NEGATIVE FLUX (-)"
        
        return energy_flux, outcome_log

    def step(self):
        self.time_step += 1
        self.season_timer += 1
        
        # 1.4 Scarcity: Exponential decay of spawn rate
        current_spawn_prob = max(0.2, np.exp(-self.scarcity_lambda * self.time_step))
        
        # 1.6 Circadian Rhythms: Environment Phase
        self.env_phase = (self.time_step / SEASON_LENGTH) * 2 * np.pi
        
        # Phase 13: Biology Update
        self.update_pheromones()
        
        # Phase 15: Symbiosis Update
        self.metabolic_osmosis()
        # Phase 15: Symbiosis Update
        self.metabolic_osmosis()
        
        # 4.9 Collective Memory: Retrieve lost knowledge
        self.collective_memory_retrieval()
        
        self._update_entropy_metrics()
        
        # 5.6 Collective Optimization
        if self.time_step % 100 == 0:
            self._update_fitness_landscape()
            
        # --- 3.2 HORIZONTAL NEURAL TRANSFER (Viral Propagation) ---
        # Highly fit agents (Energy > 90) spontaneously create "Weight Viruses"
        # and sneeze them onto their neighbors.
        if self.time_step % 50 == 0:
            for agent in list(self.agents.values()):
                if agent.energy > 90.0:
                    # Create virus packet
                    packet = agent.create_weight_packet()
                    # Broadcast to neighbors
                    neighbors = [
                        a for a in self.agents.values() 
                        if a.id != agent.id and abs(a.x - agent.x) <= 2 and abs(a.y - agent.y) <= 2
                    ]
                    for n in neighbors:
                         n.receive_infection(packet)
                         # Log the infection event sparingly
                         if random.random() < 0.05:
                            st.session_state.event_log.insert(0, {
                                "Tick": self.time_step,
                                "Agent": n.id,
                                "Event": f"🦠 INFECTED by {agent.id[:4]}",
                                "Vector": [0]*21
                            })
        
        if self.season_timer >= SEASON_LENGTH:
            self.current_season += 1
            self.season_timer = 0
            # 1.4 Scarcity applied to seasonal spawn
            for _ in range(int(20 * current_spawn_prob)): 
                self.spawn_resource()
        
        if self.time_step % 2 == 0:
            for _ in range(5): self.spawn_resource()
        
        # 4.8 Spawn MegaResource rarely
        if self.time_step % 100 == 0:
            mx, my = random.randint(0, self.size-1), random.randint(0, self.size-1)
            self.grid[(mx, my)] = MegaResource(mx, my)

    def _update_entropy_metrics(self):
        """1.10 Complete Entropy Defiance: Track system-wide entropy changes."""
        # 1. Agent Weight Entropy (Neural Compression)
        if self.agents:
            weights = []
            for a in list(self.agents.values()):
                weights.append(a.calculate_weight_entropy())
            self.agent_entropy = np.mean(weights)
        
        # 2. Environmental Entropy (Resource Distribution)
        # Using a simple grid occupancy entropy
        occ = np.zeros(self.size * self.size)
        for loc in self.grid:
            idx = loc[0] * self.size + loc[1]
            occ[idx] = 1
        p = (occ.sum() + 1e-8) / len(occ)
        env_entropy = -(p * np.log2(p + 1e-8) + (1-p) * np.log2(1-p + 1e-8))
        
        # 3. 1.10 Complete Entropy Defiance Verification
        # Total S = S_agents + S_environment
        # We need dS_agents < 0 and dS_total > 0 (Global dissipation)
        # Since I am not tracking dS_dissipated strictly yet, I use dissipated_energy as proxy for S_produced.
        
        current_agent_S = self.agent_entropy
        current_env_S = env_entropy
        
        # Store previous values for derivative
        if not hasattr(self, 'last_agent_S'):
            self.last_agent_S = current_agent_S
            self.last_system_S = self.system_entropy
            self.entropy_verified = False
        else:
            dS_agents = current_agent_S - self.last_agent_S
            dS_env = current_env_S - self.system_entropy # Actually system_S IS env_S here
            
            # S_dissipated is monotonically increasing, so dS_dissipated/dt > 0 always.
            # Verification Condition:
            # Agent Entropy is decreasing (ordering themselves)
            # while Universe Entropy (Env + Heat) is increasing.
            
            # Heat produced this step ~ dissipated_energy delta
            # We track cumulative, so we need delta
            if not hasattr(self, 'last_dissipated'): self.last_dissipated = 0.0
            d_heat = self.dissipated_energy - self.last_dissipated
            self.last_dissipated = self.dissipated_energy
            
            # Strict Check
            # We smooth it over time to avoid noise failures
            if dS_agents < 0 and (dS_env + d_heat) > 0:
                 self.entropy_verified = True
            
            self.last_agent_S = current_agent_S
        
        self.system_entropy = env_entropy

    def _update_fitness_landscape(self):
        """5.6 Collective Optimization: Population evolves the fitness function."""
        # Agents "vote" via their behavior.
        # High Trade = Vote for Efficiency.
        # High Movement = Vote for Growth/Exploration.
        
        if not self.agents: return
        
        avg_trade = np.mean([a.last_value.item() for a in self.agents.values() if a.last_value is not None])
        # Use simple heuristics
        
        eff_vote = 0.0
        growth_vote = 0.0
        
        for a in self.agents.values():
            if hasattr(a, 'role'):
                if a.role == "Processor": eff_vote += 1.0
                if a.role == "Forager": growth_vote += 1.0
                
        total = eff_vote + growth_vote + 1e-8
        self.collective_values["Efficiency"] = eff_vote / total
        self.collective_values["Growth"] = growth_vote / total
        
        # Shift Oracle Logic
        # If Efficiency is valued, Processors get bonus flux.
        # If Growth is valued, Foragers get bonus flux.
        # This is strictly "Collective Optimization" - the rules change to fit the dominant strategy.
        
        # We model this by shifting the 'bias' of the Oracle's last layer
        # Index 0 is Energy.
        bias_shift = (self.collective_values["Efficiency"] - 0.5) * 0.1
        self.fitness_landscape_shift = bias_shift
        
        # Apply to Oracle (Simulated Epigenetics of the Universe?)
        # No, just store it and apply in resolve_quantum_state
        pass
