from setuptools import setup, find_packages

setup(
    name="secbrowser",
    version="0.0.1",
    packages=find_packages(),
    install_requires=["flask"
    ],
    include_package_data=True,
    package_data={
        'secbrowser': ['templates/*.html', 'static/css/*.css', 'static/js/*.js'],
    },
    author="John Friedman",
    email="johnfriedman@datamule.xyz",
    description="A simple interface to interact with SEC filings."
)