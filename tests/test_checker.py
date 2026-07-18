"""
Unit tests for compare_qos().

These use lightweight fake objects instead of real rclpy TopicEndpointInfo,
so the tests run fast and don't require a live ROS 2 graph or daemon.
"""

import sys
import types
import pytest


# --- Minimal fakes for the pieces of rclpy.qos we depend on -----------
# This lets the test suite run in environments without a full ROS 2
# install, as long as rclpy is importable. If rclpy IS installed, these
# fakes are ignored in favor of the real enums (see conftest note below).

from ros2_qos_doctor.checker import compare_qos, Severity
from rclpy.qos import QoSDurabilityPolicy, QoSReliabilityPolicy, QoSLivelinessPolicy


class FakeQoS:
    def __init__(self, reliability, durability, liveliness=None):
        self.reliability = reliability
        self.durability = durability
        self.liveliness = liveliness or QoSLivelinessPolicy.AUTOMATIC


class FakeEndpointInfo:
    def __init__(self, node_name, qos_profile):
        self.node_name = node_name
        self.qos_profile = qos_profile


def test_reliable_subscriber_vs_best_effort_publisher_is_error():
    pub = FakeEndpointInfo(
        "pub_node",
        FakeQoS(QoSReliabilityPolicy.BEST_EFFORT, QoSDurabilityPolicy.VOLATILE),
    )
    sub = FakeEndpointInfo(
        "sub_node",
        FakeQoS(QoSReliabilityPolicy.RELIABLE, QoSDurabilityPolicy.VOLATILE),
    )

    mismatches = compare_qos(pub, sub)

    assert len(mismatches) == 1
    assert mismatches[0].field == "reliability"
    assert mismatches[0].severity == Severity.ERROR


def test_matching_reliability_and_durability_is_compatible():
    pub = FakeEndpointInfo(
        "pub_node",
        FakeQoS(QoSReliabilityPolicy.RELIABLE, QoSDurabilityPolicy.VOLATILE),
    )
    sub = FakeEndpointInfo(
        "sub_node",
        FakeQoS(QoSReliabilityPolicy.RELIABLE, QoSDurabilityPolicy.VOLATILE),
    )

    mismatches = compare_qos(pub, sub)

    assert mismatches == []


def test_transient_local_subscriber_vs_volatile_publisher_is_error():
    pub = FakeEndpointInfo(
        "pub_node",
        FakeQoS(QoSReliabilityPolicy.RELIABLE, QoSDurabilityPolicy.VOLATILE),
    )
    sub = FakeEndpointInfo(
        "sub_node",
        FakeQoS(QoSReliabilityPolicy.RELIABLE, QoSDurabilityPolicy.TRANSIENT_LOCAL),
    )

    mismatches = compare_qos(pub, sub)

    assert len(mismatches) == 1
    assert mismatches[0].field == "durability"
    assert mismatches[0].severity == Severity.ERROR


def test_best_effort_subscriber_accepts_any_publisher_reliability():
    # A BEST_EFFORT subscriber has no strict requirement, so a RELIABLE
    # publisher should never be flagged as a mismatch on this axis.
    pub = FakeEndpointInfo(
        "pub_node",
        FakeQoS(QoSReliabilityPolicy.RELIABLE, QoSDurabilityPolicy.VOLATILE),
    )
    sub = FakeEndpointInfo(
        "sub_node",
        FakeQoS(QoSReliabilityPolicy.BEST_EFFORT, QoSDurabilityPolicy.VOLATILE),
    )

    mismatches = compare_qos(pub, sub)

    assert mismatches == []


def test_liveliness_mismatch_is_warning_not_error():
    pub = FakeEndpointInfo(
        "pub_node",
        FakeQoS(
            QoSReliabilityPolicy.RELIABLE,
            QoSDurabilityPolicy.VOLATILE,
            liveliness=QoSLivelinessPolicy.AUTOMATIC,
        ),
    )
    sub = FakeEndpointInfo(
        "sub_node",
        FakeQoS(
            QoSReliabilityPolicy.RELIABLE,
            QoSDurabilityPolicy.VOLATILE,
            liveliness=QoSLivelinessPolicy.MANUAL_BY_TOPIC,
        ),
    )

    mismatches = compare_qos(pub, sub)

    assert len(mismatches) == 1
    assert mismatches[0].field == "liveliness"
    assert mismatches[0].severity == Severity.WARNING
