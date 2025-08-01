# SnaarfBot Web App and API

This is the source code for the SnaarfBot.com website and the SnaarfBot internal API. These support the [SnaarfBot](https://github.com/BBBThunda/snaarfbot) Twitch chat bot.


## Platform Requirements

The application can be run in two ways:

### Docker Setup (Recommended)
- Docker Engine or Docker Desktop
- Docker Compose

Note: Docker Desktop includes both Docker and Docker Compose and is recommended for Windows and macOS users. Linux users typically use Docker Engine directly, which requires separate installation of Docker Compose.

### Manual Setup (Not Actively Supported - check dockerfile for most up-to-date dependencies)
- Debian 12.10 or Windows
- PostgreSQL 14 (with user/db created)
- Python 3.10.12
- pip 22.0.2
- pytest 7.4.2
- Redis (for session management)

#### Database

For the PostreSQL server we recommend you create a database `snaarf_app` owned by user `snaarf_app` that matches the credentials mentioned below in the Environment section. Make sure user `snaarf_app` has a secure password.

## Commands

A quick description of the commands necessary to test will eventually be added to a CONTRIBUTING doc and maybe a Makefile. These will do for now:


## Initial Setup
Here's how to set up your environment to work with this repo once you've cloned it.
Note: all commands should be run from the project root

### Environment
A `.env.example` file is provided with default values for local development. Create your `.env` file by copying it:
```bash
cp .env.example .env
```

Then adjust the following values in `.env` based on your configuration. This file is ignored by git. DO NOT commit any passwords or sensitive data to this repository.
```dosini
# PostgreSQL DB Connection
DB_PASS=passwordForDbUser

# Redis Configuration
REDIS_AUTH_PASSWORD=secureRedisPassword

# Application Security
APP_SECRET_KEY=secureSecretKeyForSessionSigning

# Twitch API Configuration
TWITCH_CLIENT_ID=yourTwitchClientId
TWITCH_SECRET=yourTwitchClientSecret
TWITCH_REDIRECT_URI=http://localhost:8000/twitch/auth_redirect
```

Note: For Twitch API credentials, you'll need to:
1. Create a Twitch Developer account
2. Register your application
3. Get your Client ID and Client Secret
4. Add your redirect URI to the allowed redirect URIs in your Twitch Developer Console

### Automatic Setup With Docker (Recommended)
The Docker setup uses the official Python 3.10 slim image based on Debian 12.10 (Bookworm). This is the recommended and actively supported method.

#### Build and run the Containers
If you have Docker installed, the setup is as easy as running the following commands from the repo root:
```bash
docker-compose up --build
```
This will start three containers:
- The SnaarfBot application
- A PostgreSQL 14 database
- A Redis server for session management

The application will be available at http://localhost:8000

Note: The application code is mounted as a volume, so any changes you make to the code will be reflected immediately without needing to rebuild the container.

#### Executing commands in a running container
First, get the CONTAINER_ID from docker:
```bash
docker ps
```
Then use the exec command to open a shell inside the container:
```bash
docker exec -it <CONTAINER_ID> /bin/bash
```

#### Monitoring Server Logs
To monitor server logs, use:
```bash
docker-compose logs -f
```

To monitor logs for a specific service:
```bash
docker-compose logs -f app      # Application logs
docker-compose logs -f postgres # Database logs
docker-compose logs -f redis    # Redis logs
```

### Manual Setup (Not Actively Supported)
The following steps should work, but will at least get you moving in the right direction. Be aware that this method is not actively supported like the Docker method so you may need to make some tweaks. Feel free to suggest corrections or submit a pull request if you run into issues.

#### Virtual Environment and Platform Dependencies
##### Linux/Debian
Install platform dependencies - the `apt-get` commands are meant to be run on Debian 12.10 - check the dockerfile for the most up-to-date versions/commands
```bash
sudo apt-get -y update && sudo apt-get -y upgrade
sudo apt-get install python3.10 python3.10-venv python3-pip python3-setuptools
```

For Production deploy environments, also install:
```bash
sudo apt-get install python3.10-dev build-essential libssl-dev libffi-dev
```

##### Windows
Install Python 3.10 from the [official Python website](https://www.python.org/downloads/). Make sure to check "Add Python to PATH" during installation.

Create/activate a virtual environment for the repository:
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

If you get a PowerShell execution policy error, run:
```bash
Set-ExecutionPolicy -Scope CurrentUser Unrestricted
```

#### Install Python and App Dependencies
Install the required Python packages:
```bash
pip install wheel uwsgi flask
pip install -r requirements.txt
```

#### Network Access
##### Linux/Debian
If you plan on serving the app to external machines on your subnet, update firewall rules:
```bash
sudo ufw allow 8000
```

##### Windows
Windows Defender Firewall may prompt you to allow network access when you start the server. If it doesn't, you may need to manually add an inbound rule for port 8000 in Windows Defender Firewall settings.

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

##### Using Docker (Recommended)
```bash
# Run all tests
docker-compose up test

# Run specific test file
docker-compose run test pytest tests/test_oauth.py

# Run specific test function
docker-compose run test pytest tests/test_oauth.py::test_auth_redirect_success

# Run tests with output (for debugging)
docker-compose run test pytest -s tests
```

##### Manual Setup
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_oauth.py

# Run specific test function
pytest tests/test_oauth.py::test_auth_redirect_success

# Run tests with output (for debugging)
pytest -s tests
```
