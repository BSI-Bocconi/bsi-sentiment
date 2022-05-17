from bsi_sentiment import __title__, __author__, __email__, __url__, __version__

import setuptools


with open("README.md") as f:
    long_description = f.read()

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
    python_requires='>=3.8',
    setup_requires=['wheel'],
    install_requires=[
        "nltk~=3.7",
        "snscrape~=0.4.3.20220106",
        "textblob~=0.17.1",
        "tqdm~=4.62.3",
        "tweepy~=4.9.0",
    ],
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
    },
)
