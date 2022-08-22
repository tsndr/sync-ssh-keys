# Sync SSH Keys
A simple script to sync ssh public keys to multiple servers, without the danger of locking yourself out (since it writes to `authorized_keys2`)

### Create configuration file
Rename `config-example.yaml` to `config.yaml` and set your own data.

## Usage
Run `cargo run` or `cargo build --release && ./target/release/sync-ssh-keys`
