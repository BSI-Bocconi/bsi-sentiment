from bsi_sentiment import __title__, __author__, __email__, __url__, __version__

import setuptools

with open("README.md") as f:
    long_description = f.read()

with open("requirements.txt") as f:
    required = f.readlines()[:-2]

setuptools.setup(
    name=__title__,
    version=__version__,
    author=__author__,
    author_email=__email__,
    description="BSI Tool for Sentiment Analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=__url__,
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    setup_requires=['wheel'],
    install_requires=required,
    extras_require={
        ':python_version < "3.8"': ['snscrape >= 0.3.4'],
        ':python_version >= "3.8"': ['snscrape @ git+https://github.com/JustAnotherArchivist/snscrape.git']
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3"
    ],
    entry_points={
        'console_scripts': [
            'sentiment=bsi_sentiment.bsi_sentiment:main'
        ]
    }
)
