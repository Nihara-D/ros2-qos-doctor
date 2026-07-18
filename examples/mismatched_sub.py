"""
Subscribes to /scan requiring RELIABLE delivery -- a common default for
nodes that assume every message matters (e.g. costmap-style consumers).

Because the publisher in mismatched_pub.py is BEST_EFFORT, this subscriber
will never receive a single message, and neither side will log an error.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import String


class MismatchedSubscriber(Node):
    def __init__(self):
        super().__init__("mismatched_subscriber")
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.subscription = self.create_subscription(
            String, "/scan", self.callback, qos
        )

    def callback(self, msg):
        self.get_logger().info(f"received: {msg.data}")


def main():
    rclpy.init()
    node = MismatchedSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
