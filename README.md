# ros2-qos-doctor

A small CLI that catches QoS mismatches between ROS 2 publishers and subscribers before they waste your afternoon.

## Why I made this

If you've spent time with ROS 2 you've probably hit this: a topic looks fine in `ros2 topic list`, your subscriber callback just never fires, and there's no error anywhere telling you why. Usually it's a QoS mismatch, the publisher and subscriber picked incompatible settings (reliability, durability, etc.) and DDS just quietly refuses to connect them. No warning, no crash, nothing in the logs.

I got bitten by this enough times that I wrote a tool to check for it automatically instead of guessing.

## What it does

Run `ros2-qos-doctor` while your nodes are up, and it scans every topic in the graph, compares the QoS settings of every publisher/subscriber pair on that topic, and tells you in plain language where they don't match and why the data isn't getting through.

Example output:

```
$ ros2-qos-doctor

/scan
  [ERROR] reliability: publisher 'mismatched_publisher' = BEST_EFFORT, subscriber 'mismatched_subscriber' = RELIABLE
    Subscriber requires RELIABLE delivery but publisher only offers BEST_EFFORT. The subscriber will receive nothing.
```

It exits with a non-zero status if it finds a real problem, so you can also drop it into a launch check or CI pipeline if you want.

## Reproducing the example above

There are two small demo scripts in `examples/` that create this exact mismatch on purpose, so you can see the tool actually catch it:

```bash
# terminal 1
python3 examples/mismatched_pub.py

# terminal 2
python3 examples/mismatched_sub.py

# terminal 3
ros2-qos-doctor
```

Watch terminal 2, it never prints a "received" line. Now you know why.

## Install

```bash
git clone https://github.com/niharandini/ros2-qos-doctor.git
cd ros2-qos-doctor
pip install -e .
```

You need a sourced ROS 2 install (Humble, Jazzy, Kilted, anything with `rclpy`). No other dependencies.

## Usage

```bash
ros2-qos-doctor                 # scan every topic once
ros2-qos-doctor --topic /scan   # only check specific topic(s), can repeat this flag
ros2-qos-doctor --watch         # keep re-scanning, useful while bringing a system up
ros2-qos-doctor --watch --interval 5
ros2-qos-doctor --no-color      # plain text, e.g. for CI logs
```

## What it currently checks

- **Reliability**: a subscriber asking for `RELIABLE` won't get anything from a `BEST_EFFORT` publisher, flagged as an error.
- **Durability**: a subscriber asking for `TRANSIENT_LOCAL` won't get anything from a `VOLATILE` publisher, flagged as an error.
- **Liveliness**: mismatched policies get flagged as a warning (rarely fatal, but worth knowing about).

Deadline and lifespan checks are natural next additions if anyone wants to send a PR.

## How it works, briefly

It spins up a short-lived ROS 2 node and uses `get_publishers_info_by_topic` / `get_subscriptions_info_by_topic`, both already exposed by `rclpy`, to pull the live QoS profile for every endpoint on every topic. Then it runs each publisher/subscriber pair through the standard DDS QoS compatibility rules. No extra middleware, no extra dependencies beyond `rclpy` itself.

## Contributing

Happy to take issues and PRs. A few things I'd like to add eventually:

- Deadline / lifespan policy checks
- A mode that reads a launch file statically instead of requiring a live system
- A ready-made GitHub Action for CI use

## License

Apache-2.0

## Author

Nihara Randini - shniharard@gmail.com
