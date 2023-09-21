# SnaarfBot Web App and API

This is the source code for the SnaarfBot.com website and the SnaarfBot internal API. These support the [SnaarfBot](https://github.com/BBBThunda/snaarfbot) Twitch chat bot.

## Platform Requirements

- Python 3.10.12
- pip 22.0.2
- pytest 7.4.2

## Commands

A quick description of the commands necessary to test will eventually be added to a CONTRIBUTING doc and maybe a Makefile. These will do for now:

#### Virtual Environment
You can create any virtual env you feel comfortable with. Here's the recommended one:
```bash
python -m venv .venv
```

#### Run tests
These tests must pass before you push code changes. You can open up /tmp/coverage.html in a browser to see the code coverage report
```bash
pytest tests
```

#### Run tests with output
For when you need to stick a print() statement in your tests to troubleshoot
```bash
pytest -s tests
```

#### Lint code
This must also pass before you push code changes
```bash
flake8
```
