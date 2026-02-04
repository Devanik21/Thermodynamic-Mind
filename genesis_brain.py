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
    def __init__(self, input_dim=17, hidden_dim=32, output_dim=21):
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
        
        # Neural State
        self.brain = GenesisBrain()
        self.optimizer = optim.Adam(self.brain.parameters(), lr=0.005)
        self.hidden_state = torch.zeros(1, 32)
        
        # Memory for learning
        self.last_vector = None
        self.last_value = None
        self.last_log_prob = None
        
        # If born from parents, inherit genome
        if genome:
            self._apply_genome(genome)

    def decide(self, signal_16, smell_intensity=0.0):
        self.age += 1
        
        # Prepare Input
        input_tensor = torch.cat([signal_16.unsqueeze(0), torch.tensor([[smell_intensity]])], dim=1).float()
        
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
        actor_loss = -(advantage * self.last_vector.sum()) # Crude approximation for demonstration
        
        total_loss = actor_loss + critic_loss
        
        # Backprop (Online Learning)
        self.optimizer.zero_grad()
        total_loss.backward()
        self.optimizer.step()
        
        self.thoughts_had += 1
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
