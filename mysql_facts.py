#!/usr/bin/python

import os, re
from parse import compile
import StringIO
from subprocess import Popen, PIPE
import glob

import sys, json, os
from itertools import izip

DOCUMENTATION = '''
---
module: gather_mySQL_facts; tested on Ubuntu 10,12,14,16 with mysql 5.1, 5.5, 5.7
author:
    - "Domenico Caruso" domenico.caruso@de.clara.net

short_description: Provide facts regarding mySQL

prerequisites: it must be Ubuntu otherwise there is no debian-sys-main user

description: provides facts like: are there unknown users? Are there users without password? What are users privileges(on what db)?
             print general settings from /etc/mysql/my.cnf; print status output(show status); print slave/master status(show slave/master status); print DBs

'''

EXAMPLES = '''
     "sql_privileges": {
        "debian-sys-maint@localhost": {
            "*.*": "GRANT ALL PRIVILEGES"
        },
        "root@127.0.0.1": {
            "*.*": "GRANT ALL PRIVILEGES"
        },
        "root@::1": {
            "*.*": "GRANT ALL PRIVILEGES"
        },
        "root@localhost": {
            "''@''": "GRANT PROXY",
            "*.*": "GRANT ALL PRIVILEGES"
        },
        "root@ubuntu1404": {
            "''@''": "GRANT PROXY",
            "*.*": "GRANT ALL PRIVILEGES"
        }
    },
    "sql_settings": {
        "basedir": "/usr",
        "bind-address": "127.0.0.1",
        "datadir": "/var/lib/mysql",
        "expire_logs_days": "10",
        "key_buffer": "16M",
        "lc-messages-dir": "/usr/share/mysql",
        "log_error": "/var/log/mysql/error.log",
        "max_allowed_packet": "16M",
        "max_binlog_size": "100M",
        "myisam-recover": "BACKUP",
        "nice": "0",
        "pid-file": "/var/run/mysqld/mysqld.pid",
        "port": "3306",
        "query_cache_limit": "1M",
        "query_cache_size": "16M",
        "socket": "/var/run/mysqld/mysqld.sock",
        "thread_cache_size": "8",
        "thread_stack": "192K",
        "tmpdir": "/tmp",
        "user": "mysql"
    },
    "sql_slave_master": {
        "master": {},
        "slave": {}

'''

def parse_users(pw,mdb):
      
    authentication = {}
    user_pass = {}
    # connection to mysql
    con = mdb.connect('localhost', 'debian-sys-maint', pw)
    # obtain version
    cur = con.cursor()
    cur.execute('select version()')
    rows = cur.fetchall()
    version= float(rows[0][0].split("-")[0].rsplit(".",1)[0])
    
    # read user,host and passwords (hashes)
    cur = con.cursor()
    if version >= 5.7:
       cur.execute('select user,host,HEX(authentication_string) from mysql.user')
    elif version < 5.7:
       cur.execute('select user,host,HEX(password) from mysql.user')
    rows = cur.fetchall()
    col_names = [desc[0] for desc in cur.description]
    for row in rows:
        user_pass[ row[0]+'@'+row[1] ] = row[2]
    authentication = user_pass
    return authentication

def parse_privileges(pw,mdb):

    con = mdb.connect('localhost', 'debian-sys-maint', pw)
    user_privileges = {}
    cur = con.cursor()
    cur.execute("SELECT user,host FROM mysql.user")
    rows = cur.fetchall()
    for row in rows:
        user = row[0]
        location = row[1]
        ul = user +'@' +location
        con.cursor()
        cur.execute("SHOW GRANTS FOR %s@%s ",(user,location))
        l = cur.fetchall()
        for line in l:
            privilege = line[0].split(" TO ")[0].split(" ON ")[0]
            on_db = line[0].split(" TO ")[0].split(" ON ")[1]
            if ul not in user_privileges:
               user_privileges[ul] = {}
            user_privileges[ul][on_db]=privilege
    return user_privileges

def parse_databases(pw,mdb):
    # read databases
    databases = []
    con = mdb.connect('localhost', 'debian-sys-maint', pw) 
    cur = con.cursor()
    cur.execute('show DATABASES')
    rows = cur.fetchall()
    for row in rows:
        databases.append(row[0])
    return databases

def parse_settings(mdb):
    general_settings = {}
    f = open('/etc/mysql/my.cnf', 'r')
    config_dir = []
    for line in f:
        if re.match('#',line): continue     # avoid comments    
        elif re.match('!includedir',line):  # find other config directory
           config_dir.append(line.split()[1])
        elif '=' in line:                   # we want only key = value lines
           key = line.split('=')[0].strip('[ \t]')
           value = line.split('=')[1].strip('[ \n]')
           general_settings[key] = value
    
    # now we iterate over the other possible config files
    for folder in config_dir:
        config_files= glob.glob(folder+'*')
        for f in config_files:
            conf = open(f,'r')
            for line in conf:
                if re.match('#',line): continue     #avoid comments
                elif '=' in line:                   # we want only key = value lines
                   key = line.split('=')[0].strip('[ \t]')
                   value = line.split('=')[1].strip('[ \n]')
                   general_settings[key] = value
    return general_settings

def parse_slave_master(pw,mdb):
    slave_master = {}
    slave_master['slave'] = {}
    slave_master['master'] = {}
    con = mdb.connect('localhost', 'debian-sys-maint', pw) 
    cur = con.cursor()
    cur.execute("show slave status")
    rows = cur.fetchall()
    desc = cur.description
    if rows:
       i=0
       while i < len(desc):
           slave_master['slave'][desc[i][0]]=rows[0][i]
           i += 1  
    cur = con.cursor()
    cur.execute("show master status")
    rows = cur.fetchall()
    desc = cur.description
    if rows:
       i=0
       while i < len(desc):
           slave_master['master'][desc[i][0]]=rows[0][i]
           i += 1  
      
    return slave_master

def parse_status(pw,mdb):
    status = {}
    con = mdb.connect('localhost', 'debian-sys-maint', pw)
    cur = con.cursor()
    cur.execute("""show status""")
    rows = cur.fetchall()
    for row in rows:
        status[row[0]]=row[1]
    return status


# read debian user password
try:
   f = open('/etc/mysql/debian.cnf','r')
   for line in f:
       if 'password' in line:
          pw = line.split()[2]
except:
   sys.exit("MySQL not installed or not on Debian. Ignoring module")
try:
   import MySQLdb as mdb
except: 
   sys.exit("package required: python-mysqldb. Ignoring module")

users = {}
users['users'] = parse_users(pw,mdb)
privileges = {}
privileges['privileges'] = parse_privileges(pw,mdb)
status = {}
status['status'] = parse_status(pw,mdb)
settings = {}
settings['settings'] = parse_settings(mdb)
slave_master = {}
slave_master['slave_master'] = parse_slave_master(pw,mdb)
databases = {}
databases['databases'] = parse_databases(pw,mdb)

with open('risultato.txt','w') as outfile:
     json.dump(users,outfile,indent=1)
with open('risultato.txt','aw') as outfile:
     json.dump(privileges,outfile,indent=1)
with open('risultato.txt','aw') as outfile:
     json.dump(status,outfile,indent=1)
with open('risultato.txt','aw') as outfile:
     json.dump(settings,outfile,indent=1)
with open('risultato.txt','aw') as outfile:                                                                                                                                         
     json.dump(slave_master,outfile,indent=1)
with open('risultato.txt','aw') as outfile:                                                                                                                                         
     json.dump(databases,outfile,indent=1)
