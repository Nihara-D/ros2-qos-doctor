"""
Command-line entry point for ros2-qos-doctor.

Usage:
    ros2-qos-doctor                 # scan all topics once
    ros2-qos-doctor --topic /scan   # restrict to specific topic(s)
    ros2-qos-doctor --watch         # re-scan every N seconds
    ros2-qos-doctor --no-color      # disable ANSI colors (e.g. for CI logs)
"""

import argparse
import sys
import time

from .checker import run_scan, Severity


class Colors:
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    @classmethod
    def disable(cls):
        cls.RED = cls.YELLOW = cls.GREEN = cls.BOLD = cls.DIM = cls.RESET = ""


def _severity_color(severity):
    return Colors.RED if severity == Severity.ERROR else Colors.YELLOW


def print_report(reports):
    """Print a human-readable report. Returns True if any ERROR-level mismatch found."""
    any_error = False
    any_mismatch = False

    checked_topics = [r for r in reports if r.publisher_count and r.subscriber_count]

    if not checked_topics:
        print(f"{Colors.DIM}No topics with both a publisher and a subscriber were found.{Colors.RESET}")
        return False

    for report in checked_topics:
        if not report.mismatches:
            continue

        any_mismatch = True
        print(f"\n{Colors.BOLD}{report.topic}{Colors.RESET}")
        for m in report.mismatches:
            if m.severity == Severity.ERROR:
                any_error = True
            color = _severity_color(m.severity)
            print(
                f"  {color}[{m.severity.value}]{Colors.RESET} "
                f"{m.field}: publisher '{m.publisher_node}' = {m.pub_value}, "
                f"subscriber '{m.subscriber_node}' = {m.sub_value}"
            )
            print(f"    {Colors.DIM}{m.explanation}{Colors.RESET}")

    if not any_mismatch:
        print(f"{Colors.GREEN}No QoS incompatibilities found across "
              f"{len(checked_topics)} topic(s).{Colors.RESET}")

    return any_error


def main():
    parser = argparse.ArgumentParser(
        prog="ros2-qos-doctor",
        description="Detect QoS incompatibilities between ROS 2 publishers and subscribers.",
    )
    parser.add_argument(
        "--topic",
        action="append",
        help="Restrict the scan to specific topic name(s). Can be repeated.",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Continuously re-scan instead of running once.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=3.0,
        help="Seconds between scans in --watch mode (default: 3.0).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output.",
    )
    args = parser.parse_args()

    if args.no_color:
        Colors.disable()

    try:
        if args.watch:
            print(f"{Colors.DIM}Watching for QoS mismatches "
                  f"(Ctrl+C to stop)...{Colors.RESET}")
            while True:
                print(f"\n{Colors.BOLD}--- scan at {time.strftime('%H:%M:%S')} ---{Colors.RESET}")
                reports = run_scan(topic_filter=args.topic)
                print_report(reports)
                time.sleep(args.interval)
        else:
            reports = run_scan(topic_filter=args.topic)
            had_error = print_report(reports)
            sys.exit(1 if had_error else 0)
    except KeyboardInterrupt:
        print(f"\n{Colors.DIM}Stopped.{Colors.RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
