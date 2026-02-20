from rlcard.envs import make
from rlcard.agents.dqn_agent import DQNAgent
from rlcard.games.ctpinochle.utils.action_event import ActionEvent, PassBid, BidAction, PlayCardAction, SelectTrumpAction

import os
import numpy as np
import argparse 
import torch 
import rlcard 
from rlcard.utils import get_device, set_seed, tournament, reorganize, Logger, plot_curve

import time
# For evaluating how long it takes to run when testing on hpc
start = time.time()

def train(args):
    # Set up rl environment for training 
    env = rlcard.make(
        'ctpinochle',
        config={
            'seed': args.seed,
            'allow_step_back': False
        }
    )
    eval_env = rlcard.make(
        'ctpinochle',
        config={
            'seed': args.seed+1,
            'allow_step_back': False
        }
    )

    set_seed(args.seed)
    device = get_device()
    print(f'Using device: {device}')

    # Set up the agenta
    # See ctpinochle.py for state breakdown
    STATE_SHAPE = [env.state_shape[0][1]]
    print(f'State shape: {STATE_SHAPE}')
    NUM_ACTIONS = env.num_actions #83

    agents = []
    for i in range(env.num_players): 
        agent = DQNAgent(num_actions=NUM_ACTIONS,
                         state_shape=STATE_SHAPE,
                         mlp_layers=args.mlp_layers,
                         device=device,
                         replay_memory_size=args.memory_size,
                         replay_memory_init_size=args.memory_init_size,
                         update_target_estimator_every=args.update_every,
                         discount_factor=args.gamma,
                         epsilon_start=args.epsilon_start,
                         epsilon_end=args.epsilon_end,
                         epsilon_decay_steps=args.epsilon_decay_steps,
                         batch_size=args.batch_size,
                         learning_rate=args.lr,
                         train_every=args.train_every,
                         save_path=args.save_dir,
                         save_every=args.save_every)
        agents.append(agent)
    
    env.set_agents(agents)
    eval_env.set_agents(agents)

    # Set up logging information
    os.makedirs(args.log_dir, exist_ok=True)
    os.makedirs(args.save_dir, exist_ok=True)

    with Logger(args.log_dir) as logger:
        for episode in range(args.num_episodes):

            # Run for on episode and collect transitions
            trajectories, payoffs = env.run(is_training=True)

            trajectories = reorganize(trajectories, payoffs)

            # Feed transitions to each agents replay buffer
            for i in range(env.num_players):
                for transition in trajectories[i]:
                    agents[i].feed(transition)
            
            # evaluate it periodically
            if episode % args.eval_every == 0:
                logger.log_performance(
                    episode,
                    tournament(eval_env, args.eval_num)[0] # avg payoff of player 0
                )
            
            # plot training curve
            csv_path, fig_path = logger.csv_path, logger.fig_path
        
        plot_curve(csv_path, fig_path, algorithm='DQN')
        print(f'\nTraining complete. Results saved to args.log_dir')

        # Save final checkpoints
        for i, agent in enumerate(agents):
            agent.save_checkpoint(path=args.save_dir, filename = f'checkpoint_dqn_player{i}.pt')
        print(f'Checkpoints saved to {args.save_dir}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser('CTPinochle DQN Training')

    # Training
    parser.add_argument('--num_episodes',        type=int,   default=1)
    parser.add_argument('--eval_every',          type=int,   default=1)
    parser.add_argument('--eval_num',            type=int,   default=1_000,
                        help='Number of games to average over during evaluation')
    parser.add_argument('--seed',                type=int,   default=42)

    # DQN Hyperparameters
    parser.add_argument('--lr',                  type=float, default=0.00005)
    parser.add_argument('--gamma',               type=float, default=0.99)
    parser.add_argument('--batch_size',          type=int,   default=32)
    parser.add_argument('--memory_size',         type=int,   default=20_000)
    parser.add_argument('--memory_init_size',    type=int,   default=1_000)
    parser.add_argument('--train_every',         type=int,   default=1)
    parser.add_argument('--update_every',        type=int,   default=1_000,
                        help='Steps between copying Q-net weights to target net')
    parser.add_argument('--epsilon_start',       type=float, default=1.0)
    parser.add_argument('--epsilon_end',         type=float, default=0.1)
    parser.add_argument('--epsilon_decay_steps', type=int,   default=20_000)

    # Network Architecture
    parser.add_argument('--mlp_layers',          type=int,   nargs='+', default=[256, 256, 128],
                        help='Hidden layer sizes for the Q-network MLP')

    # I/O
    parser.add_argument('--log_dir',             type=str,   default='./logs/dqn_ctpinochle')
    parser.add_argument('--save_dir',            type=str,   default='./checkpoints/dqn_ctpinochle')
    parser.add_argument('--save_every',          type=int,   default=10_000)

    args = parser.parse_args()
    train(args)
    print(f"Execution time: {time.time() - start:.2f} seconds")
