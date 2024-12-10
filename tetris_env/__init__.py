from gym.envs.registration import register

register(
    id='Tetris-v0',
    entry_point='tetris_env.env:TetrisEnv',  # Path to TetrisEnv
)
