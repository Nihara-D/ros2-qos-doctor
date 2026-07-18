from setuptools import setup, find_packages

setup(
    name="ros2-qos-doctor",
    version="0.1.0",
    description="Detect QoS incompatibilities between ROS 2 publishers and subscribers.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Nihara Randini",
    author_email="shniharard@gmail.com",
    license="Apache-2.0",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "ros2-qos-doctor=ros2_qos_doctor.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Topic :: Scientific/Engineering :: Robotics",
    ],
)
