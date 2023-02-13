export CUDA_VISIBLE_DEVICES=0
export SDL_VIDEODRIVER=dummy
python run_qnet.py --algo DQN --env BreakoutNoFrameskip-v4 --learning_rate 0.0003 --steps 1e6 --batch 128 --train_freq 1 --target_update 1000 --node 512 --hidden_n 1 --final_eps 0.05 --learning_starts 1000 --gamma 0.99 --buffer_size 5e5 --exploration_fraction 0.6 --clip_rewards
python run_qnet.py --algo C51 --env BreakoutNoFrameskip-v4 --learning_rate 0.0003 --steps 1e6 --batch 128 --train_freq 1 --target_update 1000 --node 512 --hidden_n 1 --final_eps 0.05 --learning_starts 1000 --gamma 0.99 --buffer_size 5e5 --exploration_fraction 0.6 --min 0 --max 30 --clip_rewards
python run_qnet.py --algo QRDQN --env BreakoutNoFrameskip-v4 --learning_rate 0.0003 --steps 1e6 --batch 128 --train_freq 1 --target_update 1000 --node 512 --hidden_n 1 --final_eps 0.05 --learning_starts 1000 --gamma 0.99 --buffer_size 5e5 --exploration_fraction 0.6 --n_support 128 --delta 0.01 --clip_rewards
python run_qnet.py --algo IQN --env BreakoutNoFrameskip-v4 --learning_rate 0.0003 --steps 1e6 --batch 128 --train_freq 1 --target_update 1000 --node 512 --hidden_n 1 --final_eps 0.05 --learning_starts 1000 --gamma 0.99 --buffer_size 5e5 --exploration_fraction 0.6 --n_support 128 --delta 0.01 --clip_rewards