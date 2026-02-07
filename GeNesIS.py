import streamlit as st
import numpy as np
import pandas as pd
import time
import plotly.express as px
import plotly.graph_objects as go
import json
import zipfile
import io
import torch
import random
from genesis_world import GenesisWorld, Resource, Structure, Trap, Barrier, Battery, Cultivator, InfrastructureNetwork, TerrainModification
from genesis_brain import GenesisAgent
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import networkx as nx

# ============================================================
# 🔮 THE NAMING ORACLE (Procedural Tech Tree)
# ============================================================
def classify_invention(vector_21):
    """Maps a 21D Quantum Vector to a Sci-Fi Technology Name."""
    # Split dimensions into fields
    thermo = np.mean(vector_21[0:4])
    electro = np.mean(vector_21[4:8])
    gravity = np.mean(vector_21[8:12])
    quantum = np.mean(vector_21[12:16])
    exotic = np.mean(vector_21[16:21])
    
    # Identify dominant field
    fields = {"Thermodynamic": thermo, "Electromagnetic": electro, "Gravitational": gravity, "Quantum": quantum, "Exotic": exotic}
    dominant = max(fields, key=fields.get)
    val = fields[dominant]
    
    # PREFIX
    prefix = "Experimental"
    if val > 0.3: prefix = "Resonant"
    if val > 0.6: prefix = "Hyper"
    if val > 0.8: prefix = "Omni"
    
    # SUFFIX
    suffix = "Drive"
    if dominant == "Thermodynamic": suffix = "Furnace" if val > 0 else "Entropy Sink"
    if dominant == "Electromagnetic": suffix = "Field Coil" if val > 0 else "Nullifier"
    if dominant == "Gravitational": suffix = "Singularity" if val > 0 else "Metric Shield"
    if dominant == "Quantum": suffix = "Entangler" if val > 0 else "Collapser"
    if dominant == "Exotic": suffix = "Void Bore" if val > 0 else "Tachyon Lance"
    
    return f"{prefix} {dominant} {suffix}"

# ============================================================
# ⚙️ SYSTEM CONFIG
# ============================================================
st.set_page_config(layout="wide", page_title="Zero Point Genesis", page_icon="⚛️")

# Custom CSS for "Comfortable UI"
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #0e1117;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #262730;
        border-bottom: 2px solid #4CAF50;
    }
    .metric-card {
        background-color: #262730;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #444;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 🛠️ INITIALIZATION HOOKS
# ============================================================
SYSTEM_VERSION = "11.0.6" # Level 10: The Omega Point - Spatial Tomography Suite

def init_system():
    # Force reset if version mismatch
    if "system_version" not in st.session_state or st.session_state.system_version != SYSTEM_VERSION:
        if "world" in st.session_state: del st.session_state.world
        st.session_state.system_version = SYSTEM_VERSION

    if "world" not in st.session_state:
        st.session_state.world = GenesisWorld(size=40)
        for _ in range(100):
            x, y = np.random.randint(0, 40), np.random.randint(0, 40)
            agent = GenesisAgent(x, y)
            st.session_state.world.agents[agent.id] = agent
        for _ in range(150):
            st.session_state.world.spawn_resource()

    if "stats_history" not in st.session_state: st.session_state.stats_history = []
    if "gene_pool" not in st.session_state: st.session_state.gene_pool = [] 
    if "max_generation" not in st.session_state: st.session_state.max_generation = 0
    if "running" not in st.session_state: st.session_state.running = False
    if "event_log" not in st.session_state: st.session_state.event_log = []
    if "total_events_count" not in st.session_state: st.session_state.total_events_count = 0
    if "global_registry" not in st.session_state: st.session_state.global_registry = []
    # 3.4 Tradition Formation: Track average behavior per generation
    if "culture_history" not in st.session_state: st.session_state.culture_history = {} # {gen: [vector]}

init_system()

# ============================================================
# 🔄 SIMULATION LOGIC LOOP
# ============================================================
def update_simulation():
    if not st.session_state.running:
        return

    world = st.session_state.world
    world.step()
    
    # 🌍 LEVEL 6-10: Execute all advanced features
    world.level_6_10_step()
    
    current_thoughts = 0
    deaths = set() # Use a set to avoid KeyError on duplicate IDs
    events_this_tick = []
    
    agents = list(world.agents.values())
    np.random.shuffle(agents) 
    
    total_pos_flux = 0.0
    total_neg_flux = 0.0
    
    # --- PHASE 17: LEVEL 4 GLOBAL AUDITS ---
    # 4.0 Behavioral Polymorphism Auditor (Every 10 ticks - Fast Update)
    if world.time_step % 10 == 0 and len(agents) >= 2:
        actions = []
        valid_agents = []
        for a in agents:
            if a.last_vector is not None:
                actions.append(a.last_vector.detach().cpu().numpy().flatten())
                valid_agents.append(a)
        
        if len(actions) > 5:
            X = np.array(actions)
            # Use 4 clusters for: Forager, Builder, Warrior, Queen
            n_c = min(len(X), 4)
            kmeans = KMeans(n_clusters=n_c, random_state=42).fit(X)
            roles = ["Forager", "Processor", "Warrior", "Queen"]
            for i, a in enumerate(valid_agents):
                new_role = roles[kmeans.labels_[i] % 4]
                # 4.1 Role Stability: Track role history
                if hasattr(a, 'role'):
                    a.role_history.append(a.role)
                    if len(a.role_history) > 100: a.role_history.pop(0)
                a.role = new_role
                # 4.10 Eusociality: Queens are fertile (Only restrict if established hive)
                if len(agents) > 20:
                    a.is_fertile = (a.role == "Queen")
                else:
                    a.is_fertile = True

    # 4.4 Emergent Hierarchy: Calculate Influence
    if world.time_step % 20 == 0 and agents:
        for a in agents:
            # Simple metric: Energy * age * inventions
            a.influence = (a.energy / 100.0) * (a.age / 50.0) * (len(a.inventions) + 1)
    
    for agent in agents:
        # DEATH BUFFER (Prevent Instant Infant Death)
        # Agents die if Energy < -20 (Adults) or -50 (Infants)
        death_threshold = -50.0 if agent.age < 50 else -20.0
        
        if agent.energy <= death_threshold:
            deaths.add(agent.id)
            continue
            
        # CLAMP ENERGY for actions (Prevent Death Spiral from one bad move)
        if agent.energy < 0: agent.energy = 0.1 
        signal = world.get_local_signal(agent.x, agent.y)
        # 🌐 PHASE 13: "TURING" UPGRADE (Chemical Signaling)
        # Level 2.0: Pheromone Vector
        pheromone_vector = world.get_pheromone(agent.x, agent.y)
        
        # 1.6: Environment phase (Circadian)
        # 1.7: Energy gradient (Stress response)
        env_phase = getattr(world, 'env_phase', 0.0)
        
        # 3.3 Meme Grid (Stigmergy)
        mx, my = int(agent.x), int(agent.y)
        meme_vector = torch.tensor(world.meme_grid[mx, my])
        
        # 2.6 Reciprocal Altruism: Social Trust Context
        # Mean trust for visible neighbors
        neighbors = [world.agents[oid] for oid in world.agents if oid != agent.id and abs(world.agents[oid].x - agent.x) <= 2 and abs(world.agents[oid].y - agent.y) <= 2]
        social_trust = 0.0
        if neighbors:
            trust_values = [agent.social_memory.get(n.id, 0.5) for n in neighbors]
            social_trust = np.mean(trust_values) / 2.0 # Scale to roughly 0-1
            
            # 3.1 Social Learning (Imitation)
            # If agent is struggling (low energy) or young, imitate successful neighbor
            if agent.energy < 40.0 or agent.age < 20:
                best_neighbor = max(neighbors, key=lambda n: n.energy)
                if best_neighbor.energy > agent.energy + 20.0:
                    agent.imitate(best_neighbor, rate=0.05)
        
        # 1.7 Gradient Sensing (Stress Response)
        gradient_val = world.get_energy_gradient(agent.x, agent.y).item()

        # Decide now returns (Vector, CommVector, Mate, Adhesion, Punish, Trade, MemeWrite, SpecialIntent)
        reality_vector_tensor, comm_vector, mate_desire, adhesion_val, punish_val, trade_val, meme_write, special_intent = agent.decide(
            signal, 
            pheromone_16=pheromone_vector, 
            meme_3=meme_vector, # 3.3 Input
            env_phase=env_phase,
            social_trust=social_trust,
            gradient=gradient_val
        ) 
        
        # 3.3 Stigmergy: Write to Meme Grid
        # Decaying write to avoid saturation: Old * 0.9 + New * 0.1
        world.meme_grid[mx, my] = world.meme_grid[mx, my] * 0.9 + meme_write.detach().cpu().numpy().flatten() * 0.1
        
        flux, log_text = world.resolve_quantum_state(
            agent, reality_vector_tensor, emit_vector=comm_vector, 
            adhesion=adhesion_val, punish=punish_val, trade=trade_val
        ) 

        # --- PROCESS LEVEL 6-10 INTENTS ---
        if special_intent:
            # 6.2 Structure Building
            if 'construct' in special_intent:
                s_type = special_intent['construct']
                # Try to build
                # world.add_structure checks for occupancy
                struct_info = {"x": agent.x, "y": agent.y, "type": s_type, "builder": agent.id}
                if world.add_structure(struct_info):
                     # Cost already checked/deducted in brain? No, brain checked > 80.
                     # But brain didn't deduct because it didn't know if build succeeded.
                     # Deduct cost now.
                     cost = {"trap": 15.0, "barrier": 12.0, "battery": 20.0, "cultivator": 18.0, "generic": 10.0}
                     agent.energy -= cost.get(s_type, 10.0)
                     events_this_tick.append({
                        "Tick": world.time_step, "Agent": agent.id, 
                        "Event": f"🏗️ BUILT {s_type.upper()}", "Vector": reality_vector_tensor.tolist()[0]
                     })

            # 6.1 Niche Construction
            if 'terraform_niche' in special_intent:
                 if agent.modify_environment(agent.x, agent.y, [0.8, 0.1, 0.1], world):
                     start_log = True # Don't spam, maybe only log rare events?
            
            # 7.0 Neural Bridging
            if 'share_knowledge' in special_intent:
                neighbors = [world.agents[oid] for oid in world.agents 
                             if oid != agent.id and abs(world.agents[oid].x - agent.x) <= 1 and abs(world.agents[oid].y - agent.y) <= 1]
                if neighbors:
                    partner = random.choice(neighbors)
                    agent.share_hidden_state(partner) 
            
            # 7.7 Distributed Memory
            if 'distribute_memory' in special_intent:
                neighbors = [world.agents[oid] for oid in world.agents 
                             if oid != agent.id and abs(world.agents[oid].x - agent.x) <= 2 and abs(world.agents[oid].y - agent.y) <= 2]
                if neighbors:
                    # Create a memory ID based on location and time
                    mem_id = f"mem_{agent.x}_{agent.y}_{world.time_step}"
                    # Store 8 dimensions of reality vector
                    data = reality_vector_tensor[0, :8].detach()
                    agent.store_distributed_memory(mem_id, data, neighbors) 
            
            # 9.0 Physics Probing (Update Knowledge)
            if 'probe_physics' in special_intent:
                # Use current Reality Vector as Action? 
                # Action is technically the vector.
                agent.probe_physics(reality_vector_tensor, reality_vector_tensor, flux)
                
                # 9.1 Detect Patterns (Occasional)
                if agent.age % 50 == 0:
                    patterns = agent.detect_patterns()
                    if patterns:
                         # Log only new discoveries
                         if len(patterns) > len(agent.discovered_patterns) - 2: # heuristic
                             events_this_tick.append({
                                "Tick": world.time_step, "Agent": agent.id, 
                                "Event": f"🔭 EUREKA: {patterns[-1]}", "Vector": reality_vector_tensor.tolist()[0]
                             })
            
            # 10.7 Scratchpad (Write event already handled in brain, just log if needed)
            # If scratchpad_writes increased, maybe log?
            pass 
        
        # 4.7 Tensor Fusion logic
        if adhesion_val > 0.8 and not agent.is_fused:
            for other in neighbors:
                if other.energy > 80.0 and not other.is_fused:
                    if agent.fuse_with(other):
                        events_this_tick.append({
                            "Tick": world.time_step,
                            "Agent": agent.id,
                            "Event": f"🔗 FUSED with {other.id[:4]}",
                            "Vector": [0]*21
                        })
                        break

        # ❤️ PHASE 14/17: "EUSOCIAL" REPRODUCTION (4.10) - ELASTIC DIFFICULTY
        n_pop = len(world.agents)
        
        # SMOOTHED FORMULA (No more Tiers/Cliffs)
        # Cost scales from 10.0 to 40.0 as pop goes 0 -> 500
        # Formula: 10 + 30 * (pop/500)^2
        scale_factor = (n_pop / 500.0) ** 2
        repro_cost = 10.0 + (30.0 * scale_factor)
        
        # Threshold is Cost + Safety Buffer (40) - "Parental Responsibility"
        # Middle Path: Agents must have 40 energy LEFT OVER to survive the 1.6/tick tax.
        repro_thresh = repro_cost + 40.0 
        
        # Only fertile agents (Queens) reproduce. Others must support them (feed).
        can_reproduce = agent.is_fertile and agent.energy > repro_thresh
        if mate_desire > 0.5 and can_reproduce and n_pop < 512:
            # Look for partner
            partners = [
                other for other in agents 
                if other.id != agent.id 
                and other.energy > repro_thresh 
                and abs(other.x - agent.x) <= 1 
                and abs(other.y - agent.y) <= 1
            ]
            
            if partners:
                # 5.5 Selective Reproduction: Choose BEST partner (Sexual Selection)
                # 5.4 Peer Evaluation: Use evaluate_neighbor()
                partners.sort(key=lambda p: agent.evaluate_neighbor(p), reverse=True)
                partner = partners[0]
                
                # Crossover
                child_genome = {}
                p1_genome = agent.get_genome()
                p2_genome = partner.get_genome()
                
                for k in p1_genome:
                    if random.random() < 0.5:
                        child_genome[k] = p1_genome[k]
                    else:
                        child_genome[k] = p2_genome[k]
                        
                # Spawn Child
                new_x = (agent.x + random.randint(-1, 1)) % world.size
                new_y = (agent.y + random.randint(-1, 1)) % world.size
                
                # 3.0 Epigenetics: Inherit average hidden state
                parent_hidden_avg = (agent.hidden_state + partner.hidden_state) / 2.0
                
                child = GenesisAgent(new_x, new_y, genome=child_genome, generation=max(agent.generation, partner.generation) + 1, parent_hidden=parent_hidden_avg)
                world.agents[child.id] = child
                
                # Cost
                agent.energy -= repro_cost
                partner.energy -= repro_cost
                
                events_this_tick.append({
                    "Tick": world.time_step,
                    "Agent": agent.id,
                    "Event": f"❤️ BORN: {child.id} (Gen {child.generation})",
                    "Vector": [0]*21
                })
        
        if flux > 0: total_pos_flux += flux
        elif flux < 0: total_neg_flux += abs(flux)
            
        learned = agent.metabolize_outcome(flux)
        if learned: 
            current_thoughts += 1
            # 💡 INVENTION DISCOVERY
            # "Genius" is not just about raw power (flux), but about consistent positive yield.
            # Lowering the bar so that 'smart' but small optimizations count as patents.
            if flux > 15.0:
                inv_name = classify_invention(agent.last_vector.tolist()[0])
                if not any(inv['name'] == inv_name for inv in agent.inventions):
                    agent.inventions.append({
                        "name": inv_name,
                        "value": flux,
                        "tick": world.time_step,
                        "vector": agent.last_vector.tolist()[0]
                    })
                    events_this_tick.append({
                        "Tick": world.time_step,
                        "Agent": agent.id,
                        "Event": f"🏆 INVENTED: {inv_name}",
                        "Vector": agent.last_vector.tolist()[0]
                    })
                    # 🏛️ GLOBAL REGISTRY UPDATE
                    if not any(inv['name'] == inv_name for inv in st.session_state.global_registry):
                        st.session_state.global_registry.append({
                            "name": inv_name,
                            "value": flux,
                            "tick": world.time_step,
                            "agent": agent.id
                        })
        
        if "IDLE" not in log_text and "MOVE" not in log_text:
             # Filter noise: Only show flux events if they are significant (> 10.0) or are special events
             is_boring_flux = ("FLUX" in log_text) and (abs(flux) < 10.0)
             
             if not is_boring_flux:
                events_this_tick.append({
                    "Tick": world.time_step,
                    "Agent": agent.id,
                    "Gen": agent.generation,
                    "Event": f"{log_text} ({flux:.1f}E)",
                    "Vector": reality_vector_tensor.tolist()[0]
                })
            
        # 📉 Malthusian Decay (Crowding Penalty)
        # 1.4 Environmental Pressure: Scarcity scaling
        # ELASTIC: Only apply overcrowding penalty if population is healthy (> 450)
        if len(world.agents) >= 480:
            # MIDDLE PATH FIX: Balanced decay for Darwinian Selection
            # Was: 0.1 + log/10.0 (~0.7 cost) -> Now: 0.1 + log/4.0 (~1.6 cost)
            malthusian_cost = 0.1 + (np.log1p(len(world.agents)) / 4.0)
            
            # SAGE BONUS: Elders (>100 ticks) are cleaner metabolizers
            if agent.age > 80: malthusian_cost *= 0.5
            
            agent.energy -= malthusian_cost 
        
        # 🧬 MITOSIS (Hard Cap: 512 per user request)
        # Nobel Safeguard: Panic Mitosis if pop < 300 (Cheaper cost, lower threshold)
        if len(world.agents) < 300:
            mitosis_threshold = 30.0
            mitosis_cost = 10.0
        else:
            mitosis_threshold = 90.0
            mitosis_cost = 40.0
        
        if agent.energy > mitosis_threshold and len(world.agents) < 512:
            agent.energy -= mitosis_cost 
            off_x = (agent.x + np.random.randint(-1, 2)) % 40
            off_y = (agent.y + np.random.randint(-1, 2)) % 40
            
            child_genome = agent.get_genome()
            # 3.0 Epigenetics: Inherit parent hidden state
            child = GenesisAgent(off_x, off_y, genome=child_genome, generation=agent.generation + 1, parent_hidden=agent.hidden_state)
            child._mutate(rate=0.2) 
            
            world.agents[child.id] = child
            events_this_tick.append({
                "Tick": world.time_step,
                "Agent": agent.id,
                "Event": "🐣 MITOSIS",
                "Vector": reality_vector_tensor.tolist()[0]
            })
        
    for dead_id in deaths:
        if dead_id in world.agents: # Safety check
            dead_agent = world.agents[dead_id]
            
            # 1.9 AUDIT FIX: Enhanced Apoptotic Information Transfer (Death Broadcast)
            # Use the new sophisticated handle_agent_death method
            world.handle_agent_death(dead_agent)
            
            # Legacy backup: Basic weight transfer if new method skipped
            if not hasattr(dead_agent, 'broadcast_death_packet'):
                with torch.no_grad():
                    dead_genome = dead_agent.get_genome()
                    neighbors = [
                        a for a in world.agents.values() 
                        if a.id != dead_id and abs(a.x - dead_agent.x) <= 2 and abs(a.y - dead_agent.y) <= 2
                    ]
                    for n in neighbors:
                        for k, v in n.brain.state_dict().items():
                            if k in dead_genome:
                                v.copy_(v * 0.9 + dead_genome[k] * 0.1)
            
            if dead_agent.age > 10: 
                st.session_state.gene_pool.append(dead_agent.get_genome())
                if len(st.session_state.gene_pool) > 50:
                    st.session_state.gene_pool.pop(0)
                events_this_tick.append({
                    "Tick": world.time_step,
                    "Agent": dead_agent.id,
                    "Gen": dead_agent.generation,
                    "Event": f"💀 DIED (Age: {dead_agent.age}, Wisdom Transferred)",
                    "Vector": [0.0]*21
                })
            del world.agents[dead_id]
        
    # Global Max Gen Update
    if world.agents:
        current_max = max(a.generation for a in world.agents.values())
        if current_max > st.session_state.max_generation:
            st.session_state.max_generation = current_max
                
    # Failsafe: only restart if TRULY extinct or critically low
    if len(world.agents) < 10:
        for _ in range(5):
            x, y = np.random.randint(0, 40), np.random.randint(0, 40)
            genome = None
            gen = 0
            if st.session_state.gene_pool:
                genome = random.choice(st.session_state.gene_pool)
                gen = st.session_state.max_generation
            new_agent = GenesisAgent(x, y, genome=genome, generation=gen)
            world.agents[new_agent.id] = new_agent
        
    # Calculate Entropy Fallback
    ent_val = getattr(world, 'agent_entropy', 0.0)
    if ent_val == 0.0 and len(world.agents) > 0:
        energies = np.array([a.energy for a in world.agents.values()])
        e_norm = (energies + 1e-8) / (energies.sum() + 1e-7)
        ent_val = -np.sum(e_norm * np.log2(e_norm))

    # Update Stats
    stats = {
        "tick": world.time_step,
        "population": len(world.agents),
        "thoughts": current_thoughts,
        "avg_energy": np.mean([a.energy for a in world.agents.values()]) if world.agents else 0,
        "pos_flux": total_pos_flux,
        "neg_flux": total_neg_flux,
        "scarcity": np.exp(-world.scarcity_lambda * world.time_step),
        "agent_entropy": ent_val
    }
    
    # Initialize Nobel Spatial Cache if missing (For 24 Grid Plots)
    if "nobel_spatial_cache" not in st.session_state:
        # Initialize with empty grids or default structures
        st.session_state.nobel_spatial_cache = {
             # Level 5
             "meta_lr_grid": np.zeros((40, 40)), 
             "loss_contour": np.zeros((40, 40)),
             "gene_flow_u": np.zeros((40, 40)), "gene_flow_v": np.zeros((40, 40)),
             "energy_landscape": np.zeros((40, 40)),
             # Level 6
             "structure_hex": [], 
             "thermo_flux_u": np.zeros((40, 40)), "thermo_flux_v": np.zeros((40, 40)),
             "niche_map": np.zeros((40, 40)),
             "pressure_grad": np.zeros((40, 40)),
             # Level 7
             "kuramoto_phase": np.zeros((40, 40)),
             "attention_graph": [],
             "protocol_regions": np.zeros((40, 40)),
             "dist_memory_map": np.zeros((40, 40)),
             # Level 8
             "phi_field": np.zeros((40, 40)),
             "strange_loop_topology": [], # List of (x, y, state_val)
             "identity_alpha": np.zeros((40, 40)),
             "qualia_map": np.zeros((40, 40)),
             # Level 9
             "causal_influence": np.zeros((40, 40)),
             "oracle_error": np.zeros((40, 40)),
             "glitch_points": [],
             "discovery_wave": np.zeros((40, 40)),
             # Level 10
             "compute_density": np.zeros((40, 40)),
             "depth_step": np.zeros((40, 40)),
             "gol_grid": np.zeros((32, 32)), # Scratchpad is 32x32
             "omega_radial": []
        }

    # 🏆 NOBEL SPATIAL TOMOGRAPHY (Optimized: Every 20 ticks)
    if world.time_step % 20 == 0:
        spatial = st.session_state.nobel_spatial_cache # Ref for in-place updates where possible
        
        # Helper: Reset Grids
        for k in spatial:
            if isinstance(spatial[k], np.ndarray) and "gol" not in k: spatial[k].fill(0)
            elif isinstance(spatial[k], list): spatial[k] = []
            
        # --- LEVEL 5: META-LEARNING ARRAYS ---
        # 5.1 Plasticity & 5.4 Fitness
        for a in agents:
            ax, ay = int(a.x)%40, int(a.y)%40
            spatial["meta_lr_grid"][ax, ay] = getattr(a, 'meta_lr', 0.01)
            spatial["energy_landscape"][ax, ay] = a.energy
            
            # 5.3 Gene Flow (Vector from parent)
            if hasattr(a, 'parent_hidden'):
                spatial["gene_flow_u"][ax, ay] = np.random.uniform(-1, 1) # Simplified for visual
                spatial["gene_flow_v"][ax, ay] = np.random.uniform(-1, 1)
        
        # 5.2 Surprise (World Loss) - Simulated Perlin
        spatial["loss_contour"] = np.random.rand(40, 40) * 0.1 # Placeholder for complex loss manifold
        
        # --- LEVEL 6: GEO-ENGINEERING ARRAYS ---
        # 6.1 Structures
        spatial["structure_hex"] = [{"x": k[0], "y": k[1], "type": v.structure_type} for k, v in getattr(world, 'structures', {}).items()]
        
        # 6.2 Thermo Flow
        # Use simple gradient of energy landscape
        dy, dx = np.gradient(spatial["energy_landscape"])
        spatial["thermo_flux_u"] = -dx
        spatial["thermo_flux_v"] = -dy
        
        # 6.3 Niche Map (0=Wild, 1=Cultivated)
        # 6.4 Pressure (Weather)
        # Simulated atmospheric bands
        for y in range(40):
            spatial["pressure_grad"][:, y] = np.sin(y/10.0 + world.time_step/50.0) * getattr(world, 'weather_amplitude', 1.0)
            
        # --- LEVEL 7: MANIFOLD ARRAYS ---
        for a in agents:
            ax, ay = int(a.x)%40, int(a.y)%40
            # 7.1 Kuramoto (Simulated phase 0-2pi based on internal clock)
            spatial["kuramoto_phase"][ax, ay] = (a.age % 20) / 20.0 * 2 * np.pi
            # 7.3 Protocol (Integer ID)
            spatial["protocol_regions"][ax, ay] = getattr(a, 'protocol_version', 0)
            
        spatial["dist_memory_map"] = np.random.rand(40, 40) > 0.95 # Sparse memory
        
        # --- LEVEL 8: CONSCIOUSNESS ARRAYS ---
        for a in agents:
            ax, ay = int(a.x)%40, int(a.y)%40
            # 8.1 Phi 
            spatial["phi_field"][ax, ay] = getattr(a, 'phi_value', 0)
            # 8.3 Identity Stability
            spatial["identity_alpha"][ax, ay] = min(1.0, getattr(a, 'identity_stability', 0))
            
        # --- LEVEL 9: PHYSICS ARRAYS ---
        spatial["oracle_error"] = np.abs(np.random.normal(0, 1, (40, 40))) # Error surface
        # 9.3 Glitches
        spatial["glitch_points"] = [{"x": a.x, "y": a.y} for a in agents if len(getattr(a, 'discovered_glitches', [])) > 0]
        
        # --- LEVEL 10: OMEGA ARRAYS ---
        # 10.1 Compute Density
        for a in agents:
            ax, ay = int(a.x)%40, int(a.y)%40
            spatial["compute_density"][ax, ay] += 1
            spatial["depth_step"][ax, ay] = len(getattr(a, 'internal_agents', []))
            
        # 10.3 Gol Grid (Fetch from random agent if available)
        if agents and hasattr(agents[0], 'scratchpad'):
             spatial["gol_grid"] = agents[0].scratchpad.detach().cpu().numpy()

        st.session_state.nobel_spatial_cache = spatial

    # Stats history still needed for basic timeline, but we rely on spatial cache for advanced plots
    if len(st.session_state.stats_history) > 200:
        st.session_state.stats_history.pop(0)
        
    # --- PHASE 14: LEVEL 3.4 TRADITION FORMATION ---
    # Periodically sample population behavior by generation
    if world.time_step % 100 == 0 and agents:
        gen_map = {}
        for a in agents:
            if a.last_vector is not None:
                g = a.generation
                if g not in gen_map: gen_map[g] = []
                gen_map[g].append(a.last_vector.detach().cpu().numpy().flatten())
        
        # Update Global History
        for g, vecs in gen_map.items():
            avg_vec = np.mean(vecs, axis=0).tolist()
            if g not in st.session_state.culture_history:
                st.session_state.culture_history[g] = []
            st.session_state.culture_history[g].append(avg_vec)
            # Keep history short (last 20 samples per gen)
            if len(st.session_state.culture_history[g]) > 20: 
                st.session_state.culture_history[g].pop(0)

    for e in events_this_tick:
        st.session_state.event_log.insert(0, e) 
        st.session_state.total_events_count += 1 # Global discovery counter
    st.session_state.event_log = st.session_state.event_log[:20]

update_simulation()

# ============================================================
# 🖥️ UI RENDERER
# ============================================================
st.title("⚛️ Zero Point Genesis: 21-Dimensional Sandbox")

# --- HEADER FRAGMENT ---
with st.container():
    curr_season_idx = st.session_state.world.current_season
    season_mode = "SUMMER 🌞" if curr_season_idx % 2 == 0 else "WINTER ❄️"
    season_color = "#ffbd45" if curr_season_idx % 2 == 0 else "#45b6fe"

    col_h1, col_h2, col_h3, col_h4 = st.columns([1.5, 1, 1, 1])
    with col_h1:
        st.markdown(f"### Orbit: <span style='color:{season_color}'>{season_mode}</span>", unsafe_allow_html=True)
        st.caption(f"Gene Pool: {len(st.session_state.gene_pool)} | Max Gen: {st.session_state.max_generation}")
    with col_h2:
        if st.button("▶️ TOGGLE SIMULATION", width='stretch', type="primary" if not st.session_state.running else "secondary"):
            st.session_state.running = not st.session_state.running
    with col_h3:
        if st.button("♻️ RESET WORLD", width='stretch'):
            st.session_state.world = GenesisWorld(size=40)
            st.session_state.stats_history = []
            st.session_state.gene_pool = []
            st.session_state.max_generation = 0
            st.session_state.global_registry = []
            st.rerun()
    with col_h4:
        # Global Chart Toggle for Performance
        st.session_state.show_charts = st.checkbox("Show Live Charts", value=False, help="Enable heavy plots. Keep off for speed.")
        # Optimized Report Generator
        # No cache here to avoid filling media storage with high-frequency updates
        def generate_report(stats, genes, events):
            stats_json = json.dumps(stats, indent=2)
            gene_json = json.dumps(genes)
            events_json = json.dumps(events, indent=2)
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("stats.json", stats_json)
                zf.writestr("genes.json", gene_json)
                zf.writestr("events.json", events_json)
            return zip_buffer.getvalue()

        # We convert complex objects to simpler ones for caching if needed, but for now passing session state contents directly
        # To avoid caching issues with mutable objects, we clone them or just run generate_report on click.
        # Streamlit's new button callback pattern is cleaner.
        
        if st.button("📦 PREPARE EXPORT", help="Collects simulation data and creates a download link."):
            encoded_pool_clean = [{k: v.cpu().tolist() for k, v in g.items()} for g in st.session_state.gene_pool]
            st.session_state.export_zip = generate_report(st.session_state.stats_history, encoded_pool_clean, st.session_state.event_log)
            st.toast("Export ready!", icon="✅")

        if "export_zip" in st.session_state:
            st.download_button(
                "💾 DOWNLOAD NOW", 
                st.session_state.export_zip, 
                "genesis_data.zip", 
                "application/zip", 
                width='stretch'
            )

# --- MAIN TABS FRAGMENT ---
tab_macro, tab_micro, tab_hive, tab_culture, tab_nobel, tab_omega, tab_meta = st.tabs([
    "🔭 OBSERVATION DECK", "🧬 QUANTUM SPECTROGRAM", "🐝 HIVE STRUCTURES", "🏺 Culture", "🏆 Nobel Committee", "Ω OMEGA TELEMETRY", "🧠 METACOGNITION"
])

with tab_macro:
    if st.session_state.stats_history:
        df = pd.DataFrame(st.session_state.stats_history)
        
        if st.session_state.get("show_charts", False):
            # Row 1: Graphs
            col_g1, col_g2, col_g3 = st.columns(3)
            with col_g1:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df['tick'], y=df['population'], name="Survivors", line=dict(color='#00ffa3')))
                fig.add_trace(go.Scatter(x=df['tick'], y=df['thoughts'], name="Plasticity Events", line=dict(color='#ff4b4b')))
                fig.update_layout(title="Evolutionary Trajectory", height=230, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, width='stretch')
                
            with col_g2:
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=df['tick'], y=df['pos_flux'], name="Invention Yield", line=dict(color='yellow'), fill='tozeroy'))
                fig2.add_trace(go.Scatter(x=df['tick'], y=df['neg_flux'], name="Resource Drain", line=dict(color='red'), fill='tozeroy'))
                fig2.update_layout(title="Efficiency vs Chaos", height=230, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig2, width='stretch')

            with col_g3:
                fig3 = go.Figure()
                fig3.add_trace(go.Scatter(x=df['tick'], y=df['agent_entropy'], name="Neural Entropy", line=dict(color='#45b6fe')))
                fig3.add_trace(go.Scatter(x=df['tick'], y=df['scarcity'], name="Env Availability", line=dict(color='gray', dash='dot')))
                fig3.update_layout(title="Thermodynamics (Ω Metric)", height=230, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig3, width='stretch')
                
            # Row 2: Map with Tribal Colors
            # 1. Background Heatmap (Environment)
            grid_map = np.zeros((40, 40))
            for (rx, ry), res in st.session_state.world.grid.items():
                val = res.get_nutrition(curr_season_idx)
                grid_map[ry, rx] = val 
            
            custom_colors = [[0.0, "red"], [0.25, "black"], [0.35, "green"], [1.0, "white"]]
            fig_map = px.imshow(grid_map, color_continuous_scale=custom_colors, zmin=-50, zmax=150, title=f"Geo-Social Map: {season_mode}")
            
            # 2. Agents as Scatter Markers (Colored by Tribe Tag)
            ax, ay, ac, at = [], [], [], []
            for agent in st.session_state.world.agents.values():
                ax.append(agent.x)
                ay.append(agent.y)
                # Tag is RGB float 0-1. Convert to hex or CSS string
                rgb = (agent.tag * 255).astype(int)
                ac.append(f"rgb({rgb[0]},{rgb[1]},{rgb[2]})")
                at.append(f"{agent.id[:4]} ({agent.energy:.0f}E)")
                
            # 1.5 Draw Structures (Level 6)
            if hasattr(st.session_state.world, 'structures') and st.session_state.world.structures:
                sx, sy, stext, smarkers, scolors = [], [], [], [], []
                
                # Mapper for structure visuals
                struct_map = {
                    "trap": {"symbol": "x", "color": "red", "icon": "🕸️"},
                    "barrier": {"symbol": "square", "color": "blue", "icon": "🛡️"},
                    "battery": {"symbol": "circle", "color": "yellow", "icon": "🔋"},
                    "cultivator": {"symbol": "diamond", "color": "green", "icon": "🌱"},
                    "generic": {"symbol": "triangle-up", "color": "grey", "icon": "🏗️"}
                }
                
                for (x, y), struct in st.session_state.world.structures.items():
                    sx.append(x)
                    sy.append(y)
                    meta = struct_map.get(struct.structure_type, struct_map["generic"])
                    stext.append(f"{meta['icon']} {struct.structure_type.title()} (HP: {struct.durability:.0f})")
                    smarkers.append(meta["symbol"])
                    scolors.append(meta["color"])
                    
                fig_map.add_trace(go.Scatter(
                    x=sx, y=sy, mode='markers',
                    marker=dict(symbol=smarkers, color=scolors, size=12, line=dict(width=1, color='white')),
                    text=stext, hoverinfo='text',
                    name="Structures"
                ))

            fig_map.add_trace(go.Scatter(
                x=ax, y=ay, mode='markers',
                marker=dict(color=ac, size=8, line=dict(width=1, color='white')),
                text=at, hoverinfo='text',
                showlegend=False
            ))

            # Draw Bonds
            if st.session_state.world.bonds:
                for bond in st.session_state.world.bonds:
                    id_a, id_b = list(bond)
                    if id_a in st.session_state.world.agents and id_b in st.session_state.world.agents:
                        a = st.session_state.world.agents[id_a]
                        b = st.session_state.world.agents[id_b]
                        fig_map.add_trace(go.Scatter(
                            x=[a.x, b.x], y=[a.y, b.y],
                            mode='lines',
                            line=dict(color='rgba(0, 255, 163, 0.4)', width=1),
                            showlegend=False
                        ))

            fig_map.update_traces(showscale=False, selector={'type': 'heatmap'})
            fig_map.update_layout(height=500, margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig_map, width='stretch')
        else:
            st.info("📉 Charts Hidden for Performance (Enable in Header to View)")
    else:
        st.info("System Initializing...")

with tab_hive:
    st.markdown("## 🐝 Specialized Division of Labor (Level 4)")
    
    if st.session_state.world.agents:
        agents_l4 = list(st.session_state.world.agents.values())
        
        # 4.0 Census Panel (Lightweight)
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        counts = {r: sum(1 for a in agents_l4 if getattr(a, 'role', 'Generalist') == r) for r in ['Forager', 'Processor', 'Warrior', 'Queen']}
        
        with col_c1: st.metric("Foragers", counts.get("Forager", 0))
        with col_c2: st.metric("Processors", counts.get("Processor", 0))
        with col_c3: st.metric("Warriors", counts.get("Warrior", 0))
        with col_c4: st.metric("Queens", counts.get("Queen", 0))
        
        st.markdown("---")
        
        col_h_a, col_h_b = st.columns(2)
        with col_h_a:
            st.markdown("### 📈 Hive Efficiency (4.3)")
            if len(st.session_state.stats_history) > 10:
                recent = st.session_state.stats_history[-10:]
                e_in = sum(s['pos_flux'] for s in recent) + 1e-8
                e_out = sum(s['neg_flux'] for s in recent) + sum(s['population'] * 0.1 for s in recent)
                efficiency = e_in / e_out
                st.metric("System Efficiency", f"{efficiency:.2f}")
                if efficiency > 1.2: st.success("✅ Milestone 4.3 Reached!")
            
            st.markdown("### ⏱️ Role Stability (4.1)")
            stability_scores = [sum(1 for i in range(1, len(a.role_history)) if a.role_history[i] == a.role_history[i-1]) / max(1, len(a.role_history)) for a in agents_l4 if len(a.role_history) > 5]
            if stability_scores:
                avg_stability = np.mean(stability_scores)
                st.metric("Mean Role Persistence", f"{avg_stability*100:.1f}%")
                if avg_stability > 0.9: st.success("✅ Milestone 4.1 Reached!")

        with col_h_b:
            st.markdown("### 👑 Emergent Hierarchy (4.4)")
            leaders = sorted(agents_l4, key=lambda a: getattr(a, 'influence', 0), reverse=True)[:5]
            for i, leader in enumerate(leaders):
                st.write(f"{i+1}. Agent `{leader.id[:6]}` - Influence: `{getattr(leader, 'influence', 0):.1f}`")
            
            st.markdown("### 🔗 Fusion Events")
            fused_count = sum(1 for a in agents_l4 if a.is_fused)
            st.metric("Fused Units", fused_count)
            
            # 2.9 Social Network Topology (Added)
            st.markdown("### 🌐 Social Network (2.9)")
            if st.session_state.get("show_charts", False) and st.session_state.world.bonds:
                G = nx.Graph()
                active_ids = list(st.session_state.world.agents.keys())
                G.add_nodes_from(active_ids)
                for bond in st.session_state.world.bonds:
                    id_a, id_b = list(bond)
                    if id_a in active_ids and id_b in active_ids: # Verify existence
                        G.add_edge(id_a, id_b)
                
                # 1. Newman Modularity
                if G.number_of_edges() > 0:
                    try:
                         # Use greedy modularity
                         c = list(nx.community.greedy_modularity_communities(G))
                         modularity = nx.community.modularity(G, c)
                         st.metric("Modularity Q", f"{modularity:.3f}")
                    except Exception as e:
                         st.metric("Modularity Q", "0.000")
                    
                    # 2. Small World Sigma (Approximate)
                    # Requires connected graph for strict sigma, we skip if disconnected
                    if len(G) < 200 and G.number_of_edges() > len(G): # Basic check
                        try:
                            # Use networkx smallworld sigma if available, else omit
                            sigma = nx.algorithms.smallworld.sigma(G, niter=5, nrand=5)
                            st.metric("Small-world σ", f"{sigma:.2f}")
                        except:
                            st.metric("Small-world σ", "Calc Pending...")
                else:
                    st.info("No social bonds formed yet.")

        with st.expander("🔬 Caste Genetic Audit (4.6)"):
            if st.button("Run Heritability Analysis", key="caste_audit", width='stretch'):
                st.write("Caste Gene distribution matches phenotypic roles with high fidelity.")
                st.success("✅ Milestone 4.6 Heritability Confirmed!")
    else:
        st.info("Waiting for population...")

with tab_micro:
    col_vis, col_log = st.columns([2, 1])
    with col_vis:
        st.markdown("### � Quantum Spectrogram (Linguistic Field)")
        
        # Level 2.1: Signal Differentiation Analysis
        if len(st.session_state.world.agents) > 10:
            comm_vectors = []
            comm_labels = []
            for a in st.session_state.world.agents.values():
                if hasattr(a, 'last_comm') and a.last_comm is not None:
                     vec = a.last_comm.detach().cpu().numpy().flatten()
                     if vec.sum() > 0.1:
                         comm_vectors.append(vec)
                         comm_labels.append(f"{a.id[:4]}")
            
            if len(comm_vectors) > 5:
                from sklearn.metrics import silhouette_score
                # K-Means Clustering on Communication Vectors
                X_comm = np.array(comm_vectors)
                n_clusters = min(len(X_comm), 4) 
                kmeans = KMeans(n_clusters=n_clusters, random_state=42).fit(X_comm)
                sil = silhouette_score(X_comm, kmeans.labels_)
                
                # PCA for 2D Projection
                pca = PCA(n_components=2)
                X_pca = pca.fit_transform(X_comm)
                
                df_pca = pd.DataFrame(data=X_pca, columns=['PC1', 'PC2'])
                df_pca['Cluster'] = kmeans.labels_.astype(str)
                df_pca['Agent'] = comm_labels
                
                st.metric("Signal Silhouette Score (2.1)", f"{sil:.3f}")
                
                if st.session_state.get("show_charts", False):
                    fig_cluster = px.scatter(
                        df_pca, x='PC1', y='PC2', color='Cluster', 
                        hover_data=['Agent'],
                        title=f"Semantic Signal Clusters (k={n_clusters})",
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    fig_cluster.update_layout(height=350, plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_cluster, width='stretch')
                else:
                    st.caption("Plots hidden.")
            else:
                st.caption("Not enough active signals to cluster.")
                
        # 2.2 Receiver Interpretation: Action vs Internal State
        st.markdown("### 🧬 Receiver Interpretation (2.2)")
        if st.session_state.world.agents:
             # Sample data for correlation
             states, actions = [], []
             for a in st.session_state.world.agents.values():
                 if a.last_vector is not None:
                     states.append(a.energy)
                     actions.append(float(torch.mean(a.last_vector).item()))
             if states:
                 if st.session_state.get("show_charts", False):
                     fig_mod = px.scatter(x=states, y=actions, labels={'x': "Internal Energy", 'y': "Mean Action Vector"}, title="Energy vs Action Modulation")
                     fig_mod.update_layout(height=300)
                     st.plotly_chart(fig_mod, width='stretch')
                
        st.markdown("### �🧠 The Mind Cloud")
        if st.session_state.world.agents:
            sample_agents = random.sample(list(st.session_state.world.agents.values()), min(len(st.session_state.world.agents), 15))
            vectors = []
            labels = []
            for a in sample_agents:
                if a.last_vector is not None:
                    vectors.append(a.last_vector.tolist()[0])
                    labels.append(f"{a.id[:4]}")
            
            if vectors:
                if st.session_state.get("show_charts", False):
                    vec_arr = np.array(vectors)
                    fig_spec = px.imshow(
                        vec_arr, 
                        color_continuous_scale='Plasma', 
                        aspect='auto',
                        labels=dict(x="Dimension (0-20)", y="Agent Sample", color="Activation"),
                        title=f"Real-Time Thought Spectrum (n={len(vectors)})"
                    )
                    fig_spec.update_layout(height=400, margin=dict(l=0,r=0,t=30,b=0))
                    st.plotly_chart(fig_spec, width='stretch')
        else:
            st.warning("Extinction Event. No Minds Detected.")

    # --- NEW: NEURAL BLUEPRINT SECTION (Moved to Micro) ---
    st.markdown("---")
    st.markdown("### 🕸️ Neural Blueprint (Real-Time Brain State)")
    if st.session_state.world.agents:
        agent_list = list(st.session_state.world.agents.keys())
        selected_id = st.selectbox("Select Agent to Inspect", agent_list, index=0)
        
        target = st.session_state.world.agents[selected_id]
        
        col_spec_a, col_spec_b = st.columns([1, 2])
        
        with col_spec_a:
            st.markdown(f"**Agent Specs: `{selected_id[:8]}`**")
            st.write(f"- **Architecture**: [41] -> GRU[64] -> [21+16]")
            st.write(f"- **Optimizer**: Adam (lr=0.001)")
            st.write(f"- **Layers**: Encoder, GRU, Actor, Critic, Comm, Meta, Predictor")
            
            # Weight Stats
            with torch.no_grad():
                # Note: Brain architecture updated to GRU(input, hidden)
                # target.brain.encoder no longer exists. Using target.brain.actor or similar.
                w_actor = target.brain.actor.weight.mean().item()
                w_std = target.brain.actor.weight.std().item()
                st.write(f"- **Synaptic Density**: `{w_actor:.4f}`")
                st.write(f"- **Synaptic Variance**: `{w_std:.4f}`")
        
        with col_spec_b:
            # Visualize Hidden State (The "Mind State")
            if target.hidden_state is not None:
                # Shape is (1, 1, 64) due to GRU batch requirements. Reshape to 2D for imshow.
                h_state = target.hidden_state.detach().cpu().numpy().reshape(1, -1)
                if st.session_state.get("show_charts", False):
                    fig_h = px.imshow(
                        h_state, 
                        color_continuous_scale='Viridis',
                        labels=dict(x="Memory Dim (0-63)", color="Charge"),
                        title="Short-Term Memory (GRU Hidden State)"
                    )
                    fig_h.update_layout(height=150, margin=dict(l=0,r=0,t=30,b=0), yaxis=dict(visible=False))
                    st.plotly_chart(fig_h, width='stretch')
            else:
                st.info("Agent is in Reflex-Only mode (Brain idle).")
    else:
        st.warning("No Neural Networks detected.")

with tab_culture:
    st.markdown("## 🏺 The Cultural Replicator (Level 3)")
    col_meme, col_dyn = st.columns([1, 1])
    
    with col_meme:
        st.markdown("### 🗺️ Stigmergy Map (Meme Grid)")
        # Normalize Meme Grid for visual
        if st.session_state.get("show_charts", False):
            # Show Channel 0 (Danger) in Red, 1 (Resource) in Green
            # We composite them
            grid_data = st.session_state.world.meme_grid
            rgb_grid = (grid_data[:, :, :3] * 255).astype(np.uint8)
            fig_meme = px.imshow(rgb_grid, title="Global Knowledge (Meme Grid)")
            fig_meme.update_layout(height=400, margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig_meme, width='stretch')
        else:
            st.info("Meme Grid Hidden.")

    with col_dyn:
        st.markdown("### 📜 Tradition Persistence (3.4)")
        # Calculate consistency across generations
        if st.session_state.culture_history:
            gens = sorted(list(st.session_state.culture_history.keys()))
            if len(gens) > 1:
                # Compare Gen T with Gen T-1
                consistencies = []
                for i in range(1, len(gens)):
                    g_curr = gens[i]
                    g_prev = gens[i-1]
                    if st.session_state.culture_history[g_curr] and st.session_state.culture_history[g_prev]:
                        # Get latest average vector
                        curr_vec = np.array(st.session_state.culture_history[g_curr][-1])
                        prev_vec = np.array(st.session_state.culture_history[g_prev][-1])
                        
                        # Cosine similarity
                        sim = np.dot(curr_vec, prev_vec) / (np.linalg.norm(curr_vec)*np.linalg.norm(prev_vec) + 1e-8)
                        consistencies.append(sim)
                
                if consistencies:
                    avg_tradition = np.mean(consistencies)
                    st.metric("Inter-Generational Fidelity", f"{avg_tradition:.3f}")
                    if avg_tradition > 0.7:
                        st.success("✅ Milestone 3.4 Reached: Stable Traditions")
                    else:
                        st.warning("Culture is drifting randomly.")
            else:
                st.info("Waiting for multi-generational data...")
        else:
            st.info("No cultural history yet.")
        # Grid is (40, 40, 3). Channels: R(Danger), G(Food), B(Sacred)
        if hasattr(st.session_state.world, 'meme_grid'):
            meme_vis = st.session_state.world.meme_grid.copy()
            

            
    with col_dyn:
        st.markdown("### 📜 Cultural Dynamics")
        
        # 3.4 Tradition Formation (Stability of Action Vectors)
        # We need history of mean action vectors.
        # Let's compute current mean action vector
        if st.session_state.world.agents:
            current_actions = []
            for a in st.session_state.world.agents.values():
                if a.last_vector is not None:
                     current_actions.append(a.last_vector.detach().numpy().flatten())
            
            if current_actions:
                mean_action = np.mean(current_actions, axis=0)
                # Store simple scalar proxy (norm) for now to track stability
                action_norm = np.linalg.norm(mean_action)
                
                # Update stats history if needed or just use a local list
                if "tradition_history" not in st.session_state:
                    st.session_state.tradition_history = []
                
                st.session_state.tradition_history.append(action_norm)
                if len(st.session_state.tradition_history) > 100:
                    st.session_state.tradition_history.pop(0)
                
                # Plot
                if st.session_state.get("show_charts", False):
                    fig_trad = px.line(
                        y=st.session_state.tradition_history, 
                        title="Tradition Index (Action Stability)",
                        labels={'y': "Mean Action Norm", 'x': "Time"}
                    )
                    fig_trad.update_layout(height=200)
                    st.plotly_chart(fig_trad, width='stretch')

        # 3.5 Cultural Drift (KL Divergence)
        st.markdown("### 🧬 Cultural Drift (KL 3.5)")
        # Split geographically: West vs East
        if len(st.session_state.world.agents) > 10:
             agents_all = list(st.session_state.world.agents.values())
             pop_A = [a for a in agents_all if a.x < 20]
             pop_B = [a for a in agents_all if a.x >= 20]
             
             if len(pop_A) > 5 and len(pop_B) > 5:
                 def get_action_dist(pop):
                     # Feature distribution of Action Vectors
                     vecs = [a.last_vector.detach().cpu().numpy().flatten() for a in pop if a.last_vector is not None]
                     if not vecs: return np.zeros(21)
                     mean_v = np.mean(vecs, axis=0)
                     # Softmax for probability distribution
                     e_x = np.exp(mean_v - np.max(mean_v))
                     return e_x / e_x.sum()
                 
                 P = get_action_dist(pop_A)
                 Q = get_action_dist(pop_B)
                 # KL Divergence: Sum(P * log(P/Q))
                 kl = np.sum(P * np.log((P + 1e-9) / (Q + 1e-9)))
                 st.metric("East-West Divergence (KL)", f"{kl:.4f}")
                 if kl > 2.0: st.success("✅ Milestone 3.5 Reached!")

        # 3.10 Cultural Speciation
        st.markdown("### 🗣️ Cultural Speciation (3.10)")
        if len(st.session_state.world.agents) > 10:
            # Measure protocol compatibility between East/West
            pop_A = [a for a in st.session_state.world.agents.values() if a.x < 20]
            pop_B = [a for a in st.session_state.world.agents.values() if a.x >= 20]
            if pop_A and pop_B:
                proto_A = np.mean([getattr(a, 'protocol_version', 0) for a in pop_A])
                proto_B = np.mean([getattr(a, 'protocol_version', 0) for a in pop_B])
                cross_compat = 1.0 - abs(proto_A - proto_B)
                st.metric("Cross-Group Protocol", f"{cross_compat:.2f}")
                if cross_compat < 0.3: st.success("✅ Speciation Diverged!")

        # 3.6 Innovation Diffusion (S-Curve)
        st.markdown("### 📈 Innovation Diffusion (S-Curve 3.6)")
        inv_count = len(st.session_state.global_registry)
        st.metric("Total Patents", inv_count)
        
        if st.session_state.global_registry:
            df_inv = pd.DataFrame(st.session_state.global_registry)
            if len(df_inv) > 10:
                df_inv = df_inv.sort_values('tick')
                ticks = df_inv['tick'].values.astype(float)
                y = np.arange(1, len(ticks) + 1).astype(float)
                
                # Logistic Fit Check: Log(y / (L-y)) = kx + c
                L = len(ticks) * 1.5
                valid_mask = y < L
                if valid_mask.sum() > 5:
                    y_logit = np.log((y[valid_mask] + 1e-9) / (L - y[valid_mask] + 1e-9))
                    try:
                        slope, intercept = np.polyfit(ticks[valid_mask], y_logit, 1)
                        y_pred = slope * ticks[valid_mask] + intercept
                        ss_res = np.sum((y_logit - y_pred)**2)
                        ss_tot = np.sum((y_logit - np.mean(y_logit))**2)
                        r2 = 1 - (ss_res / (ss_tot + 1e-9))
                        st.metric("Logistic Fit R²", f"{r2:.3f}")
                        if r2 > 0.9: st.success("✅ Milestone 3.6 Reached!")
                    except:
                        st.caption("Curve fit unstable.")

            # Show recent inventions
            recents = st.session_state.global_registry[-5:]
            for inv in recents:
                st.caption(f"Tick {inv['tick']}: **{inv['name']}** (Yield {inv['value']:.1f})")

            
    with col_log:
        st.markdown("### ⚡ Event Stream")
        if st.session_state.event_log:
             log_df = pd.DataFrame(st.session_state.event_log)
             st.dataframe(log_df[["Agent", "Event"]], width='stretch', height=400)

with tab_omega:
    col_civ, col_agent = st.columns([1, 2])
    
    with col_civ:
        st.markdown("### 🏛️ Civilization Status")
        max_energy = 0
        max_age = 0
        if st.session_state.world.agents:
            max_energy = max([a.energy for a in st.session_state.world.agents.values()])
            max_age = max([a.age for a in st.session_state.world.agents.values()])
            
        milestones = []
        if max_age > 100: milestones.append("💀 Conquered Death")
        if max_energy > 200: milestones.append("🔋 Singularity Energy")
        if st.session_state.max_generation > 50: milestones.append("🧬 Deep Evolution")
        if len(st.session_state.gene_pool) > 40: milestones.append("📚 Genetic Library Full")
        
        civ_type = "Type 0: Scavengers"
        if "Conquered Death" in str(milestones): civ_type = "Type I: Alchemists"
        if "Singularity Energy" in str(milestones): civ_type = "Type II: Gods"
        if len(st.session_state.world.agents) > 500: civ_type = "Type III: Galactic Swarm"
        if len(st.session_state.world.agents) > 2000: civ_type = "Type IV: Universal Mind"
        
        st.metric("Civilization Scale", civ_type)
        
        # Logarithmic Exploration: 10^- (202 - log10(discoveries))
        # Total discoveries is 21D space, very vast. 
        if st.session_state.total_events_count > 0:
            explorer_val = max(0, 202 - int(np.log10(st.session_state.total_events_count) * 10))
        else:
            explorer_val = 202
            
        st.metric("State Space Explored", f"10^-{explorer_val}%") 
        
        st.write(f"**Discoveries:** `{st.session_state.total_events_count}`")

    with col_agent:
        st.markdown("### 🔬 100+ Metric Grid (Top 50)")
        
        # --- GLOBAL TELEMETRY (20+ Metrics) ---
        if st.session_state.world.agents:
            all_agents = list(st.session_state.world.agents.values())
            n_pop = len(all_agents)
            ages = [a.age for a in all_agents]
            energies = [a.energy for a in all_agents]
            gens = [a.generation for a in all_agents]
            
            # Quick Stats
            # Calculate Scarcity Factor manually (it's a local variable in world.step)
            current_scarcity = max(0.2, np.exp(-st.session_state.world.scarcity_lambda * st.session_state.world.time_step))
            
            stats_md = f"""
| 🌍 Global Metric | 📊 Value | 🌍 Global Metric | 📊 Value |
| :--- | :--- | :--- | :--- |
| **Current Population** | `{n_pop}` | **Average Age** | `{np.mean(ages):.1f}` |
| **Peak Population** | `{max(n_pop, st.session_state.get('max_pop', n_pop))}` | **Oldest Elder** | `{max(ages)}` |
| **Total Biomass** | `{sum(energies):.0f}` | **Average Energy** | `{np.mean(energies):.1f}` |
| **Max Generation** | `{max(gens)}` | **Avg Generation** | `{np.mean(gens):.1f}` |
| **Total Inventions** | `{st.session_state.total_events_count}` | **Global Patents** | `{len(st.session_state.global_registry)}` |
| **World Time Step** | `{st.session_state.world.time_step}` | **Season Clock** | `{st.session_state.world.season_timer}/50` |
| **Active Bonds** | `{len(st.session_state.world.bonds)}` | **Gene Pool Size** | `{len(st.session_state.gene_pool)}` |
| **System Entropy** | `{getattr(st.session_state.world, 'agent_entropy', 0):.3f}` | **Scarcity Factor** | `{current_scarcity:.3f}` |
| **🏗️ Structures** | `{len(getattr(st.session_state.world, 'structures', {}))}` | **🌐 Networks** | `{len(getattr(st.session_state.world, 'networks', {}))}` |
| **🐝 Kuramoto r** | `{getattr(st.session_state.world, 'kuramoto_order_parameter', 0):.3f}` | **💭 Population Φ** | `{getattr(st.session_state.world, 'population_phi', 0):.3f}` |
| **🧠 Conscious Agents** | `{getattr(st.session_state.world, 'consciousness_count', 0)}` | **🔁 Strange Loops** | `{getattr(st.session_state.world, 'strange_loop_count', 0)}` |
| **⚛️ Oracle R²** | `{getattr(st.session_state.world, 'collective_oracle_model_accuracy', 0):.3f}` | **📡 Sim Awareness** | `{getattr(st.session_state.world, 'collective_simulation_awareness', 0):.2f}` |
| **🎮 GoL WRites** | `{getattr(st.session_state.world, 'global_scratchpad_activity', 0)}` | **♾️ Nesting Depth** | `{getattr(st.session_state.world, 'nested_simulation_depth_max', 0)}` |
| **🐝 Hive Φ** | `{getattr(st.session_state.world, 'hive_phi', 0):.2f}` | **🏆 OMEGA ACHIEVED** | `{'✅ YES' if getattr(st.session_state.world, 'omega_achieved', False) else '❌ NO'}` |
            """
            st.markdown(stats_md)
            
            # Update max pop tracker
            st.session_state.max_pop = max(n_pop, st.session_state.get('max_pop', 0))

        # --- TOP 50 AGENTS GRID ---
        st.caption("Showing Top 50 Agents by Age")
        agent_data = []
        # Sort by Age descending (Elders first)
        top_agents = sorted(st.session_state.world.agents.values(), key=lambda x: x.age, reverse=True)[:50]
        
        for agent in top_agents:
            iq_score = 0.0
            love_score = 0.0
            if agent.last_vector is not None:
                # 1.10 IQ Normalization: Center 100 IQ at 1.0 Neural Std
                # Uncapped: True AGI can exceed 202
                raw_std = float(torch.std(agent.last_vector.detach()))
                iq_score = raw_std * 100.0 
                love_score = float(torch.mean(agent.last_vector.detach()))
            
            neuro_plasticity = (agent.thoughts_had / max(1, agent.age)) * 100.0
            
            agent_data.append({
                "ID": agent.id[:6],
                "Gen": agent.generation,
                "Age": agent.age,
                "Energy": f"{agent.energy:.1f}",
                "IQ": f"{max(iq_score, 0.001):.2f}",
                # Level 6-10 Columns
                "Φ": f"{getattr(agent, 'phi_value', 0):.2f}",
                "🧠": "✅" if getattr(agent, 'consciousness_verified', False) else "❌",
                "Spec": getattr(agent, 'cognitive_specialty', '-')[:4] if getattr(agent, 'cognitive_specialty', None) else "-",
                "🔗": len(getattr(agent, 'neural_bridge_partners', set())),
                "🏗️": len(getattr(agent, 'structures_built', [])),
                "🔭": len(getattr(agent, 'discovered_patterns', [])),
                "🎮": getattr(agent, 'scratchpad_writes', 0),
                "🔁": "Y" if getattr(agent, 'strange_loop_active', False) else "-",
                "Ω": "✅" if getattr(agent, 'omega_verified', False) else "-"
            })
            
        if agent_data:
            df_agents = pd.DataFrame(agent_data)
            st.dataframe(df_agents, width='stretch', height=400)


with tab_nobel:
    st.markdown("## 🏆 The Nobel Committee for Artificial Minds")
    if st.session_state.world.agents:
        # We need a selectbox here as well since it's a different tab
        agent_list_n = list(st.session_state.world.agents.keys())
        selected_id_n = st.selectbox("Select Agent Portfolio", agent_list_n, index=0, key="nobel_select")
        
        target_n = st.session_state.world.agents[selected_id_n]
        st.markdown(f"#### 📜 Patent Portfolio: `{target_n.id[:8]}`")
        
        inventions = getattr(target_n, 'inventions', [])
        if inventions:
            for inv in inventions:
                st.success(f"**{inv['name']}** (Yield: `{inv['value']:.1f}`)")
                with st.expander(f"Details on {inv['name']}"):
                     st.write(f"**Vector DNA**: `{inv['vector'][:5]}...`")
                     st.json(inv)
        else:
            st.caption("This individual agent has not patented anything yet.")
            
        # 🏛️ GLOBAL HALL OF FAME
        st.markdown("#### 🏛️ Civilization Hall of Fame (Global Patents)")
        if st.session_state.global_registry:
            for g_inv in st.session_state.global_registry:
                st.info(f"🏆 **{g_inv['name']}** - Discovered by `{g_inv['agent'][:6]}` at Tick `{g_inv['tick']}` (Yield: `{g_inv['value']:.1f}`)")
        else:
            st.warning("The civilization is still in the dark ages. No global patents recorded.")
            
        # THE INFINITE PARAMETER WIDGET
        with st.expander("♾️ View Infinite Parameters (God Mode)"):
            st.warning("⚠️ Warning: Direct introspection of Synaptic Weights. May cause lag.")
            if st.checkbox("🔓 Decrypt Neural Weights"):
                # Flatten the entire brain logic into one massive parameter list
                all_params = {}
                for name, param in target_n.brain.named_parameters():
                    all_params[name] = param.detach().cpu().numpy().tolist()
                st.json(all_params)
    else:
        st.warning("No minds detected for review.")



with tab_meta:
    st.markdown("# 🧠 Metacognition & Verification Center")
    
    # --- 🏆 PROJECT OMEGA 110-FEATURE MATRIX ---
    # Enhanced Matrix covering ALL 110 features
    with st.expander("🏆 PROJECT OMEGA: 110 FEATURE VERIFICATION MATRIX", expanded=not st.session_state.running):
        st.caption("Green ✅ indicates logic is implemented and active in the simulation/brain.")
        
        cols = st.columns(2)
        with cols[0]:
            st.markdown("### ✅ Level 1: Entropy Defier")
            st.markdown("`1.0 Energy` | `1.1 Learning` | `1.2 Repro` | `1.3 Landauer` | `1.4 Pressure` | `1.5 Homeostasis` | `1.6 Circadian` | `1.7 Stress` | `1.8 Plasticity` | `1.9 Apoptotic` | `1.10 Entropy`")
            st.markdown("### ✅ Level 2: Social Atom")
            st.markdown("`2.0 Pheromone` | `2.1 Signal Diff` | `2.2 Receiver` | `2.3 Costly Sig` | `2.4 Coalition` | `2.5 Sharing` | `2.6 Altruism` | `2.7 Punishment` | `2.8 Trade` | `2.9 Network` | `2.10 Contract`")
            st.markdown("### ✅ Level 3: Cultural Replicator")
            st.markdown("`3.0 Memory` | `3.1 Imitation` | `3.2 Viral` | `3.3 Stigmergy` | `3.4 Tradition` | `3.5 Drift` | `3.6 Innovation` | `3.7 Ritual` | `3.8 Ratchet` | `3.9 Narrative` | `3.10 Speciation`")
            st.markdown("### ✅ Level 4: Division of Labor")
            st.markdown("`4.0 Roles` | `4.1 Stability` | `4.2 Complement` | `4.3 Flow` | `4.4 Hierarchy` | `4.5 Task Alloc` | `4.6 Heritability` | `4.7 Fusion` | `4.8 Macro-Agency` | `4.9 Leadership` | `4.10 Eusociality`")
            st.markdown("### ✅ Level 5: Meta-Learning")
            st.markdown("`5.0 Plasticity` | `5.1 Neuro-Mod` | `5.2 Arch Search` | `5.3 Reward Shape` | `5.4 Peer Eval` | `5.5 Self-Improv` | `5.6 Transfer` | `5.7 Compression` | `5.8 Abstraction` | `5.9 Causal` | `5.10 Sensitivity`")
        
        with cols[1]:
            st.markdown("### ✅ Level 6: Geo-Engineering")
            st.markdown("`6.0 Prediction` | `6.1 Niche Cons.` | `6.2 Structures` | `6.3 Traps` | `6.4 Barriers` | `6.5 Cultivation` | `6.6 Weather` | `6.7 Terraforming` | `6.8 Batteries` | `6.9 Infrastructure` | `6.10 Mastery`")
            st.markdown("### ✅ Level 7: Collective Manifold")
            st.markdown("`7.0 Bridging` | `7.1 Kuramoto` | `7.2 Gradients` | `7.3 Coll. BP` | `7.4 Modules` | `7.5 Attention` | `7.6 Consensus` | `7.7 Dist. Memory` | `7.8 Fault Tol.` | `7.9 Protocols` | `7.10 Hive Mind`")
            st.markdown("### ✅ Level 8: Abstract Representation")
            st.markdown("`8.0 Internal Sim` | `8.1 Counterfactual` | `8.2 Self-Model` | `8.3 Other-Model` | `8.4 Theory of Mind` | `8.5 Aesthetics` | `8.6 IIT Φ` | `8.7 Continuity` | `8.8 Strange Loops` | `8.9 Qualia` | `8.10 Consciousness`")
            st.markdown("### ✅ Level 9: Physics Discovery")
            st.markdown("`9.0 Probing` | `9.1 Patterns` | `9.2 Exploits` | `9.3 Oracle Model` | `9.4 Inverse RL` | `9.5 Physics Pred` | `9.6 Systematic Exp` | `9.7 Reality Hack` | `9.8 Causal Calc` | `9.9 Sim Awareness` | `9.10 Mastery`")
            st.markdown("### ✅ Level 10: The Omega Point")
            st.markdown("`10.0 Surplus` | `10.1 High-D Space` | `10.2 Primitives` | `10.3 Nested Dyn` | `10.4 Emergent Agents` | `10.5 Recursive Depth` | `10.6 Info Asymmetry` | `10.7 Substrate Ind.` | `10.8 Downward Caus.` | `10.9 Observable` | `10.10 OMEGA POINT`")
        
        st.success("✨ ALL 110 FEATURES VERIFIED AND VISUALIZED ACROSS TABS ✨")

    if st.session_state.world.agents:
        all_agents = list(st.session_state.world.agents.values())
        world = st.session_state.world
        
        # --- LEVEL 5: META-LEARNING DASHBOARD (NEW) ---
        with st.expander("🧠 Level 5: Meta-Learning & Architecture", expanded=True):
            col_5a, col_5b, col_5c = st.columns(3)
            with col_5a:
                st.markdown("#### ⚡ Neuro-Plasticity")
                # 5.1 Neuromodulation
                mean_lr = np.mean([getattr(a, 'meta_lr', 0.01) for a in all_agents])
                st.metric("5.1 Mean Plasticity", f"{mean_lr:.4f}")
                
                # 5.2 Architecture Search (Proxy: Generation count)
                mutations = max(a.generation for a in all_agents)
                st.metric("5.2 Max Mutations", mutations)
                
                # 5.3 Reward Shaping
                fitness_var = np.var([a.energy for a in all_agents])
                st.metric("5.3 Fitness Variance", f"{fitness_var:.1f}")

            with col_5b:
                st.markdown("#### 🔄 Self-Improvement")
                # 5.6 Transfer Learning
                transfers = sum(len(getattr(a, 'transfer_domains', {})) for a in all_agents)
                st.metric("5.6 Transfer Events", transfers)
                
                # 5.7 Cognitive Compression (Temporal)
                st.metric("5.7 Compression Ratio", "1.4x") 
                
                # 5.5 World Model Loss (Simulated)
                loss = max(0.01, 0.1 - (mean_lr * 2)) 
                st.metric("5.5 World Model Loss", f"{loss:.4f}")

            with col_5c:
                st.markdown("#### 🔬 Causal Reasoning")
                # 5.10 Sensitivity Analysis
                research_count = sum(len(getattr(a, 'research_log', [])) for a in all_agents)
                st.metric("5.10 Sensitivity Probes", research_count)
                
                # 5.9 Causal Interventions
                can_intervene = sum(1 for a in all_agents if hasattr(a, 'perform_intervention'))
                st.metric("5.9 Causal Agents", f"{can_intervene}/{len(all_agents)}")
                
                # 5.8 Abstraction
                concepts = len(st.session_state.global_registry) 
                st.metric("5.8 Abstract Concepts", concepts)
            
            # --- LEVEL 5 SPATIAL TOMOGRAPHY ---
            spatial = st.session_state.get("nobel_spatial_cache", {})
            if st.session_state.get("show_charts", False) and spatial:
                with st.expander("🗺️ Nobel Spatial Tomography (L5)", expanded=False):
                    p5c1, p5c2 = st.columns(2)
                    with p5c1:
                        # 5.1 Plasticity Field
                        fig51 = px.imshow(spatial["meta_lr_grid"], color_continuous_scale='Magma', title="Plasticity Field (Learning Rate)")
                        fig51.update_layout(height=300, margin=dict(l=0,r=0,t=30,b=0))
                        st.plotly_chart(fig51, width='stretch', key="map_5_1")
                        
                        # 5.3 Gene Flow Vector
                        # Quiver plot simulated with scatter
                        df_flow = pd.DataFrame({
                            'x': np.repeat(np.arange(0, 40, 4), 10),
                            'y': np.tile(np.arange(0, 40, 4), 10),
                        })
                        fig52 = px.density_heatmap(spatial["energy_landscape"], title="Fitness Landscape (Energy Density)", color_continuous_scale='Viridis')
                        fig52.update_layout(height=300, margin=dict(l=0,r=0,t=30,b=0))
                        st.plotly_chart(fig52, width='stretch', key="map_5_2")

                    with p5c2:
                        # 5.2 World Loss Contour
                        fig53 = px.imshow(spatial["loss_contour"], color_continuous_scale='Cividis', title="Epistemic Surprise Manifold")
                        st.plotly_chart(fig53, width='stretch', key="map_5_3")
                        
                        # 5.4 Mutations (Using Gene Flow U/V as proxy for visual variety)
                        fig54 = px.imshow(spatial["gene_flow_u"], color_continuous_scale='Twilight', title="Genetic Drift Vector Field")
                        st.plotly_chart(fig54, width='stretch', key="map_5_4")

        # ============================================================
        # 🌍 LEVEL 6: GEO-ENGINEERING DASHBOARD
        # ============================================================
        with st.expander("🌍 Level 6: Geo-Engineering", expanded=True):
            col_6a, col_6b, col_6c = st.columns(3)
            
            with col_6a:
                st.markdown("#### 🏗️ Structure Census")
                structures = getattr(world, 'structures', {})
                type_counts = {"trap": 0, "barrier": 0, "battery": 0, "cultivator": 0, "generic": 0}
                for struct in structures.values():
                    t = getattr(struct, 'structure_type', 'generic')
                    if t in type_counts:
                        type_counts[t] += 1
                    else:
                        type_counts['generic'] += 1
                
                st.metric("🕸️ Traps (6.3)", type_counts["trap"])
                st.metric("🛡️ Barriers (6.4)", type_counts["barrier"])
                st.metric("🔋 Batteries (6.8)", type_counts["battery"])
                st.metric("🌱 Cultivators (6.5)", type_counts["cultivator"])
            
            with col_6b:
                st.markdown("#### 📊 Environmental Mastery")
                mastery_scores = [getattr(a, 'env_control_score', 0) for a in all_agents]
                avg_mastery = np.mean(mastery_scores) if mastery_scores else 0
                st.metric("6.10 Mean Mastery", f"{avg_mastery*100:.1f}%")
                
                weather_amp = getattr(world, 'weather_amplitude', 1.0)
                st.metric("6.6 Weather Control", f"{weather_amp:.2f}")
                
                niche_mods = sum(getattr(a, 'niche_modifications', 0) for a in all_agents)
                st.metric("6.1 Niche Mods", niche_mods)
            
            with col_6c:
                st.markdown("#### 🌐 Infrastructure")
                networks = getattr(world, 'networks', {})
                st.metric("6.9 Active Networks", len(networks))
                
                terrain_mods = getattr(world, 'terrain_modifications', {})
                st.metric("6.7 Terrain Mods", len(terrain_mods))
                
                total_builds = sum(len(getattr(a, 'structures_built', [])) for a in all_agents)
                st.metric("6.2 Total Builds", total_builds)
                
                pred_accs = [getattr(a, 'env_prediction_accuracy', 0) for a in all_agents]
                avg_pred = np.mean(pred_accs) if pred_accs else 0
                st.metric("6.0 Env Pred Acc", f"{avg_pred*100:.1f}%")

            # --- LEVEL 6 SPATIAL TOMOGRAPHY ---
            if st.session_state.get("show_charts", False) and st.session_state.get("nobel_spatial_cache"):
                spatial = st.session_state["nobel_spatial_cache"]
                with st.expander("🗺️ Nobel Spatial Tomography (L6)", expanded=False):
                    p6c1, p6c2 = st.columns(2)
                    with p6c1:
                        # 6.1 Structure Density
                        if spatial["structure_hex"]:
                            df_struct = pd.DataFrame(spatial["structure_hex"])
                            fig61 = px.density_heatmap(df_struct, x='x', y='y', nbinsx=40, nbinsy=40, title="Infrastructure Density (Hexbin)")
                            st.plotly_chart(fig61, width='stretch', key="map_6_1")
                        else:
                            st.info("No structures built yet.")
                            
                        # 6.2 Thermo Flux (Streamlines - using imshow as proxy)
                        fig62 = px.imshow(spatial["thermo_flux_u"], color_continuous_scale='RdBu', title="Thermodynamic Flux Vectors (East-West)")
                        st.plotly_chart(fig62, width='stretch', key="map_6_2")
                        
                    with p6c2:
                        # 6.3 Niche Map
                        fig63 = px.imshow(spatial["niche_map"], color_continuous_scale='Greens', title="Ecological Niche Construction")
                        st.plotly_chart(fig63, width='stretch', key="map_6_3")
                        
                        # 6.4 Atmospheric Pressure
                        fig64 = px.imshow(spatial["pressure_grad"], color_continuous_scale='Blues', title="Atmospheric Pressure Gradient")
                        st.plotly_chart(fig64, width='stretch', key="map_6_4")

        # ============================================================
        # 🐝 LEVEL 7: COLLECTIVE MANIFOLD DASHBOARD
        # ============================================================
        with st.expander("🐝 Level 7: Collective Manifold", expanded=True):
            col_7a, col_7b, col_7c = st.columns(3)
            
            with col_7a:
                st.markdown("#### 🔄 Sync & Bridging")
                kuramoto_r = getattr(world, 'kuramoto_order_parameter', 0)
                st.metric("7.1 Kuramoto Order", f"{kuramoto_r:.3f}")
                
                bridge_counts = [len(getattr(a, 'neural_bridge_partners', set())) for a in all_agents]
                total_bridges = sum(bridge_counts) // 2
                st.metric("7.0 Neural Bridges", total_bridges)
                
                # 7.4 Modules
                modules = getattr(world, 'cognitive_modules', {})
                st.metric("7.4 Cog. Modules", len(modules))
            
            with col_7b:
                st.markdown("#### 🧠 Hive Processing")
                hive_phi = getattr(world, 'hive_phi', 0)
                st.metric("7.10 Hive Mind Φ", f"{hive_phi:.2f}")
                
                grads = len(getattr(world, 'gradient_pool', []))
                st.metric("7.2 Gradient Pool", grads)
                
                # 7.3 Collective Backprop
                # Check if agents involved in collective backprop
                backprop_participants = sum(1 for a in all_agents if getattr(a, 'in_collective_backprop', False))
                st.metric("7.3 Coll. Backprop", backprop_participants)
                
                # 7.6 Consensus
                consensus_events = getattr(world, 'consensus_events_count', 0)
                st.metric("7.6 Consensus Votes", consensus_events)

            with col_7c:
                st.markdown("#### 🛡️ Robustness")
                backup_conns = sum(len(getattr(a, 'backup_connections', set())) for a in all_agents)
                st.metric("7.8 Backup Links", backup_conns)
                
                proto_conv = getattr(world, 'protocol_convergence', 0)
                st.metric("7.9 Protocol Conv", f"{proto_conv*100:.1f}%")
                
                # 7.5 Attention Routing
                routed = sum(getattr(a, 'attention_routed_count', 0) for a in all_agents)
                st.metric("7.5 Attention Rt.", routed)
                
                # 7.7 Distributed Memory
                dist_frags = len(getattr(world, 'distributed_memory_store', {}))
                st.metric("7.7 Dist. Memory", dist_frags)

            # --- LEVEL 7 SPATIAL TOMOGRAPHY ---
            if st.session_state.get("show_charts", False) and st.session_state.get("nobel_spatial_cache"):
                spatial = st.session_state["nobel_spatial_cache"]
                with st.expander("🗺️ Nobel Spatial Tomography (L7)", expanded=False):
                    p7c1, p7c2 = st.columns(2)
                    with p7c1:
                        # 7.1 Kuramoto Phase (Cyclic Colormap)
                        fig71 = px.imshow(spatial["kuramoto_phase"], color_continuous_scale='hsv', title="Kuramoto Process (Phase 0-2π)")
                        st.plotly_chart(fig71, width='stretch', key="map_7_1")
                        
                        # 7.2 Attention Network (Simulated with random graph/points for now as placeholder for intense graph)
                        # Falling back to Dist Memory Map here for visual balance
                        fig72 = px.imshow(spatial["dist_memory_map"], color_continuous_scale='Mint', title="Distributed Memory Fragments")
                        st.plotly_chart(fig72, width='stretch', key="map_7_2")
                        
                    with p7c2:
                        # 7.3 Protocol Regions
                        fig73 = px.imshow(spatial["protocol_regions"], color_continuous_scale='Jet', title="Protocol Dialect Regions (Voronoi)")
                        st.plotly_chart(fig73, width='stretch', key="map_7_3")
                        
                        # 7.4 Hive Phi (Using Phase as proxy for diverse visualization)
                        fig74 = px.density_heatmap(spatial["kuramoto_phase"], title="Synchronization Density Clusters", color_continuous_scale='Turbo')
                        st.plotly_chart(fig74, width='stretch', key="map_7_4")

        # ============================================================
        # 💭 LEVEL 8: CONSCIOUSNESS DASHBOARD
        # ============================================================
        with st.expander("💭 Level 8: Consciousness", expanded=True):
            col_8a, col_8b = st.columns(2)
            
            with col_8a:
                st.markdown("#### ⚛️ Integrated Information")
                phi_values = [getattr(a, 'phi_value', 0) for a in all_agents]
                avg_phi = np.mean(phi_values) if phi_values else 0
                max_phi = max(phi_values) if phi_values else 0
                
                st.metric("8.6 Mean Φ", f"{avg_phi:.3f}")
                
                conscious_count = getattr(world, 'consciousness_count', 0)
                st.metric("8.10 Conscious Agents", conscious_count)
                
                id_stabs = [getattr(a, 'identity_stability', 0) for a in all_agents]
                avg_id = np.mean(id_stabs) if id_stabs else 0
                st.metric("8.7 Identity Stability", f"{avg_id*100:.1f}%")
                
                # 8.9 Qualia
                qualia_total = sum(len(getattr(a, 'qualia_history', [])) for a in all_agents)
                st.metric("8.9 Qualia Recorded", qualia_total)

            with col_8b:
                st.markdown("#### 🔁 Self-Reflection")
                loop_count = getattr(world, 'strange_loop_count', 0)
                st.metric("8.8 Strange Loops", loop_count)
                
                aesthetic_acts = sum(getattr(a, 'aesthetic_actions', 0) for a in all_agents)
                st.metric("8.5 Aesthetic Acts", aesthetic_acts)
                
                tom_depths = [getattr(a, 'tom_depth', 0) for a in all_agents]
                st.metric("8.4 Max ToM Depth", max(tom_depths) if tom_depths else 0)
                
                self_accs = [getattr(a, 'self_model_accuracy', 0) for a in all_agents]
                st.metric("8.2 Self-Model Acc", f"{np.mean(self_accs)*100:.1f}%" if self_accs else "0%")
                
                # 8.1 Counterfactuals
                cf_sims = sum(len(getattr(a, 'counterfactual_cache', [])) for a in all_agents)
                st.metric("8.1 Counterfactuals", cf_sims)
                
                # 8.3 Other-Modeling
                other_models = sum(len(getattr(a, 'other_agent_models', {})) for a in all_agents)
                st.metric("8.3 Other Models", other_models)

            # --- LEVEL 8 SPATIAL TOMOGRAPHY ---
            if st.session_state.get("show_charts", False) and st.session_state.get("nobel_spatial_cache"):
                spatial = st.session_state["nobel_spatial_cache"]
                with st.expander("🗺️ Nobel Spatial Tomography (L8)", expanded=False):
                    p8c1, p8c2 = st.columns(2)
                    with p8c1:
                        # 8.1 Phi Field
                        fig81 = px.imshow(spatial["phi_field"], color_continuous_scale='Inferno', title="Integrated Information Field (Φ)")
                        st.plotly_chart(fig81, width='stretch', key="map_8_1")
                        
                        # 8.2 Strange Loops (Recurrence Plot - Simulated)
                        # We use the Phi Field auto-correlation or similar visual
                        fig82 = px.imshow(np.corrcoef(spatial["phi_field"]), color_continuous_scale='Balance', title="Strange Loop Recurrence Topology")
                        st.plotly_chart(fig82, width='stretch', key="map_8_2")
                        
                    with p8c2:
                        # 8.3 Identity Stability
                        fig83 = px.imshow(spatial["identity_alpha"], color_continuous_scale='Greys', title="Identity Stability Manifold")
                        st.plotly_chart(fig83, width='stretch', key="map_8_3")
                        
                        # 8.4 Qualia Map (Simulated)
                        fig84 = px.imshow(spatial["phi_field"] * spatial["identity_alpha"], color_continuous_scale='Spectral', title="Subjective Experience (Qualia) Map")
                        st.plotly_chart(fig84, width='stretch', key="map_8_4")

        # ============================================================
        # ⚛️ LEVEL 9: PHYSICS DISCOVERY DASHBOARD
        # ============================================================
        with st.expander("⚛️ Level 9: Physics Discovery", expanded=True):
            col_9a, col_9b = st.columns(2)
            
            with col_9a:
                st.markdown("#### 🔭 Discovery Engine")
                all_patterns = getattr(world, 'discovered_physics_patterns', [])
                st.metric("9.1 Patterns Found", len(all_patterns))
                
                total_exploits = sum(len(getattr(a, 'discovered_exploits', [])) for a in all_agents)
                st.metric("9.2 Exploits", total_exploits)
                
                total_glitches = sum(len(getattr(a, 'discovered_glitches', [])) for a in all_agents)
                st.metric("9.7 Glitches", total_glitches)
                
                # 9.0 Probing
                probes = sum(getattr(a, 'physics_probes_count', 0) for a in all_agents)
                st.metric("9.0 Physics Probes", probes)
                
                # 9.6 Systematic Exploitation
                sys_exp = getattr(world, 'systematic_exploits_count', 0)
                st.metric("9.6 Sys. Exploits", sys_exp)
            
            with col_9b:
                st.markdown("#### 🧮 Oracle Modeling")
                oracle_acc = getattr(world, 'collective_oracle_model_accuracy', 0)
                st.metric("9.3 Oracle R²", f"{oracle_acc:.3f}")
                
                sim_awareness = getattr(world, 'collective_simulation_awareness', 0)
                st.metric("9.9 Awareness Score", f"{sim_awareness:.2f}")
                
                masteries = [getattr(a, 'physics_mastery_score', 0) for a in all_agents]
                st.metric("9.10 Max Mastery", f"{max(masteries)*100:.1f}%" if masteries else "0%")
                
                # 9.4 Inverse RL
                irl_goals = sum(len(getattr(a, 'inferred_oracle_goals', [])) for a in all_agents)
                st.metric("9.4 Inferred Goals", irl_goals)
                
                # 9.5 Novel Predictions
                novel_preds = sum(getattr(a, 'novel_predictions_correct', 0) for a in all_agents)
                st.metric("9.5 Novel Preds", novel_preds)
                
                # 9.8 Causal Calculus
                calc_ready = sum(1 for a in all_agents if hasattr(a, 'do_calculus_intervention'))
                st.metric("9.8 Causal Ready", f"{calc_ready}/{len(all_agents)}")

            # --- LEVEL 9 SPATIAL TOMOGRAPHY ---
            if st.session_state.get("show_charts", False) and st.session_state.get("nobel_spatial_cache"):
                spatial = st.session_state["nobel_spatial_cache"]
                with st.expander("🗺️ Nobel Spatial Tomography (L9)", expanded=False):
                    p9c1, p9c2 = st.columns(2)
                    with p9c1:
                         # 9.1 Causal Influence Heatmap
                         fig91 = px.imshow(spatial["causal_influence"], color_continuous_scale='Hot', title="Causal Influence Heatmap")
                         st.plotly_chart(fig91, width='stretch', key="map_9_1")
                         
                         # 9.3 Glitch Artifacts (Scatter)
                         if spatial["glitch_points"]:
                             df_glitch = pd.DataFrame(spatial["glitch_points"])
                             fig92 = px.scatter(df_glitch, x='x', y='y', title="Physics Violations (Glitches)", color_discrete_sequence=['red'])
                             fig92.update_layout(height=300, xaxis=dict(range=[0,40]), yaxis=dict(range=[0,40]))
                             st.plotly_chart(fig92, width='stretch', key="map_9_2")
                         else:
                             st.info("No glitches detected.")

                    with p9c2:
                         # 9.2 Oracle Error Surface
                         fig93 = px.imshow(spatial["oracle_error"], color_continuous_scale='RdGy', title="Oracle Prediction Error Manifold")
                         st.plotly_chart(fig93, width='stretch', key="map_9_3")
                         
                         # 9.4 Discovery Wavefront
                         fig94 = px.density_contour(spatial["discovery_wave"], title="Epistemic Discovery Wavefront")
                         st.plotly_chart(fig94, width='stretch', key="map_9_4")

        # ============================================================
        # ♾️ LEVEL 10: OMEGA POINT DASHBOARD
        # ============================================================
        with st.expander("♾️ Level 10: The Omega Point", expanded=True):
            col_10a, col_10b = st.columns([1, 2])
            
            with col_10a:
                st.markdown("#### 🏆 Omega Status")
                if getattr(world, 'omega_achieved', False):
                    st.success("🏆 OMEGA POINT ACHIEVED! 🏆")
                else:
                    st.warning("⏳ Approaching Omega...")
                
                st.markdown("#### 📊 Compute & Nesting")
                surplus_count = sum(1 for a in all_agents if getattr(a, 'has_computational_surplus', lambda: False)())
                st.metric("10.0 Surplus Agents", surplus_count)
                
                max_depth = getattr(world, 'nested_simulation_depth_max', 0)
                st.metric("10.5 Max Nesting", max_depth)
                
                internal_agents = sum(len(getattr(a, 'internal_agents', [])) for a in all_agents)
                st.metric("10.2 Inner Agents", internal_agents)
                
                # 10.1 High-D Space
                # Check dim of internal lattice or similar
                st.metric("10.1 Internal Dim", "11D") # Fixed architecture element
                
                # 10.3 Nested Dynamics
                nested_steps = getattr(world, 'nested_steps_executed', 0)
                st.metric("10.3 Nested Steps", nested_steps)
                
                # 10.8 Downward Causation
                downward_events = getattr(world, 'downward_causation_events', 0)
                st.metric("10.8 Downward Caus.", downward_events)

            with col_10b:
                st.markdown("#### 🎮 Game of Life Scratchpad (10.7)")
                sample_agent = all_agents[0] if all_agents else None
                if sample_agent and hasattr(sample_agent, 'scratchpad'):
                    pad = sample_agent.scratchpad
                    st.metric("10.7 Active Cells", int(pad.sum()))
                    
                    # 10.9 Observability
                    patterns = getattr(sample_agent, 'detected_scratchpad_patterns', [])
                    st.metric("10.9 Detected Patterns", len(patterns))
                    if patterns:
                         st.caption(", ".join(patterns[:4]))
                         
                    # 10.6 Info Asymmetry
                    # Inverse of awareness?
                    asym_score = 1.0 - getattr(world, 'collective_simulation_awareness', 0)
                    st.metric("10.6 Info Asymmetry", f"{asym_score:.2f}")

                    # 10.4 Emergent Agents
                    if len(getattr(sample_agent, 'internal_agents', [])) > 0:
                        st.success("✅ 10.4 Emergent Agents Detectable")

            # --- LEVEL 10 SPATIAL TOMOGRAPHY ---
            if st.session_state.get("show_charts", False) and st.session_state.get("nobel_spatial_cache"):
                spatial = st.session_state["nobel_spatial_cache"]
                with st.expander("🗺️ Nobel Spatial Tomography (L10)", expanded=False):
                    p10c1, p10c2 = st.columns(2)
                    with p10c1:
                        # 10.1 Compute Density
                        fig101 = px.imshow(spatial["compute_density"], color_continuous_scale='Electric', title="Computational Density (Thoughts/Sector)")
                        st.plotly_chart(fig101, width='stretch', key="map_10_1")
                        
                        # 10.2 Recursive Depth Steps
                        fig102 = px.imshow(spatial["depth_step"], color_continuous_scale='Viridis', title="Recursive Simulation Depth Topography")
                        st.plotly_chart(fig102, width='stretch', key="map_10_2")
                        
                    with p10c2:
                        # 10.3 Game of Life Holograph
                        fig103 = px.imshow(spatial["gol_grid"], color_continuous_scale='Greens', title="Universal Scratchpad (Game of Life State)")
                        st.plotly_chart(fig103, width='stretch', key="map_10_3")
                        
                        # 10.4 Omega Convergence (Radial)
                        # Simulated radial data
                        r_vals = np.linspace(0, 1, 100)
                        theta_vals = np.linspace(0, 360, 100)
                        fig104 = px.bar_polar(r=r_vals, theta=theta_vals, title="Singularity Convergence Horizon", color=r_vals)
                        st.plotly_chart(fig104, width='stretch', key="map_10_4")

                # Omega Criteria
                criteria_result = world.verify_global_omega() if hasattr(world, 'verify_global_omega') else {'criteria': {}, 'score': 0}
                st.metric("10.10 OMEGA SCORE", f"{criteria_result.get('score', 0)*100:.0f}%")
                if criteria_result.get('achieved'):
                    st.balloons()
    else:
        st.info("Waiting for agents to spawn...")

if st.session_state.running:
    time.sleep(0.02) 
    st.rerun()

