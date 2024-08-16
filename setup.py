# type: ignore
"""fastapi-authorization-gateway"""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    desc = f.read()

exec(open("fastapi_authorization_gateway/version.py").read())

install_requires = [
    "fastapi>=0.73.0",
]

extra_reqs = {
    "dev": [
        "black>=22.3.0",
        "flake8>=4.0.1",
        "pyright>=1.1.251",
        "pytest>=7.4.4",
        "httpx==0.26.0",
    ],
}


setup(
    name="fastapi-authorization-gateway",
    description=("A route-based authorization framework for FastAPI"),
    long_description=desc,
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="FastAPI Authorization",
    maintainer="Edward Keeble",
    maintainer_email="edward@developmentseed.org",
    url="https://github.com/edkeeble/fastapi-authorization-gateway",
    license="MIT",
    packages=find_namespace_packages(
        exclude=[
            "tests",
        ]
    ),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
    tests_require=extra_reqs["dev"],
    extras_require=extra_reqs,
    version=__version__,  # noqa: F821
)
