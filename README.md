# servemon
Monitor services (HTTP/TCP/process) with auto-restart.
```bash
python servemon.py check --http https://google.com --tcp localhost:5432 --process nginx
python servemon.py watch services.json -i 60
```
Config: `{"services": [{"name": "web", "type": "http", "url": "http://localhost:8080", "restart_cmd": "systemctl restart web"}]}`

## Zero dependencies. Python 3.6+.
