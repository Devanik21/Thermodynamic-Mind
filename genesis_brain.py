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
    Input: [Local Matter Signal (16) + Scent (1)] = 17 Dimensions
    Hidden: 32 (GRU State)
    Output: 21 (Reality Vector) + 3 (Emit, Mate, Adhesion) + 1 (Critic)
    """
    def __init__(self, input_dim=19, hidden_dim=32, output_dim=21):
        super().__init__()
        self.hidden_dim = hidden_dim
        
        # Encoder: Project sensory data to hidden space
        self.encoder = nn.Linear(input_dim, hidden_dim)
        
        # Temporal Memory: GRU Cell for sequential reasoning
        self.gru = nn.GRUCell(hidden_dim, hidden_dim)
        
        # Action Head: The Reality Vector (Casting Spells)
        self.actor = nn.Linear(hidden_dim, output_dim)
        
        # Meta Head: Social/Biological behaviors (Emit Scent, Mate Desire, Adhesion)
        self.meta = nn.Linear(hidden_dim, 3)
        
        # Critic Head: Internal Value estimation (for learning)
        self.critic = nn.Linear(hidden_dim, 1)
        
        # Initialize weights for high initial variance (exploration)
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0.0)

    def forward(self, x, hidden):
        # x: [1, 17]
        # hidden: [1, 32]
        h_enc = torch.relu(self.encoder(x))
        h_next = self.gru(h_enc, hidden)
        
        vector = torch.tanh(self.actor(h_next))
        meta = torch.sigmoid(self.meta(h_next))
        value = self.critic(h_next)
        
        return vector, meta, value, h_next

# ============================================================
# 🤖 THE AGENT
# ============================================================
class GenesisAgent:
    def __init__(self, x, y, genome=None, generation=0):
        self.id = str(uuid.uuid4())
        self.x = x
        self.y = y
        self.generation = generation
        self.age = 0
        self.energy = 80.0
        self.inventions = []
        
        # Performance Metrics
        self.thoughts_had = 0
        self.reflexes_used = 0
        
        # 1.5 Homeostatic Regulation
        self.energy_stored = 20.0  # Long-term buffer
        self.energy = 60.0        # Operational energy (Short-term)
        
        # 1.6 Circadian Rhythms
        self.internal_phase = random.random() * 2 * np.pi
        
        # Neural State
        self.brain = GenesisBrain()
        self.optimizer = optim.Adam(self.brain.parameters(), lr=0.005)
        self.hidden_state = torch.zeros(1, 32)
        
        # Memory for learning
        self.last_vector = None
        self.last_value = None
        self.last_log_prob = None
        self.last_weight_entropy = self.calculate_weight_entropy()
        
        # If born from parents, inherit genome
        if genome:
            self._apply_genome(genome)

    def calculate_weight_entropy(self):
        """1.3 Landauer Metric: Shannon entropy of the brain's weight distribution."""
        with torch.no_grad():
            all_weights = torch.cat([p.view(-1) for p in self.brain.parameters()])
            # Simple histogram-based entropy
            hist = torch.histc(all_weights, bins=20, min=-2, max=2)
            prob = hist / (hist.sum() + 1e-8)
            entropy = -torch.sum(prob * torch.log2(prob + 1e-8))
            return entropy.item()

    def decide(self, signal_16, smell_intensity=0.0, env_phase=0.0):
        self.age += 1
        
        # 1.6 Synchronization: Update internal phase
        # Agents slowly drift towards environmental phase
        self.internal_phase += 0.1 * np.sin(env_phase - self.internal_phase)
        
        # Prepare Input (Add internal phase as temporal context)
        phase_signal = torch.tensor([[np.sin(self.internal_phase), np.cos(self.internal_phase)]])
        input_tensor = torch.cat([
            signal_16.unsqueeze(0), 
            torch.tensor([[smell_intensity]]),
            phase_signal
        ], dim=1).float()
        
        # Forward Pass
        vector, meta, value, h_next = self.brain(input_tensor, self.hidden_state)
        
        # Update Hidden State
        self.hidden_state = h_next.detach()
        self.last_vector = vector
        self.last_value = value
        
        # Unpack Meta Output
        emit_val = meta[0, 0].item()
        mate_desire = meta[0, 1].item()
        adhesion_val = meta[0, 2].item()
        
        return vector, emit_val, mate_desire, adhesion_val

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
        """Serializes brain state for inheritance."""
        return {k: v.clone().detach() for k, v in self.brain.state_dict().items()}

    def _apply_genome(self, genome):
        """Loads brain state from parent(s)."""
        self.brain.load_state_dict(genome)
