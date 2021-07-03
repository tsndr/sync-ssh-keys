#!/usr/bin/env python3

import paramiko
import threading
import yaml

class task_thread(threading.Thread):
   def __init__(self, host, user, keys):
      threading.Thread.__init__(self)
      self.host = host
      self.user = user
      self.keys = keys
   def run(self):
      update_keys(self.host, self.user, self.keys)

def read_config():
    with open('config.yaml', 'r') as stream:
        return yaml.safe_load(stream)

def update_keys(host, user, keys):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
        client.connect(host, username = user)
        client.exec_command('echo "###\n# Warning this file has been generated and will be overwritten!\n###\n\n' + '\n'.join(keys) + '" > ~/.ssh/authorized_keys2')
        client.close()
        print('✅ ' + user + '@' + host)
    except Exception:
        print('❌ ' + user + '@' + host)

def main():
    config = read_config()

    keys = []

    for key in config['keys']:
        keys.append(key['key'])

    for host in config['hosts']:
        for user in host['users']:
            try:
                thread = task_thread(host['host'], user, keys)
                thread.start()
            except:
                print('❌ ' + user + '@' + host['host'])

if __name__ == '__main__':
    main()