# Contributing

## Dev env setup

Prerequisites:
- at least a python 3.6 (hint use pyenv for installing multiple python versions on your system without messing up with
the distro installed python)
- [poetry](https://python-poetry.org/) for setting up the virtualenv and managing the project and its dependencies
(hint use [pipx](https://pipxproject.github.io/pipx/) in order to install this tool system wide but using its own
dedicated virtualenv in order not to install poetry dependencies in the distro installed python)


Fast path to installation and testing:

```shell 
git clone https://github.com/GigiusB/django-relativedelta.git
cd django-relativedelta 
git checkout features/tox
poetry install
poetry shell
pytest
```

In order to quickly test with another DB: ```DBENGINE=sqlite pytest```

*NB:* so far only postgres, mysql and sqlite are configured for tests (see [tox.ini](./tox.ini))

For a full test: ```tox```

For building the dist package: ```poetry build -f sdist```

For producing the requirements.txt (should you need it):
```poetry export -f requirements.txt -o dist/requirements.txt```

For producing the requirements-dev.txt (should you need it):
```poetry export --dev -f requirements.txt -o dist/requirements-dev.txt```