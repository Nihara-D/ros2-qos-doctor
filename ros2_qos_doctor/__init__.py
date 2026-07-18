"""ros2_qos_doctor: detect QoS incompatibilities in a running ROS 2 system."""

from .checker import run_scan, compare_qos, Severity, Mismatch, TopicReport

__version__ = "0.1.0"

__all__ = [
    "run_scan",
    "compare_qos",
    "Severity",
    "Mismatch",
    "TopicReport",
    "__version__",
]
