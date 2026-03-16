#!/usr/bin/env python3
"""servemon - Monitor services and processes, restart on failure."""
import subprocess, argparse, time, sys, json, os, signal

def check_http(url, timeout=5):
    import urllib.request, ssl
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(url, timeout=timeout, context=ctx) as r:
            return r.status == 200
    except: return False

def check_tcp(host, port, timeout=3):
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port)); s.close(); return True
    except: return False

def check_process(name):
    r = subprocess.run(['pgrep', '-f', name], capture_output=True)
    return r.returncode == 0

def main():
    p = argparse.ArgumentParser(description='Service monitor')
    sub = p.add_subparsers(dest='cmd')
    
    wt = sub.add_parser('watch', help='Watch services from config')
    wt.add_argument('config', help='JSON config file')
    wt.add_argument('-i', '--interval', type=int, default=30)
    
    ck = sub.add_parser('check', help='One-shot check')
    ck.add_argument('--http', nargs='*', help='HTTP URLs')
    ck.add_argument('--tcp', nargs='*', help='host:port pairs')
    ck.add_argument('--process', nargs='*', help='Process names')
    
    args = p.parse_args()
    if not args.cmd: p.print_help(); return
    
    if args.cmd == 'check':
        all_ok = True
        for url in (args.http or []):
            ok = check_http(url)
            print(f"  {'✓' if ok else '✗'} HTTP {url}")
            if not ok: all_ok = False
        for hp in (args.tcp or []):
            host, port = hp.rsplit(':', 1)
            ok = check_tcp(host, int(port))
            print(f"  {'✓' if ok else '✗'} TCP  {hp}")
            if not ok: all_ok = False
        for proc in (args.process or []):
            ok = check_process(proc)
            print(f"  {'✓' if ok else '✗'} PROC {proc}")
            if not ok: all_ok = False
        sys.exit(0 if all_ok else 1)
    
    elif args.cmd == 'watch':
        with open(args.config) as f: config = json.load(f)
        services = config.get('services', [])
        print(f"Monitoring {len(services)} services (every {args.interval}s)")
        
        while True:
            for svc in services:
                name = svc['name']
                ok = False
                if svc['type'] == 'http': ok = check_http(svc['url'])
                elif svc['type'] == 'tcp': ok = check_tcp(svc['host'], svc['port'])
                elif svc['type'] == 'process': ok = check_process(svc['pattern'])
                
                status = '✓' if ok else '✗'
                print(f"[{time.strftime('%H:%M:%S')}] {status} {name}")
                
                if not ok and 'restart_cmd' in svc:
                    print(f"  → Restarting: {svc['restart_cmd']}")
                    subprocess.run(svc['restart_cmd'], shell=True)
            
            time.sleep(args.interval)

if __name__ == '__main__':
    main()
