from setuptools import setup
setup(
    name='haiku_baselines',
    version='0.0.1',
    packages=['haiku_baselines',
              'haiku_baselines.common',
              'haiku_baselines.DQN',
              'haiku_baselines.C51',
              'haiku_baselines.QRDQN',
              'haiku_baselines.IQN',
              'haiku_baselines.FQF',
              'haiku_baselines.QRDQN',
              'haiku_baselines.DDPG',
              'haiku_baselines.TD3',
              'haiku_baselines.SAC',
              'haiku_baselines.TD4_QR',
              'haiku_baselines.TD4_IQN',
              'haiku_baselines.TQC',
              'haiku_baselines.IQA_TQC',
              'haiku_baselines.A2C',
              'haiku_baselines.TRPO',
              'haiku_baselines.ACER',
              'haiku_baselines.PPO',],
    install_requires=[
        'requests',
        'mlagents_envs',
        'gymnasium[all,atari,accept-rom-license]',
        'box2d',
        'box2d-py',
        #'box2d-kengz',
        'jax',
        'einops',
        'dm-haiku',
        'optax',
        'numpy',
        'ray[default]',
        'colabgymrender',
        'cpprb',
        'tensorboardX',
        'imageio-ffmpeg',
        #'importlib; python_version >= "3.5"',
    ]
)