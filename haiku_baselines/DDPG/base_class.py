import gym
import jax
import jax.numpy as jnp
import haiku as hk
import numpy as np

from tqdm.auto import trange
from collections import deque

from haiku_baselines.common.base_classes import TensorboardWriter, save, restore, select_optimizer
from haiku_baselines.common.cpprb_buffers import ReplayBuffer, PrioritizedReplayBuffer
from haiku_baselines.common.utils import convert_states
from haiku_baselines.common.worker import gymMultiworker

from mlagents_envs.environment import UnityEnvironment, ActionTuple

class Deteministic_Policy_Gradient_Family(object):
    def __init__(self, env, gamma=0.99, learning_rate=5e-5, buffer_size=50000, train_freq=1, gradient_steps=1, batch_size=32,
                 n_step = 1, learning_starts=1000, target_network_update_tau=2e-4, prioritized_replay=False,
                 prioritized_replay_alpha=0.6, prioritized_replay_beta0=0.4, prioritized_replay_eps=1e-6,
                 log_interval=200, tensorboard_log=None, _init_setup_model=True, policy_kwargs=None, 
                 full_tensorboard_log=False, seed=None, optimizer = 'adamw'):
        
        self.env = env
        self.log_interval = log_interval
        self.policy_kwargs = policy_kwargs
        self.seed = 42 if seed is None else seed
        self.key_seq = hk.PRNGSequence(self.seed)
        
        self.learning_starts = learning_starts
        self.train_freq = train_freq
        self.gradient_steps = gradient_steps
        self.prioritized_replay = prioritized_replay
        self.prioritized_replay_eps = prioritized_replay_eps
        self.batch_size = batch_size
        self.target_network_update_tau = target_network_update_tau
        self.prioritized_replay_alpha = prioritized_replay_alpha
        self.prioritized_replay_beta0 = prioritized_replay_beta0
        self.buffer_size = buffer_size
        self.learning_rate = learning_rate
        self.gamma = gamma
        self._gamma = self.gamma**n_step #n_step gamma
        self.tensorboard_log = tensorboard_log
        self.full_tensorboard_log = full_tensorboard_log
        self.n_step_method = (n_step > 1)
        self.n_step = n_step
        
        self.params = None
        self.target_params = None
        self.save_path = None
        self.optimizer = select_optimizer(optimizer,self.learning_rate,1e-2/self.batch_size)
        
        self.get_env_setup()
        self.get_memory_setup()
        
    def save_params(self, path):
        save(path, self.params)
            
    def load_params(self, path):
        self.params = self.target_params = restore(path)
        
    def get_env_setup(self):
        print("----------------------env------------------------")
        if isinstance(self.env,UnityEnvironment):
            print("unity-ml agent environmet")
            self.env.reset()
            group_name = list(self.env.behavior_specs.keys())[0]
            group_spec = self.env.behavior_specs[group_name]
            self.env.step()
            dec, term = self.env.get_steps(group_name)
            self.group_name = group_name
            
            self.observation_space = [list(spec.shape) for spec in group_spec.observation_specs]
            self.action_size = [branch for branch in group_spec.action_spec.continuous_size]
            self.worker_size = len(dec.agent_id)
            self.env_type = "unity"
            
        elif isinstance(self.env,gym.Env) or isinstance(self.env,gym.Wrapper):
            print("openai gym environmet")
            action_space = self.env.action_space
            observation_space = self.env.observation_space
            self.observation_space = [list(observation_space.shape)]
            self.action_size = [action_space.low.shape[0]]
            self.worker_size = 1
            self.env_type = "gym"
            
        elif isinstance(self.env,gymMultiworker):
            print("gymMultiworker")
            env_info = self.env.env_info
            self.observation_space = [list(env_info['observation_space'].shape)]
            self.action_size = [env_info['action_space'].n]
            self.worker_size = self.env.worker_num
            self.env_type = "gymMultiworker"
    
        print("observation size : ", self.observation_space)
        print("action size : ", self.action_size)
        print("worker_size : ", self.worker_size)
        print("-------------------------------------------------")
        
    def get_memory_setup(self):
        if not self.prioritized_replay:
            self.replay_buffer = ReplayBuffer(self.buffer_size,self.observation_space, self.worker_size, self.action_size, self.n_step, self.gamma)
        else:
            self.replay_buffer = PrioritizedReplayBuffer(self.buffer_size,self.observation_space,self.prioritized_replay_alpha, self.worker_size, self.action_size, self.n_step, self.gamma)
    
    def setup_model(self):
        pass
    
    def _train_step(self, steps):
        pass
    
    def _get_actions(self, params, obses) -> np.ndarray:
        pass
    
    def actions(self,obs,steps):
        pass

        
    def learn(self, total_timesteps, callback=None, log_interval=1000, tb_log_name="Q_network",
              reset_num_timesteps=True, replay_wrapper=None):
        if self.n_step_method:
            tb_log_name = "{}Step_".format(self.n_step) + tb_log_name
        if self.prioritized_replay:
            tb_log_name = tb_log_name + "+PER"
        
        pbar = trange(total_timesteps, miniters=log_interval)
        with TensorboardWriter(self.tensorboard_log, tb_log_name) as (self.summary, self.save_path):
            if self.env_type == "unity":
                self.learn_unity(pbar, callback, log_interval)
            if self.env_type == "gym":
                self.learn_gym(pbar, callback, log_interval)
            if self.env_type == "gymMultiworker":
                self.learn_gymMultiworker(pbar, callback, log_interval)
            self.save_params(self.save_path)
    
    def discription(self):
        return "score : {:.3f}, loss : {:.3f} |".format(
                                    np.mean(self.scoreque),np.mean(self.lossque)
                                    )
    
    def learn_unity(self, pbar, callback=None, log_interval=100):
        self.env.reset()
        self.env.step()
        dec, term = self.env.get_steps(self.group_name)
        self.scores = np.zeros([self.worker_size])
        self.eplen = np.zeros([self.worker_size])
        self.scoreque = deque(maxlen=10)
        self.lossque = deque(maxlen=10)
        obses = convert_states(dec.obs)
        for steps in pbar:
            self.eplen += 1
            actions = self.actions(obses,steps)
            action_tuple = ActionTuple(continuous=actions)
            old_obses = obses

            self.env.set_actions(self.group_name, action_tuple)
            self.env.step()
            
            if steps > self.learning_starts and steps % self.train_freq == 0: #train in step the environments
                loss = self.train_step(steps,self.gradient_steps)
                self.lossque.append(loss)
            
            dec, term = self.env.get_steps(self.group_name)
            term_ids = list(term.agent_id)
            term_obses = convert_states(term.obs)
            term_rewards = list(term.reward)
            term_done = list(term.interrupted)
            while len(dec) == 0:
                self.env.step()
                dec, term = self.env.get_steps(self.group_name)
                if len(term.agent_id) > 0:
                    term_ids += list(term.agent_id)
                    newterm_obs = convert_states(term.obs)
                    term_obses = [np.concatenate((to,o),axis=0) for to,o in zip(term_obses,newterm_obs)]
                    term_rewards += list(term.reward)
                    term_done += list(term.interrupted)
            obses = convert_states(dec.obs)
            nxtobs = [np.copy(o) for o in obses]
            done = np.full((self.worker_size),False)
            terminal = np.full((self.worker_size),False)
            reward = dec.reward
            term_on = len(term_ids) > 0
            if term_on:
                term_ids = np.asarray(term_ids)
                term_rewards = np.asarray(term_rewards)
                term_done = np.asarray(term_done)
                for n,t in zip(nxtobs,term_obses):
                    n[term_ids] = t
                done[term_ids] = ~term_done
                terminal[term_ids] = True
                reward[term_ids] = term_rewards
            self.scores += reward
            self.replay_buffer.add(old_obses, actions, reward, nxtobs, done, terminal)
            if term_on:
                if self.summary:
                    self.summary.add_scalar("env/episode_reward", np.mean(self.scores[term_ids]), steps)
                    self.summary.add_scalar("env/episode len",np.mean(self.eplen[term_ids]),steps)
                    self.summary.add_scalar("env/time over",np.mean(1 - done[term_ids].astype(np.float32)),steps)
                self.scoreque.extend(self.scores[term_ids])
                self.scores[term_ids] = 0
                self.eplen[term_ids] = 0
            
            if steps % log_interval == 0 and len(self.scoreque) > 0 and len(self.lossque) > 0:
                pbar.set_description(self.discription())
        
    def learn_gym(self, pbar, callback=None, log_interval=100):
        state = [np.expand_dims(self.env.reset(),axis=0)]
        self.scores = np.zeros([self.worker_size])
        self.eplen = np.zeros([self.worker_size])
        self.scoreque = deque(maxlen=10)
        self.lossque = deque(maxlen=10)
        for steps in pbar:
            self.eplen += 1
            actions = self.actions(state,steps)
            next_state, reward, terminal, info = self.env.step(actions[0])
            next_state = [np.expand_dims(next_state,axis=0)]
            done = terminal
            if "TimeLimit.truncated" in info:
                done = not info["TimeLimit.truncated"]
            self.replay_buffer.add(state, actions, reward, next_state, done, terminal)
            self.scores[0] += reward
            state = next_state
            if terminal:
                self.scoreque.append(self.scores[0])
                if self.summary:
                    self.summary.add_scalar("env/episode_reward", self.scores[0], steps)
                    self.summary.add_scalar("env/episode len",self.eplen[0],steps)
                    self.summary.add_scalar("env/time over",float(not done),steps)
                self.scores[0] = 0
                self.eplen[0] = 0
                state = [np.expand_dims(self.env.reset(),axis=0)]
                
            if steps > self.learning_starts and steps % self.train_freq == 0:
                loss = self.train_step(steps,self.gradient_steps)
                self.lossque.append(loss)
            
            if steps % log_interval == 0 and len(self.scoreque) > 0 and len(self.lossque) > 0:
                pbar.set_description(self.discription())
                
    def learn_gymMultiworker(self, pbar, callback=None, log_interval=100):
        state,_,_,_,_,_ = self.env.get_steps()
        self.scores = np.zeros([self.worker_size])
        self.eplen = np.zeros([self.worker_size])
        self.scoreque = deque(maxlen=10)
        self.lossque = deque(maxlen=10)
        for steps in pbar:
            self.eplen += 1
            actions = self.actions([state],steps)
            self.env.step(actions)

            if steps > self.learning_starts and steps % self.train_freq == 0:
                loss = self.train_step(steps,self.gradient_steps)
                self.lossque.append(loss)
            
            next_states,rewards,dones,terminals,end_states,end_idx = self.env.get_steps()
            nxtstates = np.copy(next_states)
            if end_states is not None:
                nxtstates[end_idx] = end_states
                if self.summary:
                    self.summary.add_scalar("env/episode_reward", np.mean(self.scores[end_idx]), steps)
                    self.summary.add_scalar("env/episode len",np.mean(self.eplen[end_idx]),steps)
                    self.summary.add_scalar("env/time over",np.mean(1 - dones[end_idx].astype(np.float32)),steps)
                self.scoreque.extend(self.scores[end_idx])
                self.scores[end_idx] = 0
                self.eplen[end_idx] = 0
            self.replay_buffer.add([state], actions, rewards, [nxtstates], dones, terminals)
            self.scores += rewards
            state = next_states
            
            if steps % log_interval == 0 and len(self.scoreque) > 0 and len(self.lossque) > 0:
                pbar.set_description(self.discription())
    
    def test(self, episode = 10, tb_log_name=None):
        if tb_log_name is None:
            tb_log_name = self.save_path
        
        directory = tb_log_name
        if self.env_type == "gym":
            self.test_gym(episode, directory)
    
    def test_unity(self, episode,directory):
        pass
    
    def test_gym(self, episode,directory):
        from colabgymrender.recorder import Recorder
        Render_env = Recorder(self.env, directory)
        for i in range(episode):
            state = [np.expand_dims(Render_env.reset(),axis=0)]
            terminal = False
            episode_rew = 0
            while not terminal:
                actions = np.asarray(self._get_actions(self.params,state, None))
                observation, reward, terminal, info = Render_env.step(actions[0])
                state = [np.expand_dims(observation,axis=0)]
                episode_rew += reward
            print("episod reward :", episode_rew)