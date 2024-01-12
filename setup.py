"""stac-fastapi-authorization"""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    desc = f.read()

exec(open("stac_fastapi_authorization/version.py").read())

install_requires = [
    "stac-fastapi.api>=2.4.7",
]

extra_reqs = {
    "dev": ["black>=22.3.0", "flake8>=4.0.1", "pyright>=1.1.251"],
}


setup(
    name="stac-fastapi-authorization",
    description=("An authorization framework for STAC FastAPI"),
    long_description=desc,
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="STAC FastAPI Authorization",
    maintainer="Edward Keeble",
    maintainer_email="edward@developmentseed.org",
    url="https://github.com/edkeeble/stac-fastapi-authorization",
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
    version=__version__,   # type: ignore
)
