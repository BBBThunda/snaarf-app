# SnaarfBot Web App and API

This is the source code for the SnaarfBot.com website and the SnaarfBot internal API. These support the [SnaarfBot](https://github.com/BBBThunda/snaarfbot) Twitch chat bot.


## Platform Requirements

- Ubuntu 22.04
- PostgreSQL 14 (with user/db created)
- Python 3.10.12
- pip 22.0.2
- pytest 7.4.2

#### Database

For the PostreSQL server we recommend you create a database `snaarf_app` owned by user `snaarf_app` that matches the credentials mentioned below in the `.env` File section.

#### `.env` File

Create a `.env` file in the project root with the following variables. Adjust the values based on how you configured your local PostgreSQL server/db/user. This file is ignored by git. DO NOT commit any passwords or sensitive data to this repository.
```dosini
# PostgreSQL DB Connection
DB_USER=snaarf_app
DB_PASS=passwordForDbUser
DB_HOST=localhost
DB_PORT=5432
DB_NAME=snaarf_app
```


## Commands

A quick description of the commands necessary to test will eventually be added to a CONTRIBUTING doc and maybe a Makefile. These will do for now:


### Initial Setup
Here's how to set up your environment to work with this repo once you've cloned it.
Note: all commands should be run from the project root


#### Virtual Environment and Platform Dependencies
Install platform dependencies - the `apt-get` commands are meant to be run on Ubuntu 22.04.
```bash
sudo apt-get -y update && sudo apt-get -y upgrade
sudo apt-get install python3.10 python3.10-venv python3.10-pip python3-setuptools
```

Create/activate a virtual environment for the repository.
```bash
python -m venv .venv
source .venv/bin/activate
```

For Production deploy environments, also install the following dependencies.
```bash
sudo apt-get install python3.10-dev build-essential libssl-dev libffi-dev
pip install wheel uwsgi flask
```

If you plan on serving the app to external machines on your subnet, you may need to update firewall rules.
```bash
sudo ufw allow 8000
```

Now you can install the remaining python/pip dependencies.
```bash
pip install -r requirements.txt 
```

#### Code Linting and Formatting
All changes involving .py files must pass these checks. The pre-commit hook will run these for you, but if you want to run them manually, use the following commands:
Note: You can replace `/snaarf_app /tests` with your changed files or you can just run these as-is and ignore any errors that aren't related to your changes.
```bash
flake8 /snaarf_app /tests
black /snaarf_app /tests
```

Note: `black` will automatically fix errors and modify your files. If you want to run it without modifying any files, use the `--check` switch.
```bash
black --check /snaarf_app /tests
```


#### Run tests
Tests must also pass before you push code changes. A code coverage target will be enforced eventually. For now you can manually open up /tmp/coverage.html in a browser to see the code coverage report.
```bash
pytest tests
```


#### Run tests with output
For when you need to stick a print() statement in your test files to troubleshoot.
```bash
pytest -s tests
```
