from setuptools import setup

package_name = "nav_engine"

setup(
    name=package_name,
    version="1.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="NavEngine API",
    maintainer_email="founder@navengine.io",
    description="Navigation engine failover logic, API layer, and simulation tools.",
    license="GPL-3.0-only",
)
