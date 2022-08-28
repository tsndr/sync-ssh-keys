mod config;

use std::io::Write;
use std::net::{TcpStream, SocketAddr, ToSocketAddrs};
use std::path::{PathBuf, Path};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

use ssh2::Session;

#[derive(Clone)]
struct Host {
    host: Arc<Mutex<String>>,
    port: u16,
    username: Arc<Mutex<String>>,
    content: Arc<Mutex<String>>
}

fn upload_config(h: &Host) -> Result<String, String> {
    let host = h.host.lock().unwrap().to_owned();
    let port = h.port;
    let username = h.username.lock().unwrap().to_owned();
    let private_key = PathBuf::from("/Users/toby/.ssh/id_ed25519");
    let content = h.content.lock().unwrap();
    let connection_string = format!("{}@{}", username, host);

    let addr: SocketAddr = format!("{}:{}", host, port)
        .to_socket_addrs()
        .unwrap().nth(0)
        .expect(format!("Invalid host/port in `{}:{}`", host, port).as_str());
    let tcp: TcpStream = match TcpStream::connect_timeout(&addr, Duration::from_secs(1)) {
        Ok(s) => s,
        Err(_) => return Err(connection_string)
    };
    let mut sess = Session::new().unwrap();

    sess.set_tcp_stream(tcp);
    sess.handshake().unwrap();

    sess.userauth_pubkey_file(&username, None, &private_key, None).unwrap();

    let mut remote_file = match sess.scp_send(Path::new(".ssh").join("authorized_keys2").as_path(), 0o644, content.len() as u64, None) {
        Ok(rf) => rf,
        Err(_) => return Err(connection_string)
    };

    match remote_file.write(content.as_bytes()) {
        Ok(rf) => rf,
        Err(_) => return Err(connection_string)
    };

    remote_file.send_eof().unwrap();
    remote_file.wait_eof().unwrap();
    remote_file.close().unwrap();
    remote_file.wait_close().unwrap();

    Ok(connection_string)
}

fn generate_authorized_keys(host_keys: Vec<String>) -> String {
    format!("###\n# Warning this file has been generated and will be overwritten!\n###\n\n{}\n", host_keys.join("\n"))
}

fn main() {
    let mut hosts: Vec<Host> = vec![];
    let config = match config::read() {
        Ok(c) => c,
        Err(_) => return println!("Error: `config.yaml` not found!")
    };

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

            let content = generate_authorized_keys(host_keys);

            hosts.push(Host {
                host: Arc::new(Mutex::new(host.host.to_string())),
                port: host.port.unwrap_or(22),
                username: Arc::new(Mutex::new(user_name.to_string())),
                content: Arc::new(Mutex::new(content))
            });
        }
    }

    let mut handles = vec![];

    for host in hosts {
        handles.push(thread::spawn(move || {
            match upload_config(&host) {
                Ok(s) => println!("✅ {}", s),
                Err(s) => println!("❌ {}", s)
            }
        }));
    }

    for handler in handles {
        handler.join().unwrap();
    }
}
