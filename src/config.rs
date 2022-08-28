use std::{collections::HashMap, fs, path::Path};

use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize, Debug)]
pub struct Config {
    pub keys: HashMap<String, String>,
    pub groups: HashMap<String, Vec<String>>,
    pub hosts: Vec<Host>
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Host {
    pub host: String,
    pub port: Option<u16>,
    pub users: HashMap<
        String,
        HashMap<
            String,
            Vec<String>
        >
    >
}

pub fn read() -> Result<Config, ()> {
    let yaml = fs::read_to_string(Path::new("config.yaml")).unwrap_or("".to_string());
    let config: Config = match serde_yaml::from_str(&yaml) {
        Ok(c) => c,
        Err(_) => return Err(())
    };

    Ok(config)
}
