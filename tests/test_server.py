# import pytest
# import sys

from snaarf_app.server import app, index


def test_server_index_returns_rendered_template():
    """Just check for an expected piece of the result"""
    with app.app_context(), app.test_request_context():
        indexOutput = index()
        assert "<title>SnaarfBot</title>" in indexOutput
