"""
Publishes on /scan with BEST_EFFORT reliability -- a common default for
sensor drivers (matches the ROS 2 'sensor data' QoS preset).

Run alongside examples/mismatched_sub.py to reproduce a silent QoS mismatch:
the subscriber will never print anything, with no error from ROS 2 itself.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import String


class MismatchedPublisher(Node):
    def __init__(self):
        super().__init__("mismatched_publisher")
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.publisher_ = self.create_publisher(String, "/scan", qos)
        self.timer = self.create_timer(1.0, self.tick)
        self.count = 0

    def tick(self):
        msg = String()
        msg.data = f"reading #{self.count}"
        self.count += 1
        self.publisher_.publish(msg)
        self.get_logger().info(f"published: {msg.data}")


def main():
    rclpy.init()
    node = MismatchedPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
