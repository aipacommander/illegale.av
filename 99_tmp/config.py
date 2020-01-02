import yaml
import os

config = None
path = os.path.dirname(__file__)
config_path = os.path.join(path, 'config.yml')
with open(config_path, 'r') as f:
    config = yaml.load(f)

assert config is not None, 'Create yaml file.'