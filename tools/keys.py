"""Read an API key from the environment or a dotenv-style file, never printing it."""
import os
from pathlib import Path


def read_key(name, env_file, required=True):
    key = os.environ.get(name)
    if not key and env_file and Path(env_file).is_file():
        for line in Path(env_file).read_text().splitlines():
            field, sep, value = line.strip().removeprefix('export ').partition('=')
            if sep and field.strip() == name:
                key = value.strip().strip('"\'')
                break
    if not key:
        if required:
            raise ValueError(f'Set {name} in the environment or in the env file (see .env.example)')
        return None
    if '\n' in key or '\r' in key:
        raise ValueError(f'Invalid {name} format')
    return key
