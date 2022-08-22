mod config;

use std::{net::TcpStream, path::{Path, PathBuf}, io::Write};
use ssh2::Session;

fn upload_file(host: &str, port: u16, username: &str, private_key: &Path, passphrase: Option<&str>, content: &str) -> Result<(), Box<dyn std::error::Error>> {
    let tcp: TcpStream = TcpStream::connect(format!("{}:{}", host, port))?;
    let mut sess: Session = Session::new()?;

    sess.set_timeout(3000);
    sess.set_tcp_stream(tcp);
    sess.handshake()?;

    let public_key: PathBuf = private_key.with_extension("pub");

    sess.userauth_pubkey_file(&username, Some(&public_key), &private_key, passphrase)?;

    let mut remote_file = sess.scp_send(Path::new(".ssh").join("authorized_keys2").as_path(), 0o644, content.len() as u64, None)?;

    remote_file.write(content.as_bytes())?;

    remote_file.send_eof()?;
    remote_file.wait_eof()?;
    remote_file.close()?;
    remote_file.wait_close()?;

    return Ok(());
}

fn generate_authorized_keys(host_keys: Vec<String>) -> String {
    return format!("###\n# Warning this file has been generated and will be overwritten!\n###\n\n{}\n", host_keys.join("\n"));
}

fn main() {
    let ssh_dir: PathBuf = dirs::home_dir().unwrap().join(".ssh");
    let private_key: PathBuf = ssh_dir.join("id_ed25519_old");
    let passphrase: Option<&str> = None;
    let config = config::read();

    for host in &config.hosts {
        for (user_name, user_data) in &host.users {
            let mut host_keys: Vec<String> = [].to_vec();

            if user_data.contains_key("groups") {
                for group in user_data["groups"].as_slice() {
                    if !config.groups.contains_key(group) {
                        println!("WARNING: Key-group \"{}\" not fount!", group);
                        continue;
                    }
                    for key_name in config.groups[group].as_slice() {
                        if config.keys.contains_key(key_name) {
                            host_keys.push(config.keys.get(key_name).unwrap().to_string())
                        }
                    }
                }
            }

            if user_data.contains_key("keys") {
                for key_name in user_data["keys"].as_slice() {
                    if !config.keys.contains_key(key_name) {
                        println!("WARNING: Key \"{}\" not found!", key_name);
                        continue;
                    }
                    host_keys.push(config.keys.get(key_name).unwrap().to_string())
                }
            }

            // Remove duplicates
            host_keys.sort_unstable();
            host_keys.dedup();

            if host_keys.is_empty() {
                continue;
            }

            let mut port: u16 = 22;

            if host.port.is_some() {
                port = host.port.unwrap();
            }

            let content = &generate_authorized_keys(host_keys);

            // TODO: Make async! TOKIO!!!
            match upload_file(&host.host, port, user_name, &private_key.as_path(), passphrase, content) {
                Ok(_) => println!("✅ {}@{}", user_name, host.host),
                Err(_) => println!("❌ {}@{}", user_name, host.host)
            }
        }
    }
}
