# flappy_bird

Replicate the flappy bird game with Python that can be played by human and AI players trained with reinforcement learning

# Algorithms
Two reinforcement learning algorithms implemented:
1. Standard Q-learning, where state is defined as the quantified position of the bird and its vertical speed
2. Feature Q-learning, or approximate Q-learning, where 3 features are used: <br>
  a) distance to the center of the scene<br>
  b) distance to the gap (20% from the bottom) when the bird is not in the gap<br>
  c) same as b) except when the bird is in the gap<br>

# Manual play
python flappy_bird.py

# Run Standard Q-learning:
python trainer.py <br><br>
A list of options is presented, including:<br>
a) Enter Return to run an user interactive training<br>
b) Enter a number to run this number of training sessions silently<br>
c) Enter p to let the AI play the game using learned Q-table, stored in the data folder<br><br>
Typically a few thousand training sessions are needed in order for the AI to perform well. With the Q-table committed, it can score over 500.

# Run Feature Q-learning:
python feature_trainer.py<br><br>
A list of options is presented, including:<br>
a) Enter Return to run an user interactive training<br>
b) Enter p to let the AI play using learned weights to the features.<br><br>
The idea is to let the AI learn to fly in the middle.<br>
Only a couple of training sessions are needed, therefore no silent mass training is provided. <br>
Learned weights can be stored in data/feature_weights.<br>
A copy is committed. With it, the AI can score thousands, and probably will never die.
