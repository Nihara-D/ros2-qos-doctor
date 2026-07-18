"""
Core logic for discovering topics and checking QoS compatibility
between publishers and subscribers.

This intentionally uses only rclpy's public introspection APIs
(get_publishers_info_by_topic / get_subscriptions_info_by_topic),
which are available on any live ROS 2 node without extra dependencies.
"""

from dataclasses import dataclass, field
from enum import Enum

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSReliabilityPolicy,
    QoSLivelinessPolicy,
)


class Severity(str, Enum):
    ERROR = "ERROR"     # will definitely break delivery
    WARNING = "WARNING"  # may cause subtle/partial issues


@dataclass
class Mismatch:
    topic: str
    publisher_node: str
    subscriber_node: str
    field: str
    pub_value: str
    sub_value: str
    severity: Severity
    explanation: str


@dataclass
class TopicReport:
    topic: str
    publisher_count: int
    subscriber_count: int
    mismatches: list = field(default_factory=list)


# --- Compatibility rules -----------------------------------------------
#
# These follow the DDS/ROS 2 QoS compatibility rules: a subscriber's
# requested QoS must be "equal or weaker demand" than what the publisher
# offers, for each policy independently.

def _check_reliability(pub_val, sub_val):
    """RELIABLE subscriber cannot be satisfied by a BEST_EFFORT publisher."""
    if (
        sub_val == QoSReliabilityPolicy.RELIABLE
        and pub_val == QoSReliabilityPolicy.BEST_EFFORT
    ):
        return Mismatch(
            topic="",
            publisher_node="",
            subscriber_node="",
            field="reliability",
            pub_value="BEST_EFFORT",
            sub_value="RELIABLE",
            severity=Severity.ERROR,
            explanation=(
                "Subscriber requires RELIABLE delivery but publisher only "
                "offers BEST_EFFORT. The subscriber will receive nothing."
            ),
        )
    return None


def _check_durability(pub_val, sub_val):
    """TRANSIENT_LOCAL subscriber cannot be satisfied by a VOLATILE publisher."""
    if (
        sub_val == QoSDurabilityPolicy.TRANSIENT_LOCAL
        and pub_val == QoSDurabilityPolicy.VOLATILE
    ):
        return Mismatch(
            topic="",
            publisher_node="",
            subscriber_node="",
            field="durability",
            pub_value="VOLATILE",
            sub_value="TRANSIENT_LOCAL",
            severity=Severity.ERROR,
            explanation=(
                "Subscriber requests TRANSIENT_LOCAL (wants late-joiner / "
                "latched data) but publisher is VOLATILE. The subscriber "
                "will not receive any messages published before it "
                "connected, and on some RMW implementations will receive "
                "nothing at all."
            ),
        )
    return None


def _check_liveliness(pub_val, sub_val):
    """Flag mismatched liveliness policies as a warning (rarely fatal, but confusing)."""
    if pub_val != sub_val:
        return Mismatch(
            topic="",
            publisher_node="",
            subscriber_node="",
            field="liveliness",
            pub_value=str(pub_val),
            sub_value=str(sub_val),
            severity=Severity.WARNING,
            explanation=(
                "Publisher and subscriber use different liveliness "
                "policies. Usually harmless, but can cause unexpected "
                "liveliness-lost events."
            ),
        )
    return None


_CHECKS = [
    ("reliability", _check_reliability),
    ("durability", _check_durability),
    ("liveliness", _check_liveliness),
]


def compare_qos(pub_info, sub_info):
    """Compare one publisher's QoS against one subscriber's QoS.

    Returns a list of Mismatch objects (empty if compatible).
    """
    mismatches = []
    pub_qos = pub_info.qos_profile
    sub_qos = sub_info.qos_profile

    field_map = {
        "reliability": (pub_qos.reliability, sub_qos.reliability),
        "durability": (pub_qos.durability, sub_qos.durability),
        "liveliness": (pub_qos.liveliness, sub_qos.liveliness),
    }

    for field_name, check_fn in _CHECKS:
        pub_val, sub_val = field_map[field_name]
        result = check_fn(pub_val, sub_val)
        if result:
            result.topic = ""  # filled in by caller
            result.publisher_node = pub_info.node_name
            result.subscriber_node = sub_info.node_name
            mismatches.append(result)

    return mismatches


class QosCheckerNode(Node):
    """A short-lived node used purely for graph introspection."""

    def __init__(self):
        super().__init__("qos_doctor_introspector")

    def scan(self, topic_filter=None):
        """Scan all topics and return a list of TopicReport objects.

        topic_filter: optional list of topic names to restrict the scan to.
        """
        reports = []
        topic_names_and_types = self.get_topic_names_and_types()

        for topic_name, _types in topic_names_and_types:
            if topic_filter and topic_name not in topic_filter:
                continue

            pubs = self.get_publishers_info_by_topic(topic_name)
            subs = self.get_subscriptions_info_by_topic(topic_name)

            report = TopicReport(
                topic=topic_name,
                publisher_count=len(pubs),
                subscriber_count=len(subs),
            )

            # Only meaningful to compare if both sides exist.
            for pub_info in pubs:
                for sub_info in subs:
                    # Skip a node comparing against itself (loopback topics).
                    if pub_info.node_name == sub_info.node_name:
                        continue
                    mismatches = compare_qos(pub_info, sub_info)
                    for m in mismatches:
                        m.topic = topic_name
                        report.mismatches.append(m)

            reports.append(report)

        return reports


def run_scan(topic_filter=None):
    """Convenience entry point: spins up rclpy, scans, shuts down, returns reports."""
    rclpy.init(args=None)
    try:
        node = QosCheckerNode()
        # Give discovery a brief moment to populate the graph.
        rclpy.spin_once(node, timeout_sec=1.0)
        reports = node.scan(topic_filter=topic_filter)
        node.destroy_node()
        return reports
    finally:
        rclpy.shutdown()
