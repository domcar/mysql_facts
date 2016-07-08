# mysql_facts
print in json format mysql facts

usage: sudo python mysql_facts.py


OUTPUT:


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
