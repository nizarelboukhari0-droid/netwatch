import argparse
import json
import socket
import time
from datetime import datetime, timezone
from pathlib import Path


def parse_endpoint(value: str) -> tuple[str, str, int]:
    """Parse NAME=HOST:PORT. For IPv6, use NAME=[ADDRESS]:PORT."""
    if "=" not in value:
        raise argparse.ArgumentTypeError("expected NAME=HOST:PORT")

    name, address = value.split("=", 1)
    name = name.strip()

    if address.startswith("["):
        close = address.find("]")
        if close < 0 or address[close + 1 : close + 2] != ":":
            raise argparse.ArgumentTypeError("IPv6 must use NAME=[ADDRESS]:PORT")
        host, port_text = address[1:close], address[close + 2 :]
    else:
        if ":" not in address:
            raise argparse.ArgumentTypeError("expected HOST:PORT")
        host, port_text = address.rsplit(":", 1)

    if not name or not host:
        raise argparse.ArgumentTypeError("name and host cannot be empty")

    try:
        port = int(port_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc

    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")

    return name, host, port


def check(name: str, host: str, port: int, timeout: float) -> dict:
    started = time.perf_counter()
    ok = False
    error = None

    try:
        with socket.create_connection((host, port), timeout=timeout):
            ok = True
    except OSError as exc:
        error = f"{type(exc).__name__}: {exc}"

    return {
        "name": name,
        "host": host,
        "port": port,
        "ok": ok,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Monitor TCP reachability for chosen network endpoints."
    )
    parser.add_argument(
        "--endpoint",
        action="append",
        type=parse_endpoint,
        default=[],
        metavar="NAME=HOST:PORT",
        help="endpoint to check; repeat as needed",
    )
    parser.add_argument(
        "--host",
        action="append",
        default=[],
        metavar="HOST",
        help="check a host on TCP port 443; repeat as needed",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0,
        help="seconds between rounds; 0 runs once (default: 0)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=3.0,
        help="connection timeout in seconds (default: 3)",
    )
    parser.add_argument(
        "--log",
        type=Path,
        help="append results to this JSON Lines file",
    )
    args = parser.parse_args()

    if not args.endpoint and not args.host:
        parser.error("provide at least one --endpoint or --host")
    if args.interval < 0 or args.timeout <= 0:
        parser.error("--interval must be nonnegative and --timeout must be positive")

    targets = list(args.endpoint)
    targets.extend((host, host, 443) for host in args.host)
    previous = {}

    try:
        while True:
            for name, host, port in targets:
                result = check(name, host, port, args.timeout)
                state = "UP" if result["ok"] else "DOWN"
                line = (
                    f'{result["timestamp"]} {state:4} {name} '
                    f'({host}:{port}) {result["elapsed_ms"]:.2f} ms'
                )
                if result["error"]:
                    line += f' — {result["error"]}'

                if name in previous and previous[name] != result["ok"]:
                    line += " (state changed)"

                print(line, flush=True)
                previous[name] = result["ok"]

                if args.log:
                    try:
                        with args.log.open("a", encoding="utf-8") as log_file:
                            log_file.write(json.dumps(result, ensure_ascii=False) + "\n")
                    except OSError as exc:
                        parser.exit(2, f"Could not write log {args.log}: {exc}\n")

            if args.interval == 0:
                break
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\nStopped.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
