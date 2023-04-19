export CUDA_VISIBLE_DEVICES=0
export XLA_PYTHON_CLIENT_PREALLOCATE=false
export DISPLAY=:0

ENV="--env ../../env/Walker.x86_64"
RL="--learning_rate 0.00005"
TRAIN="--steps 1e6 --buffer_size 1e6 --batch 64 --target_update_tau 1e-3 --learning_starts 5000 --gradient_steps 10"
MODEL="--node 512 --hidden_n 3"
OPTIONS="--n_support 25 --time_scale 20 --mixture truncated --quantile_drop 0.05 --cvar 0.3"
OPTIMIZER="--optimizer adam"
python  run_dpg.py --algo TD3 $ENV $RL $TRAIN $MODEL $OPTIMIZER $OPTIONS --worker_id 1 &
export CUDA_VISIBLE_DEVICES=1
python  run_dpg.py --algo SAC $ENV $RL $TRAIN $MODEL $OPTIMIZER $OPTIONS --worker_id 2
export CUDA_VISIBLE_DEVICES=0
python  run_dpg.py --algo TD4_QR $ENV $RL $TRAIN $MODEL $OPTIMIZER $OPTIONS --worker_id 3 &
export CUDA_VISIBLE_DEVICES=1
python  run_dpg.py --algo TQC $ENV $RL $TRAIN $MODEL $OPTIMIZER $OPTIONS --worker_id 4
export CUDA_VISIBLE_DEVICES=0
python  run_dpg.py --algo TD4_IQN $ENV $RL $TRAIN $MODEL $OPTIMIZER $OPTIONS --worker_id 5 &
export CUDA_VISIBLE_DEVICES=1
python  run_dpg.py --algo TQC_IQN $ENV $RL $TRAIN $MODEL $OPTIMIZER $OPTIONS