from setuptools import setup, find_packages

setup(
    name='tetris_gym',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'gym',
        'pygame',
        'numpy',
    ],
    description='A Tetris Gym environment for RL research.',
    author='Your Name',
    author_email='youssifayman2004@gmail.com',
    url='https://github.com/alamenium/tetris_gym',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.8',
    ],
)
