from setuptools import find_packages, setup

package_name = 'comm_layer'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/network_simulation.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='tagnon',
    maintainer_email='privaeloking@gmail.com',
    description='ROS topic-level communication disruption layer for resilient multi-robot simulation.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'network_simulator_node = comm_layer.network_simulator_node:main',
        ],
    },
)
