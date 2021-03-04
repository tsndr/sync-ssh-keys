#!/usr/bin/env python3

import paramiko
import threading
import yaml

class taskThread(threading.Thread):
   def __init__(self, host, keys):
      threading.Thread.__init__(self)
      self.host = host
      self.keys = keys
   def run(self):
      updateKeys(self.host, self.keys)

def readConfig():
    with open('config.yaml', 'r') as stream:
        return yaml.safe_load(stream)

def updateKeys(host, keys):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
        client.connect(host, username = 'root')
        client.exec_command('echo "###\n# Warning this file has been generated and will be overwritten!\n###\n\n' + '\n'.join(keys) + '" > ~/.ssh/authorized_keys2')
        client.close()
        print('✅ ' + host)
    except Exception:
        print('❌ ' + host)

def main():
    config = readConfig()

    keys = []

    for key in config['keys']:
        keys.append(key['key'])

    for host in config['hosts']:
        try:
            thread = taskThread(host, keys)
            thread.start()
        except:
            print('❌ ' + host)

if __name__ == '__main__':
    main()