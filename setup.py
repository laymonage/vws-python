"""Setup script for VWS Python, a wrapper for Vuforia's Web Services APIs."""

from setuptools import find_packages, setup

import versioneer

# We use requirements.txt instead of just declaring the requirements here
# because this helps with Docker package caching.
with open('requirements.txt') as requirements:
    INSTALL_REQUIRES = requirements.readlines()

# We use dev-requirements.txt instead of just declaring the requirements here
# because Read The Docs needs a requirements file.
with open('dev-requirements.txt') as dev_requirements:
    DEV_REQUIRES = dev_requirements.readlines()

setup(
    version=versioneer.get_version(),  # type: ignore
    cmdclass=versioneer.get_cmdclass(),  # type: ignore
    package_data={'vws': ['py.typed']},
    install_requires=INSTALL_REQUIRES,
    extras_require={'dev': DEV_REQUIRES},
)
