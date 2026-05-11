from setuptools import find_packages, setup

package_name = 'ugv_nav'

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
    description='UGV goal-following node for MRTA demo',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'ugv_goal_follower_node = ugv_nav.ugv_goal_follower_node:main',
            'assignment_marker_node = ugv_nav.assignment_marker_node:main',
            'demo_display_node = ugv_nav.demo_display_node:main',
        ],
    },
)
