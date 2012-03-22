from distutils.core import setup

with open("README") as f:
    readme = f.read()

setup(
    name="gizz",
    version="0.5",
    description="Command-line interface to GitHub.",
    long_description=readme,
    author="Ross Lagerwall",
    author_email="rosslagerwall@gmail.com",
    url="https://github.com/rosslagerwall/gizz",
    license="GNU General Public License Version 3+",
    packages=["gizz"],
    scripts=["bin/gizz"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Topic :: Software Development :: Version Control"
        ],
    )
