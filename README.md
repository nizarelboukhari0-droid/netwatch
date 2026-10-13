# Netwatch

A small command-line utility that checks TCP reachability for endpoints you specify. It reports whether each connection succeeds, how long it takes, and can append results to a JSON Lines log.

Netwatch only connects to the hosts and ports you provide. It does not scan networks or change system settings. It uses only the Python standard library.

## Requirements

- Python 3.9 or newer

## Usage

Check a host on TCP port 443:

```powershell
python .\netwatch.py --host example.com
```

Check multiple endpoints:

```powershell
python .\netwatch.py --host example.com --endpoint dns=1.1.1.1:53
```

Repeat checks every 10 seconds and save results:

```powershell
python .\netwatch.py --endpoint web=example.com:443 --interval 10 --log .\netwatch.jsonl
```

Stop continuous monitoring with `Ctrl+C`.

## Options

- `--host HOST`: check a host on TCP port 443; repeat to add hosts.
- `--endpoint NAME=HOST:PORT`: check a named endpoint; repeat as needed. For IPv6, use `NAME=[ADDRESS]:PORT`.
- `--timeout SECONDS`: connection timeout (default: 3).
- `--interval SECONDS`: seconds between rounds; `0` runs once (default: 0).
- `--log PATH`: append results as JSON Lines to a file.
