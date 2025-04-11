# SnaarfBot Web App and API

This is the source code for the SnaarfBot.com website and the SnaarfBot internal API. These support the [SnaarfBot](https://github.com/BBBThunda/snaarfbot) Twitch chat bot.


## Platform Requirements

- Ubuntu 22.04
- PostgreSQL 14 (with user/db created)
- Python 3.10.12
- pip 22.0.2
- pytest 7.4.2

#### Database

For the PostreSQL server we recommend you create a database `snaarf_app` owned by user `snaarf_app` that matches the credentials mentioned below in the `.env` File section. Make sure user `snaarf_app` has a secure password.

#### `.env` File

Create a `.env` file in the project root with the following variables. Adjust the values based on how you configured your local PostgreSQL server/db/user. This file is ignored by git. DO NOT commit any passwords or sensitive data to this repository.
```dosini
# PostgreSQL DB Connection
DB_USER=snaarf_app
DB_PASS=passwordForDbUser
DB_HOST=localhost
DB_PORT=5432
DB_NAME=snaarf_app
DEV_HOST=localhost
DEV_PORT=8000
```


## Commands

A quick description of the commands necessary to test will eventually be added to a CONTRIBUTING doc and maybe a Makefile. These will do for now:


## Initial Setup
Here's how to set up your environment to work with this repo once you've cloned it.
Note: all commands should be run from the project root

### Environment
Environment variables are defined in `.env`. This file is not part of the repository. You can create a copy of `.env.example` with the following command:
```bash
cp .env.example .env
```
Now open .env and replace all of the password placeholders with secure password values. Please use secure values since Twitch doesn't have dev/staging servers, so you will be testing with live Twitch user/chat data. You need to get the TWITCH_CLIENT_ID and TWITCH_SECRET from the twitch.tv website.


### Automatic Setup With Docker
#### Build and run the Container
If you have Docker the setup is as easy as running the following commands from the repo root:
```bash
docker build -f .\container\snaarf-app.dockerfile -t snaarf-app:0.1 .
docker run --env-file .env -p 8000:8000 snaarf-app:0.1
```
You should have a running app server with an initialized Redis instance for handling session data. This is the recommended/supported method.

#### Executing commands in a running container
First, get the CONTAINER_ID from docker:
```bash
docker ps
```
Then use the exec command to open a shell inside the container:
```bash
docker exec -it <CONTAINER_ID> /bin/bash
```

### Manual Setup
The following steps should work, but will at least get you moving in the right direction. Be aware that this method is not actively supported like the Docker method so you may need to make some tweaks. Feel free to suggest corrections or submit a pull request if you run into issues.

#### Virtual Environment and Platform Dependencies
Install platform dependencies - the `apt-get` commands are meant to be run on Ubuntu 22.04.
```bash
sudo apt-get -y update && sudo apt-get -y upgrade
sudo apt-get install python3.10 python3.10-venv python3-pip python3-setuptools
```

Create/activate a virtual environment for the repository.
```bash
python -m venv .venv
source .venv/bin/activate
```

If you're using powershell, the source command won't work; do this instead:
```bash
Set-ExecutionPolicy -Scope CurrentUser Unrestricted
.\.venv\Scripts\activate
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
On Windows you will instead get a popup when you start the server asking you to allow network access.

Now you can install the remaining python/pip dependencies. Make sure you do this every time your requirements.txt file changes.
```bash
pip install -r requirements.txt 
```

#### Code Linting and Formatting
All changes involving .py files must pass these checks. The pre-commit hook will run these for you, but if you want to run them manually, use the following commands:
Note: You can replace `/snaarf_app /tests` with your changed files or you can just run these as-is and ignore any errors that aren't related to your changes.
```bash
flake8 snaarf_app/ tests/
black -l 79 snaarf_app/ tests/
```

Note: `black` will automatically fix errors and modify your files. If you want to run it without modifying any files, use the `--check` switch.
```bash
black -l 79 --check snaarf_app/ tests/
```


#### Run tests
Tests must also pass before you push code changes. A code coverage target will be enforced eventually. For now you can manually open up /tmp/coverage.html in a browser to see the code coverage report.
```bash
pytest tests/
```


#### Run tests with output
For when you need to stick a print() statement in your test files to troubleshoot.
```bash
pytest -s tests
```
