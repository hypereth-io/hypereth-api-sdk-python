"""
Setup configuration for HyperETH SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hypereth-sdk",
    version="0.1.0",
    author="HyperETH",
    author_email="hello@hypereth.io",
    description="Python SDK for HyperETH",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hypereth-io/hypereth-api-sdk-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Security :: Cryptography",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "eth-account>=0.8.0",
        "web3>=6.0.0",
        "aiohttp>=3.8.0",
        "websockets>=15.0.1",
        "hyperliquid-python-sdk>=0.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "types-requests>=2.28.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.10.0",
            "responses>=0.23.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
