default: run

run:
	cargo run

run-release:
	[ -e "${PWD}/target/release/sync-ssh-keys" ] || cargo build --release
	${PWD}/target/release/sync-ssh-keys
