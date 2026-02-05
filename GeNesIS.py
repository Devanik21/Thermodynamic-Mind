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
from genesis_world import GenesisWorld, Resource
from genesis_brain import GenesisAgent
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

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
SYSTEM_VERSION = "3.1.5" # Level 3: Final Stability Update

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

init_system()

# ============================================================
# 🔄 SIMULATION LOGIC LOOP
# ============================================================
def update_simulation():
    if not st.session_state.running:
        return

    world = st.session_state.world
    world.step()
    
    current_thoughts = 0
    deaths = set() # Use a set to avoid KeyError on duplicate IDs
    events_this_tick = []
    
    agents = list(world.agents.values())
    np.random.shuffle(agents) 
    
    total_pos_flux = 0.0
    total_neg_flux = 0.0
    
    for agent in agents:
        if agent.energy <= 0:
            deaths.add(agent.id)
            continue
            
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

        # Decide now returns (Vector, CommVector, Mate, Adhesion, Punish, Trade, MemeWrite)
        reality_vector_tensor, comm_vector, mate_desire, adhesion_val, punish_val, trade_val, meme_write = agent.decide(
            signal, 
            pheromone_16=pheromone_vector, 
            meme_3=meme_vector, # 3.3 Input
            env_phase=env_phase,
            social_trust=social_trust,
            gradient=gradient_val
        ) 
        
        # 3.3 Stigmergy: Write to Meme Grid
        # Decaying write to avoid saturation: Old * 0.9 + New * 0.1
        world.meme_grid[mx, my] = world.meme_grid[mx, my] * 0.9 + meme_write.detach().numpy() * 0.1
        
        flux, log_text = world.resolve_quantum_state(
            agent, reality_vector_tensor, emit_vector=comm_vector, 
            adhesion=adhesion_val, punish=punish_val, trade=trade_val
        ) 
        
        # ❤️ PHASE 14: "GOD-REMOVER" UPGRADE (Autopoietic Reproduction)
        # Agents reproduce themselves without system intervention.
        if mate_desire > 0.5 and agent.energy > 80.0 and len(world.agents) < 256:
            # Look for partner
            partners = [
                other for other in agents 
                if other.id != agent.id 
                and other.energy > 80.0 
                and abs(other.x - agent.x) <= 1 
                and abs(other.y - agent.y) <= 1
            ]
            
            if partners:
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
                agent.energy -= 40.0
                partner.energy -= 40.0
                
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
        malthusian_cost = 0.5 + (np.log1p(len(world.agents)) / 3.0)
        agent.energy -= malthusian_cost 
        
        # 🧬 MITOSIS (Hard Cap: 256 per user request)
        if agent.energy > 120.0 and len(world.agents) < 256:
            agent.energy -= 60.0 
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
            
            # 1.9 Apoptotic Information Transfer (Death Broadcast)
            # Neighboring agents learn from the dead agent's weights
            with torch.no_grad():
                dead_genome = dead_agent.get_genome()
                # Find physical neighbors
                neighbors = [
                    a for a in world.agents.values() 
                    if a.id != dead_id and abs(a.x - dead_agent.x) <= 2 and abs(a.y - dead_agent.y) <= 2
                ]
                for n in neighbors:
                    # Transfer 10% of weight knowledge
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
                    "Event": "💀 DIED (Broadcasted)",
                    "Vector": [0.0]*21
                })
            del world.agents[dead_id]
        
    # Global Max Gen Update
    if world.agents:
        current_max = max(a.generation for a in world.agents.values())
        if current_max > st.session_state.max_generation:
            st.session_state.max_generation = current_max
                
    # Failsafe: only restart if TRULY extinct
    if len(world.agents) < 4:
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
    
    st.session_state.stats_history.append(stats)
    if len(st.session_state.stats_history) > 200:
        st.session_state.stats_history.pop(0)
        
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
        if st.button("▶️ TOGGLE SIMULATION", width="stretch", type="primary" if not st.session_state.running else "secondary"):
            st.session_state.running = not st.session_state.running
    with col_h3:
        if st.button("♻️ RESET WORLD", width="stretch"):
            st.session_state.world = GenesisWorld(size=40)
            st.session_state.stats_history = []
            st.session_state.gene_pool = []
            st.session_state.max_generation = 0
            st.session_state.global_registry = []
            st.rerun()
    with col_h4:
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
                width="stretch"
            )

# --- MAIN TABS FRAGMENT ---
tab_macro, tab_micro, tab_culture, tab_nobel, tab_omega = st.tabs(["🔭 OBSERVATION DECK", "🧬 QUANTUM SPECTROGRAM", "🏺 Culture", "🏆 Nobel Committee", "Ω OMEGA TELEMETRY"])

with tab_macro:
    if st.session_state.stats_history:
        df = pd.DataFrame(st.session_state.stats_history)
        
        # Row 1: Graphs
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['tick'], y=df['population'], name="Survivors", line=dict(color='#00ffa3')))
            fig.add_trace(go.Scatter(x=df['tick'], y=df['thoughts'], name="Plasticity Events", line=dict(color='#ff4b4b')))
            fig.update_layout(title="Evolutionary Trajectory", height=230, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            
        with col_g2:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df['tick'], y=df['pos_flux'], name="Invention Yield", line=dict(color='yellow'), fill='tozeroy'))
            fig2.add_trace(go.Scatter(x=df['tick'], y=df['neg_flux'], name="Resource Drain", line=dict(color='red'), fill='tozeroy'))
            fig2.update_layout(title="Efficiency vs Chaos", height=230, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig2, use_container_width=True)

        with col_g3:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=df['tick'], y=df['agent_entropy'], name="Neural Entropy", line=dict(color='#45b6fe')))
            fig3.add_trace(go.Scatter(x=df['tick'], y=df['scarcity'], name="Env Availability", line=dict(color='gray', dash='dot')))
            fig3.update_layout(title="Thermodynamics (Ω Metric)", height=230, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig3, use_container_width=True)
            
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
        st.plotly_chart(fig_map, width="stretch")
    else:
        st.info("System Initializing...")

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
                
                fig_cluster = px.scatter(
                    df_pca, x='PC1', y='PC2', color='Cluster', 
                    hover_data=['Agent'],
                    title=f"Semantic Signal Clusters (k={n_clusters})",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig_cluster.update_layout(height=350, plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_cluster, use_container_width=True)
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
                 fig_mod = px.scatter(x=states, y=actions, labels={'x': "Internal Energy", 'y': "Mean Action Vector"}, title="Energy vs Action Modulation")
                 fig_mod.update_layout(height=300)
                 st.plotly_chart(fig_mod, use_container_width=True)
                
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
                vec_arr = np.array(vectors)
                fig_spec = px.imshow(
                    vec_arr, 
                    color_continuous_scale='Plasma', 
                    aspect='auto',
                    labels=dict(x="Dimension (0-20)", y="Agent Sample", color="Activation"),
                    title=f"Real-Time Thought Spectrum (n={len(vectors)})"
                )
                fig_spec.update_layout(height=400, margin=dict(l=0,r=0,t=30,b=0))
                st.plotly_chart(fig_spec, width="stretch")
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
                h_state = target.hidden_state.detach().cpu().numpy()
                fig_h = px.imshow(
                    h_state, 
                    color_continuous_scale='Viridis',
                    labels=dict(x="Memory Dim (0-63)", color="Charge"),
                    title="Short-Term Memory (GRU Hidden State)"
                )
                fig_h.update_layout(height=150, margin=dict(l=0,r=0,t=30,b=0), yaxis=dict(visible=False))
                st.plotly_chart(fig_h, use_container_width=True)
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
        # Grid is (40, 40, 3). Channels: R(Danger), G(Food), B(Sacred)
        if hasattr(st.session_state.world, 'meme_grid'):
            meme_vis = st.session_state.world.meme_grid.copy()
            # Clip to 0-1 range for RGB display
            meme_vis = np.clip(meme_vis, 0, 1)
            # Resize for better visibility (optional, but plotly heatmap handles it)
            
            fig_meme = px.imshow(
                meme_vis, 
                title="Collective Memory (RGB: Danger/Resource/Sacred)",
                labels=dict(x="X", y="Y")
            )
            fig_meme.update_layout(height=400, margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig_meme, use_container_width=True)
        else:
            st.info("Meme Grid initializing...")
            
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
                fig_trad = px.line(
                    y=st.session_state.tradition_history, 
                    title="Tradition Index (Action Stability)",
                    labels={'y': "Mean Action Norm", 'x': "Time"}
                )
                fig_trad.update_layout(height=200)
                st.plotly_chart(fig_trad, use_container_width=True)
                
        # 3.6 Innovation Diffusion
        st.markdown("### 🚀 Innovation Rate")
        inv_count = len(st.session_state.global_registry)
        st.metric("Total Patents", inv_count)
        
        if st.session_state.global_registry:
            # Show recent inventions
            recents = st.session_state.global_registry[-5:]
            for inv in recents:
                st.caption(f"Tick {inv['tick']}: **{inv['name']}** (Yield {inv['value']:.1f})")

            
    with col_log:
        st.markdown("### ⚡ Event Stream")
        if st.session_state.event_log:
             log_df = pd.DataFrame(st.session_state.event_log)
             st.dataframe(log_df[["Agent", "Event"]], width="stretch", height=400)

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
        st.markdown("### 🔬 100+ Metric Grid")
        agent_data = []
        for agent in st.session_state.world.agents.values():
            iq_score = 0.0
            love_score = 0.0
            if agent.last_vector is not None:
                iq_score = float(torch.std(agent.last_vector.detach())) * 100.0
                love_score = float(torch.mean(agent.last_vector.detach()))
            
            neuro_plasticity = (agent.thoughts_had / max(1, agent.age)) * 100.0
            
            agent_data.append({
                "ID": agent.id[:6],
                "Gen": agent.generation,
                "Age": agent.age,
                "Energy": f"{agent.energy:.2f}",
                "Stored": f"{getattr(agent, 'energy_stored', 0):.1f}",
                "Inv (R,G,B)": f"{agent.inventory}",
                "IQ": f"{iq_score:.4f}",
                "H(W)": f"{getattr(agent, 'last_weight_entropy', 0):.3f}",
                "Bio-Hack %": f"{neuro_plasticity:.2f}%",
                "Entropy": f"{np.log(agent.age + 1):.4f}",
                "Reflexes": agent.reflexes_used,
                "Thoughts": agent.thoughts_had
            })
            
        if agent_data:
            df_agents = pd.DataFrame(agent_data)
            st.dataframe(df_agents, width="stretch", height=400)


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


if st.session_state.running:
    time.sleep(0.02) 
    st.rerun()
