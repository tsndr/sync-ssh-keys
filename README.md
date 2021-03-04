# Sync SSH Keys
A simple script to sync ssh public keys to multiple servers, without the danger of locking yourself out (since it writes to `authorized_keys2`)

## Setup

### Install dependencies
```bash
pip3 install -r requirements.txt
```

### Create configuration file
Rename `config-example.yaml` to `config.yaml` and set your own data.

## Usage
Run `./sync.py` or `python3 sync.py`