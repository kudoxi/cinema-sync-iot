import os
import toml

try:
    Config = toml.load('config.toml')
    ENV = 'DEV'
except FileNotFoundError:
    Config = toml.loads(os.environ['SYNCER_CONFIG'])
    ENV = 'PROD'
