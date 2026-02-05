import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import random
import uuid

# ============================================================
# 🧬 NEURAL ARCHITECTURE
# ============================================================
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
        self.comm_out = nn.Linear(hidden_dim, 16) # Social Signaling Layer
        self.meta_out = nn.Linear(hidden_dim, 4) # [Mate, Adhesion, Punish, Trade]
        self.critic = nn.Linear(hidden_dim, 1) # Value function for RL
        
        # 3.9 Narrative Memory (Predictive Processing)
        # Predicts the NEXT input state (Self-Supervised Learning)
        self.predictor = nn.Linear(hidden_dim, input_dim) 
        
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
        
        vector = torch.relu(self.actor(last_hidden))    # Reality Vector (Flux)
        comm = torch.sigmoid(self.comm_out(last_hidden)) # Signal Vector (Pheromones/Memes)
        meta = torch.sigmoid(self.meta_out(last_hidden)) # [Mate, Adhesion, Punish, Trade]
        value = self.critic(last_hidden)               # Estimated Value
        prediction = self.predictor(last_hidden)       # 3.9 Predicted Next State
        
        return vector, comm, meta, value, h_next, prediction

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
        
        # 1.6 Circadian Rhythms
        self.internal_phase = random.random() * 2 * np.pi
        
        # Neural State
        self.brain = GenesisBrain()
        self.optimizer = optim.Adam(self.brain.parameters(), lr=0.005)
        
        # 3.0 Epigenetic Memory: Inherit mental state
        if parent_hidden is not None:
            self.hidden_state = parent_hidden.detach().clone() + torch.randn_like(parent_hidden) * 0.1
        else:
            self.hidden_state = torch.zeros(1, 64)
        
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
    
        # Forward Pass
        vector, comm_vector, meta, value, h_next, prediction = self.brain(input_tensor, self.hidden_state)
        
        self.hidden_state = h_next.detach()
        self.last_vector = vector
        self.last_comm = comm_vector
        self.last_value = value
        self.last_prediction = prediction # 3.9 Store for loss calculation
        self.last_input = input_tensor    # Store input for next tick's comparison
        
        # Unpack Meta (Mate, Adhesion, Punish, Trade)
        mate_desire = meta[0, 0].item()
        adhesion_val = meta[0, 1].item()
        punish_val = meta[0, 2].item()
        trade_val = meta[0, 3].item()
        
        # 3.3 Stigmergy Output
        meme_write = comm_vector[13:16] 
        
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
        iq_reward = self.last_vector.std() * 5.0 # Punish uniform thinking
        reward = torch.tensor([[flux]], dtype=torch.float32) + iq_reward
        
        # Advantage Calculation
        advantage = reward - self.last_value.detach()
        
        # Losses
        # 1. Critic Loss: Mean Squared Error between prediction and actual flux
        critic_loss = 0.5 * (reward - self.last_value).pow(2)
        
        # 2. Actor Loss: Policy Gradient (Surrogate objective)
        # Simplified: Move weights to make 'last_vector' more likely if advantage is positive
        actor_loss = -(advantage * self.last_vector.sum()) 
        
        total_loss = actor_loss + critic_loss
        
        # Backprop (Online Learning)
        self.optimizer.zero_grad()
        total_loss.backward()
        self.optimizer.step()
        
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
        return genome

    def _apply_genome(self, genome):
        """Loads brain state from parent(s)."""
        # Remove metadata before loading into brain
        brain_state = {k: v for k, v in genome.items() if k != 'tag'}
        self.brain.load_state_dict(brain_state)
