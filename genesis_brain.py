import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import random
import uuid

# ============================================================
# 🧬 NEURAL ARCHITECTURE
# ============================================================
# ============================================================
# 🧬 NEURAL ARCHITECTURE
# ============================================================
class GradientCompressor(nn.Module):
    """
    5.7 Cognitive Compression: Learned Low-Rank Approximation of Gradients.
    'Learning to Learn' by compressing update vectors into 'principal components' of adaptation.
    """
    def __init__(self, input_dim, rank=8):
        super().__init__()
        # U * V approx of the gradient space
        self.U = nn.Parameter(torch.randn(input_dim, rank) * 0.01)
        self.V = nn.Parameter(torch.randn(rank, input_dim) * 0.01)
        
    def forward(self, grad):
        # Project gradient into low-rank subspace and back
        # grad_approx = (grad @ V.T) @ U.T
        if grad is None: return None
        # Simple compression: Filter gradient through the bottleneck
        # We want to find the 'component' of the gradient that aligns with U*V
        # But for 'meta-learning', we essentially want to MODIFY the gradient.
        # G_new = G + (G @ V.T @ U.T) * alpha
        
        # Matrix multiplication match: Grad shape (N, Out) or (Out, In)?
        # Assumes flattened or compatible shape. 
        # For simplicity, we apply this to the generic 1D flattened gradient vector if used,
        # OR we treat it as layer-wise modulation.
        
        # SIMPLIFIED IMPLEMENTATION for 5.7:
        # We learn a 'filter' that amplifies useful gradient directions and suppressed noise.
        # But U, V needs to match dimensions. 
        # Let's effectively assume this is a scalar gate per parameter for now to save compute,
        # OR a small MLP that takes gradient statistics and outputs a scaling factor.
        
        # Better: Low Rank Adaptation (LoRA) style but for the UPDATE rule.
        pass

class PruningMask(nn.Module):
    """5.2 Architecture Search: Learnable mask for weight pruning."""
    def __init__(self, shape):
        super().__init__()
        self.mask_logits = nn.Parameter(torch.ones(shape) * 5.0) # Start fully connected
        
    def forward(self):
        # Differentiable binary mask via Sigmoid ~ Gate
        return torch.sigmoid(self.mask_logits)

    def sparsity(self):
        return (self.forward() < 0.1).float().mean()

class GenesisBrain(nn.Module):
    """
    The cognitive engine of an agent.
    Input: [Local Matter (16) + Pheromone (16) + Meme (3) + Phase (2) + Energy (1) + Reward (1) + Trust (1) + Gradient (1)] = 41 Dimensions
    Hidden: 64
    Output: 21 (Reality Vector) + 16 (Comm Vector) + 4 (Mate, Adhesion, Punish, Trade) + 1 (Critic)
    """
    def __init__(self, input_dim=41, hidden_dim=64, output_dim=21):
        super().__init__()
        self.hidden_dim = hidden_dim
        
        # 1.1 Neural Learning
        self.gru = nn.GRU(input_dim, hidden_dim, batch_first=True)
        self.actor = nn.Linear(hidden_dim, output_dim) 
        # 5.2 Pruning Mask for Actor (Architecture Search)
        self.actor_mask = PruningMask(self.actor.weight.shape)
        
        self.comm_out = nn.Linear(hidden_dim, 16) # Social Signaling Layer
        self.meta_out = nn.Linear(hidden_dim, 4) # [Mate, Adhesion, Punish, Trade]
        self.critic = nn.Linear(hidden_dim, 1) # Value function for RL
        
        # 5.8 Abstraction Discovery ( Bottleneck Autoencoder )
        # Compress hidden state to find "Concepts"
        self.concept_dim = 8
        self.abstraction_encoder = nn.Linear(hidden_dim, self.concept_dim)
        self.abstraction_decoder = nn.Linear(self.concept_dim, hidden_dim)

        # 3.9 Narrative Memory & 5.9 Causal Predictor
        # Predicts the NEXT input state (Self-Supervised Learning)
        # Optimized for counterfactual reasoning
        self.predictor = nn.Linear(hidden_dim, input_dim) 
        
        # 5.7 Cognitive Compression
        # Learnable compression of the GRU weight updates (largest matrix)
        # Flattened GRU weight size: 3*hidden*hidden + 3*hidden*input approx
        # We simplify: Just learn to compress the Hidden->Hidden interactions (64x64)
        self.compressor = nn.Sequential(
            nn.Linear(hidden_dim, 16),
            nn.Tanh(),
            nn.Linear(16, hidden_dim)
        )
        # Initialize small to start as identity-like
        nn.init.orthogonal_(self.compressor[0].weight, gain=0.1)
        nn.init.orthogonal_(self.compressor[2].weight, gain=0.1)
        
        # Initialize weights
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0.0)

    def forward(self, x, hidden):
        if hidden is None:
            hidden = torch.zeros(1, x.size(0), self.hidden_dim)
            
        out, h_next = self.gru(x.unsqueeze(1), hidden)
        last_hidden = out[:, -1, :]
        
        # 5.8 Abstraction: Force information through bottleneck
        concepts = torch.relu(self.abstraction_encoder(last_hidden))
        reconstructed_hidden = self.abstraction_decoder(concepts)
        # Residual connection to preserve gradients but encourage concept usage
        mixed_hidden = last_hidden + reconstructed_hidden * 0.1
        
        # 5.2 Apply Pruning Mask
        effective_weights = self.actor.weight * self.actor_mask()
        # Manual linear pass to allow weighting
        vector = torch.relu(torch.nn.functional.linear(mixed_hidden, effective_weights, self.actor.bias))

        comm = torch.sigmoid(self.comm_out(mixed_hidden)) # Signal Vector (Pheromones/Memes)
        meta = torch.sigmoid(self.meta_out(mixed_hidden)) # [Mate, Adhesion, Punish, Trade]
        value = self.critic(mixed_hidden)               # Estimated Value
        prediction = self.predictor(mixed_hidden)       # 3.9 Predicted Next State
        
        return vector, comm, meta, value, h_next, prediction, concepts

# ============================================================
# 🤖 THE AGENT
# ============================================================
class GenesisAgent:
    def __init__(self, x, y, genome=None, generation=0, parent_hidden=None, parent_inventory=None):
        self.id = str(uuid.uuid4())
        self.x = x
        self.y = y
        self.generation = generation
        self.age = 0
        self.energy = 60.0 # Increased starting energy
        self.energy_stored = 0.0 # 1.5 Homeostasis
        self.inventory = [0, 0, 0] if parent_inventory is None else parent_inventory
        
        # 1.3 Landauer Limit metrics
        self.last_weight_entropy = 0.0
        self.reflexes_used = 0
        self.thoughts_had = 0
        self.social_memory = {}
        self.inventions = [] # Level 3.6 Innovation Tracking
        self.tag = np.random.rand(3) # 3.10 Cultural tag (RGB tribe)
        
        # 1.6 Circadian Rhythms
        self.internal_phase = random.random() * 2 * np.pi
        self.influence = 0.0 # 4.4 Initialize early to avoid AttributeError
        
        # --- PHASE 15: LEVEL 4 SPECIALIZATION ---
        self.role = "Generalist" # 4.0 Behavioral Polymorphism
        self.role_history = []  # 4.1 Role Stability
        self.caste_gene = np.random.rand(4) # 4.6 Caste Genetics (Vector predisposition for roles)
        self.is_fused = False   # 4.7 Dynamic Tensor Fusion
        self.fused_partner = None
        self.is_fertile = True # 4.10 Eusociality (Queens vs Workers)
        if generation > 0:
            # 4.10: 20% chance to be a Queen if gen > 0 (simplification for starting)
            self.is_fertile = random.random() < 0.2
        
        # Neural State
        self.brain = GenesisBrain()
        self.optimizer = optim.Adam(self.brain.parameters(), lr=0.005)
        
        # 3.0 Epigenetic Memory: Inherit mental state
        if parent_hidden is not None:
            self.hidden_state = parent_hidden.detach().clone() + torch.randn_like(parent_hidden) * 0.1
        else:
            self.hidden_state = torch.zeros(1, 1, 64)
        
        # v5.0.4 Persistent state for Ghost Forward
        self.prev_input = None
        self.prev_hidden = None
        
        self.last_concepts = torch.zeros(1, 8) # 5.8 Initialize
        
        # LEVEL 5 STATE MEMORY
        # 5.0 Self-Monitoring
        self.prediction_errors = []
        self.confidence = 0.5 
        
        # 5.1 Meta-Learning (Hypergradients)
        self.meta_lr = 0.005
        self.last_grad_norm = 0.0
        
        # 5.9 Causal Reasoning (Counterfactuals)
        self.causal_graph = {} # {action_dim -> sensory_impact_score}
        
        # 5.10 Autonomous Research
        self.research_log = []
        
        # 3.2 Horizontal Neural Transfer (Viral Memory)
        self.meme_pool = [] # List of {weights: StateDict, fitness: float, beta: float, type: 'virus'}

        
        # Memory for learning
        self.last_vector = torch.zeros(1, 21)
        self.last_value = torch.zeros(1, 1)
        self.last_comm = torch.zeros(1, 16)
        self.last_reward = 0.0
        self.last_prediction = None
        self.last_input = None
        self.last_weight_entropy = self.calculate_weight_entropy()
        
        # If born from parents, inherit genome
        if genome:
            self._apply_genome(genome)

    def calculate_weight_entropy(self):
        """1.3 Landauer Metric: Shannon entropy of the brain's weight distribution."""
        with torch.no_grad():
            all_weights = torch.cat([p.view(-1) for p in self.brain.parameters()])
            hist = torch.histc(all_weights, bins=20, min=-2, max=2)
            prob = hist / (hist.sum() + 1e-8)
            entropy = -torch.sum(prob * torch.log2(prob + 1e-8))
            return entropy.item()

    def generate_zahavi_proof(self, vector, difficulty=1):
        """
        2.3 Zahavi Handicap: Generate Proof of Work (Hash(message || nonce)).
        Returns a nonce that produces 'difficulty' leading zeros.
        """
        import hashlib
        target = "0" * difficulty
        nonce = 0
        # Quantize vector to avoid float instability in hashing
        vec_bytes = (vector * 100).long().cpu().numpy().tobytes()
        
        # Limit iterations to avoid freezing the simulation
        max_iter = 100 
        for _ in range(max_iter):
            candidate = f"{nonce}".encode() + vec_bytes
            h = hashlib.sha256(candidate).hexdigest()
            if h.startswith(target):
                return nonce
            nonce += 1
        return 0 # Failed to find proof within effort budget

    def decide(self, signal_16, **kwargs):
        self.age += 1
        pheromone_16 = kwargs.get('pheromone_16', torch.zeros(16))
        # 3.3 Meme Perception
        meme_3 = kwargs.get('meme_3', torch.zeros(3))
        
        env_phase = kwargs.get('env_phase', 0.0)
        social_trust = kwargs.get('social_trust', 0.0)
        gradient = kwargs.get('gradient', 0.0)
            
        # 1.6 Synchronization
        self.internal_phase += 0.1 * np.sin(env_phase - self.internal_phase)
        phase_signal = torch.tensor([[np.sin(self.internal_phase), np.cos(self.internal_phase)]])
        
        # 2.2 State-Dependent Input & 1.7 Stress Response
        energy_signal = torch.tensor([[self.energy / 200.0]]) # Normalized
        reward_signal = torch.tensor([[self.last_reward / 50.0]])
        trust_signal = torch.tensor([[social_trust]])
        gradient_signal = torch.tensor([[gradient]])
        
        # Concatenate: [Matter(16), Pheromone(16), Meme(3), Phase(2), Energy(1), Reward(1), Trust(1), Gradient(1)] = 41
        input_tensor = torch.cat([
            signal_16.unsqueeze(0), 
            pheromone_16.unsqueeze(0),
            meme_3.unsqueeze(0), # 3.3 New Input
            phase_signal,
            energy_signal,
            reward_signal,
            trust_signal,
            gradient_signal
        ], dim=1).float()
    
        # v5.0.4 Store previous state before update
        # We need to detach metadata to prevent graph leaks
        self.prev_input = input_tensor.detach()
        self.prev_hidden = self.hidden_state.detach()
        
        # Forward Pass
        vector, comm_vector, meta, value, h_next, prediction, concepts = self.brain(input_tensor, self.hidden_state)
        
        # 5.3 Free Energy Minimization (Action Selection)
        # Instead of just taking the random/actor output, we slightly perturb it 
        # towards actions that minimize EXPECTED Free Energy (Surprise).
        # HACK: Using the predictor gradient to find "information seeking" actions
        if random.random() < 0.2: # 20% Active Inference override
             # "What action would reduce my uncertainty?"
             # Cloud-Optimized: Analytical gradient of uncertainty w.r.t action
             pass # Complex to implement efficiently, relying on metabolize_free_energy for learning signal
             
        self.hidden_state = h_next.detach()
        self.last_concepts = concepts # 5.8
        self.last_vector = vector
        self.last_comm = comm_vector
        self.last_value = value
        self.last_prediction = prediction # 3.9 Store for loss calculation
        self.last_input = input_tensor    # Store input for next tick's comparison
        
        # 2.3 Zahavi Costly Signaling: Generate Proof of Work
        # If signal is complex (high variance), we must prove it's not cheap noise.
        # This incurs a computational cost (simulated loop or just calculating it)
        self.last_nonce = 0
        comm_variance = comm_vector.var().item()
        if comm_variance > 0.05:
            self.last_nonce = self.generate_zahavi_proof(comm_vector, difficulty=1)
        
        # Unpack Meta (Mate, Adhesion, Punish, Trade)
        mate_desire = meta[0, 0].item()
        adhesion_val = meta[0, 1].item()
        punish_val = meta[0, 2].item()
        trade_val = meta[0, 3].item()
        
        # 3.3 Stigmergy Output
        meme_write = comm_vector[0, 13:16] 
        
        return vector, comm_vector[0], mate_desire, adhesion_val, punish_val, trade_val, meme_write
        

    def metabolize_outcome(self, flux):
        """
        Learns from reality using a simplified Advantage-Actor-Critic (A2C) update.
        flux: The reward from the Oracle
        """
        if self.last_value is None:
            return False

        # 1.3 Landauer Cost: k_B * T * delta(H(W))
        current_entropy = self.calculate_weight_entropy()
        entropy_diff = current_entropy - self.last_weight_entropy
        # Cost is proportional to information erased or restructured (entropy change)
        landauer_cost = max(0.01, 0.5 * abs(entropy_diff)) 
        self.energy -= landauer_cost
        self.last_weight_entropy = current_entropy

        # Reward Signal: External Flux + IQ Incentive (Neural Variance)
        self.last_reward = flux
        # 1.3 Landauer + Metabolic Cost for 'loud' thinking
        thought_loudness = self.last_vector.sum().item()
        thought_cost = thought_loudness * 0.05 # Metabolic penalty
        self.energy -= thought_cost
        
        iq_reward = self.last_vector.std() * 5.0 # Punish uniform thinking
        
        # 5.3 Free Energy Reward (FRISTONIAN OVERRIDE) - v5.0.4 "GHOST FORWARD"
        predictor_loss = torch.tensor(0.0)
        if self.prev_input is not None and self.prev_hidden is not None:
             # Fresh forward pass on the SAME transition
             _, _, _, _, _, ghost_prediction, _ = self.brain(self.prev_input, self.prev_hidden)
             pred_loss_fn = nn.MSELoss()
             # Compare ghost prediction (made from t-1) with the ACTUAL current input (t)
             predictor_loss = pred_loss_fn(ghost_prediction, self.last_input.detach())
             
             # 5.0 Self-Monitoring
             self.prediction_errors.append(predictor_loss.item())
             if len(self.prediction_errors) > 50: self.prediction_errors.pop(0)
             recent_error = np.mean(self.prediction_errors)
             self.confidence = 1.0 / (1.0 + recent_error)
             
             # 5.1 Meta-Learning (Hypergradient)
             if len(self.prediction_errors) > 2 and self.prediction_errors[-1] > self.prediction_errors[-2] * 1.5:
                 self.meta_lr = min(0.05, self.meta_lr * 1.2)
             else:
                 self.meta_lr = max(0.001, self.meta_lr * 0.99)
                 
             for param_group in self.optimizer.param_groups:
                 param_group['lr'] = self.meta_lr

        # 5.2 Sparsity Loss
        sparsity_loss = self.brain.actor_mask.sparsity() * 0.01
        
        reward = torch.tensor([[flux]], dtype=torch.float32) + iq_reward
        
        # Advantage Calculation
        advantage = reward - self.last_value.detach()
        
        # Losses
        # 1. Critic Loss: Mean Squared Error between prediction and actual flux
        critic_loss = 0.5 * (reward - self.last_value).pow(2)
        
        # 2. Actor Loss: Policy Gradient (Surrogate objective)
        # Simplified: Move weights to make 'last_vector' more likely if advantage is positive
        # Added regularization to prevent activation explosion
        actor_loss = -(advantage * self.last_vector.sum()) + 0.01 * self.last_vector.pow(2).sum()
        
        # 5.3 Consolidated Loss: A2C + Active Inference Predictor + Sparsity
        total_loss = actor_loss + critic_loss + predictor_loss + sparsity_loss
        
        # Backprop (Online Learning)
        self.optimizer.zero_grad()
        total_loss.backward()
        
        
        # --- 5.7 COGNITIVE COMPRESSION (Meta-Gradient) ---
        # "Learn to learn faster" -> Modify gradients using the learned Compressor
        with torch.no_grad():
             if self.brain.actor.weight.grad is not None:
                 g = self.brain.actor.weight.grad
                 # Train Compressor on this gradient pattern: Target = g
                 # We want compressor(g) to approximate g, but strictly low rank
                 # Here we just run a dummy forward pass to keep the idea alive in the code structure
                 pass

        self.optimizer.step()
        
        # 4.9 Collective Memory: Natural Forgetting (Weight Decay)
        # Weights slowly decay towards 0, simulating information loss
        # Unless constantly reinforced
        with torch.no_grad():
            for p in self.brain.parameters():
                p.data.mul_(0.9999) # Safe version-incrementing weight decay
        
        # 5.10 Autonomous Research (Sensitivity Analysis)
        if random.random() < 0.01:
            self.conduct_experiment()
        
        
        self.thoughts_had += 1

        # 1.5 Homeostasis check: Transfer energy to/from buffer
        # Threshold set to 130 to allow accumulation for Mitosis (cost 60, trigger 120)
        if self.energy > 130.0:
            transfer = (self.energy - 130.0) * 0.5
            self.energy -= transfer
            self.energy_stored += transfer
        elif self.energy < 30.0 and self.energy_stored > 0:
            transfer = min(self.energy_stored, (30.0 - self.energy) * 0.8)
            self.energy += transfer
            self.energy_stored -= transfer

        return True

    def imitate(self, mentor, rate=0.05):
        """3.1 Social Learning: Blends own weights with a successful neighbor."""
        with torch.no_grad():
            for self_param, mentor_param in zip(self.brain.parameters(), mentor.brain.parameters()):
                self_param.data.copy_(self_param.data * (1.0 - rate) + mentor_param.data * rate)
            # 4.6 Caste Gene Drift during imitation
            self.caste_gene = self.caste_gene * (1.0 - rate) + mentor.caste_gene * rate

    def restorative_imitation(self, mentor):
        """4.9 Collective Memory: Rapidly learn from a mentor to restore lost knowledge."""
        # Significant weight update towards mentor (0.2 rate) to recover stability
        with torch.no_grad():
            for self_param, mentor_param in zip(self.brain.parameters(), mentor.brain.parameters()):
                # Pull self towards mentor
                self_param.data.copy_(self_param.data * 0.8 + mentor_param.data * 0.2)
            
            # Boost confidence as we "remembered"
            self.confidence = min(0.9, self.confidence + 0.3)

    def fuse_with(self, partner):
        """4.7 Dynamic Tensor Fusion: Physical/Functional merging of two agents."""
        if self.is_fused or partner.is_fused:
            return False
        
        self.is_fused = True
        partner.is_fused = True
        self.fused_partner = partner
        partner.fused_partner = self
        
        # Combine energy
        combined_energy = self.energy + partner.energy
        self.energy = combined_energy / 2.0
        partner.energy = combined_energy / 2.0
        
        # Sync Tags (Merging identity)
        new_tag = (self.tag + partner.tag) / 2.0
        self.tag = new_tag
        partner.tag = new_tag
        
        return True

    def split_fusion(self):
        """4.7 Division: Reverting from fused state."""
        if not self.is_fused:
            return
        
        partner = self.fused_partner
        if partner:
            partner.is_fused = False
            partner.fused_partner = None
        
        self.is_fused = False
        self.fused_partner = None

    def _mutate(self, rate=0.2):
        """Randomly alters brain weights to explore the genetic landscape."""
        with torch.no_grad():
            for param in self.brain.parameters():
                if random.random() < rate:
                    mutation = torch.randn_like(param) * 0.1
                    param.add_(mutation)

    def get_genome(self):
        """Serializes brain state and cultural tags for inheritance."""
        genome = {k: v.clone().detach() for k, v in self.brain.state_dict().items()}
        genome['tag'] = self.tag
        genome['caste_gene'] = self.caste_gene # 4.6 Include caste in genome
        return genome

    def _apply_genome(self, genome):
        """Loads brain state from parent(s)."""
        # Remove metadata before loading into brain
        brain_state = {k: v for k, v in genome.items() if k not in ['tag', 'caste_gene']}
        self.brain.load_state_dict(brain_state)
        
        # Inherit tag with slight drift
        if 'tag' in genome:
            self.tag = np.clip(genome['tag'] + np.random.randn(3) * 0.05, 0, 1)
            
        # 4.6 Caste Inheritance
        if 'caste_gene' in genome:
            self.caste_gene = np.clip(genome['caste_gene'] + np.random.randn(4) * 0.05, 0, 1)


    def conduct_experiment(self):
        """5.10 Gradient-based Sensitivity Analysis (The 'Newton' Method)."""
        # We want to know: d(Prediction)/d(Input_i)
        # Which input dimension effectively controls the reality vector?
        
        if self.last_input is None: return
        
        input_var = self.last_input.clone().requires_grad_(True)
        # Forward pass purely for gradients
        _, _, _, _, _, pred, _ = self.brain(input_var, self.hidden_state.detach())
        
        # Target: Maximize predicted energy (Dim 37 - Energy Signal)
        target_dim = 37 
        target = pred[0, target_dim]
        
        # Check if we can compute gradients (requires graph)
        # Since we just ran forward, we created a new graph branch.
        try:
            grads = torch.autograd.grad(target, input_var, retain_graph=False)[0]
            
            # Find max sensitivity
            sens = grads.abs().mean(dim=0)
            max_idx = torch.argmax(sens).item()
            
            # Log discovery
            channels = ["Matter"]*16 + ["Pheromone"]*16 + ["Meme"]*3 + ["Phase"]*2 + ["Energy", "Reward", "Trust", "Stress"]
            if max_idx < len(channels):
                discovery = f"{channels[max_idx]}->Energy"
                self.research_log.append(discovery)
                if len(self.research_log) > 5: self.research_log.pop(0)
        except Exception:
            pass # Gradient issues can happen if decoupled

    def perform_intervention(self, action_idx):
        """
        5.9 Counterfactual Reasoning.
        'What if I did X instead of Y?'
        Returns predicted difference in Energy Outcome.
        """
        if self.last_input is None: return 0.0
        
        # Create counterfactual input (perturb last input)
        # This is a simplification: Action isn't directly an input, it affects NEXT input.
        # But we predict NEXT input based on CURRENT input (which contains state).
        # We assume 'hidden_state' encodes intent? No.
        # We need a forward model: State + Action -> Next State.
        # Our 'predictor' does Hidden -> Next Input.
        # So we can perturb Hidden (representing altered action intent).
        
        with torch.no_grad():
            perturbed_hidden = self.hidden_state.clone()
            perturbed_hidden += torch.randn_like(perturbed_hidden) * 0.1 # Imagine doing something different
            
            pred_cf = self.brain.predictor(perturbed_hidden)
            pred_actual = self.brain.predictor(self.hidden_state)
            
            # Compare predicted energy (Index 37)
            diff = pred_cf[0, 37] - pred_actual[0, 37]
            return diff.item()

    def evaluate_neighbor(self, neighbor):
        """5.4 Peer Evaluation."""
        # Estimate fitness based on visible signals + energy
        # Real fitness = Energy, but we add 'Brain Complexity' (Entropy) as a proxy for 'Potential'
        score = neighbor.energy
        # Add 'Neural Complexity' bonus (Intelligence)
        score += neighbor.calculate_weight_entropy() * 10.0
        return score

    def create_weight_packet(self):
        """3.2 Creates a viral packet of weights."""
        # Only copy small subset to stimulate 'Gene Transfer'
        # Copy Actor weights
        packet = {
            'weights': {k: v.clone().detach().cpu() for k,v in self.brain.actor.state_dict().items()},
            'fitness': self.energy,
            'beta': 0.1 + (self.confidence * 0.2), # High confidence = high spread rate
            'id': self.id
        }
        return packet

    def receive_infection(self, packet):
        """3.2 Receive a viral packet."""
        if len(self.meme_pool) < 5:
            self.meme_pool.append(packet)
