from setuptools import find_packages, setup

package_name = 'uav_observer'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='privaelo',
    maintainer_email='privaeloking@gmail.com',
    description='UAV aerial observer node',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'target_observer_node = uav_observer.target_observer_node:main',
        ],
    },
)
