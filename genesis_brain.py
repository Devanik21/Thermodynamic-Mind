import torch
import torch.nn as nn
import torch.optim as optim
import random
import uuid

# ============================================================
# 🧠 THERMODYNAMIC CONSTANTS
# ============================================================
COST_REFLEX = 0.1      # Cheap: Just reacting
COST_THOUGHT = 5.0     # Expensive: Rewiring the synapses (Backprop)
LEARNING_THRESHOLD = 0.6 # Confidence needed to trigger Neuroplasticity

# ============================================================
# 🕸️ THE NEURAL SUBSTRATE (InstinctNet)
# ============================================================
class InstinctNet(nn.Module):
    """
    A tiny, efficient brain.
    Input: Sensory Vector (16) + Energy State (1) = 17
    Output: Action Logits (6) + Plasticity Request (1)
    """
    def __init__(self, input_dim=16, hidden_dim=32, output_dim=6):
        super().__init__()
        self.layer1 = nn.Linear(input_dim + 1, hidden_dim)
        self.layer2 = nn.Linear(hidden_dim, hidden_dim)
        
        # Head 1: The Motor Cortex (Actions)
        self.actor = nn.Linear(hidden_dim, output_dim)
        
        # Head 2: The Metacognition (Should I Learn?)
        # 0 = Habitual Mode, 1 = Learning Mode
        self.critic = nn.Linear(hidden_dim, 1)
        
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x, energy_level):
        # Concatenate Signal with Internal State (Proprioception)
        # Normalize energy (0-100 -> 0-1)
        e = torch.tensor([energy_level / 100.0]).float()
        if x.dim() == 1:
            x = torch.cat([x, e], dim=0)
        else:
            e = e.unsqueeze(0).expand(x.size(0), -1)
            x = torch.cat([x, e], dim=1)
            
        h = self.relu(self.layer1(x))
        h = self.relu(self.layer2(h))
        
        action_logits = self.actor(h)
        plasticity_gate = self.sigmoid(self.critic(h))
        
        return action_logits, plasticity_gate

# ============================================================
# 🧬 THE AGENT (The Thermodynamic Being)
# ============================================================
class GenesisAgent:
    def __init__(self, x, y, uid=None):
        self.id = uid if uid else str(uuid.uuid4())[:8]
        self.x = x
        self.y = y
        self.energy = 50.0 # Start half-full
        self.age = 0
        self.generation = 0
        
        # The Brain
        self.brain = InstinctNet()
        self.optimizer = optim.Adam(self.brain.parameters(), lr=0.01)
        
        # Short-term Memory for RL
        self.saved_log_probs = []
        self.rewards = []
        self.decided_to_learn = False
        
        # Stats
        self.thoughts_had = 0      # Times it chose backprop
        self.reflexes_used = 0     # Times it acted cheaply
    
    def decide(self, signal_vector):
        """
        The Moment of Choice: Habit or Thought?
        """
        # 1. Forward Pass (Reflex) - Cheap
        self.energy -= COST_REFLEX 
        self.reflexes_used += 1
        
        with torch.no_grad(): # Default to cheap inference
             # We temporarily re-enable grad later if we decide to learn
             pass

        logits, plasticity_score = self.brain(signal_vector, self.energy)
        
        # Sample Action
        probs = torch.nn.functional.softmax(logits, dim=0)
        distribution = torch.distributions.Categorical(probs)
        action = distribution.sample()
        
        # Store for potential learning
        self.current_log_prob = distribution.log_prob(action)
        self.decided_to_learn = False
        
        # 2. Metacognition: Do we spend energy to learn this interaction?
        # Only learn if:
        # A) The brain 'wants' to (Plasticity Score high)
        # B) We have surplus energy (Can afford the proteins)
        if plasticity_score.item() > LEARNING_THRESHOLD and self.energy > 20.0:
            self.decided_to_learn = True
        
        return action.item()

    def metabolize_outcome(self, reward):
        """
        The consequences of action.
        If we decided to learn, we now pay the price and rewire.
        """
        # Physical Reward
        # reward is from Physics (Calories)
        
        # 3. Neuroplasticity (Thought) - Expensive
        if self.decided_to_learn:
            self.energy -= COST_THOUGHT
            self.thoughts_had += 1
            
            # REINFORCE Update (Simple Policy Gradient)
            # We want to maximize Reward
            loss = -self.current_log_prob * reward
            
            # We need to re-run forward pass with gradients enabled to backprop
            # Since we didn't save the graph (to save memory/energy normally)
            # This is the "Re-thinking" cost
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            return True # Learned
            
        return False # Just lived
