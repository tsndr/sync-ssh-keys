#!/usr/bin/env python3

import paramiko
import threading
import yaml

class task_thread(threading.Thread):
    def __init__(self, host, port, user, keys):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.user = user
        self.keys = keys
    def run(self):
        update_keys(self.host, self.port, self.user, self.keys)

def read_config():
    with open('config.yaml', 'r') as stream:
        return yaml.safe_load(stream)
 
def update_keys(host, port, user, keys):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
        client.connect(host, username = user, port = port, timeout = 1)
        client.exec_command('echo "###\n# Warning this file has been generated and will be overwritten!\n###\n' + '\n'.join(keys) + '" > ~/.ssh/authorized_keys2')
        client.close()
        print('✅ ' + user + '@' + host)
    except Exception:
        print('❌ ' + user + '@' + host)

def main():
    config = read_config()
    for host in config['hosts']:
        for user_name, user_data in host['users'].items():
            host_keys = []
            if 'groups' in user_data.keys():
                for group in user_data['groups']:
                    if group not in config['groups'].keys():
                        print('WARNING: Key-group "' + group + '" not found!')
                        continue
                    for key_name in config['groups'][group]:
                        host_keys.append(config['keys'][key_name])
            if 'keys' in user_data.keys():
                for key_name in user_data['keys']:
                    if key_name not in config['keys'].keys():
                        print('WARNING: Key "' + key_name + '" not found!')
                        continue
                    host_keys.append(config['keys'][key_name])
            host_keys = list(set(host_keys)) # Filter duplicates
            if not host_keys:
                continue
            if not 'port' in host:
                host['port'] = 22
            try:
                thread = task_thread(host['host'], host['port'], user_name, host_keys)
                thread.start()
            except:
                print('❌ ' + user_name + '@' + host['host'])

if __name__ == '__main__':
    main()
