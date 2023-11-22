from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, make_response, render_template, request
import os
import requests
from urllib.parse import urlencode
import uuid

load_dotenv()

app = Flask(__name__)

BASE_TWITCH_AUTH_URI = 'https://id.twitch.tv/oauth2/authorize'
BASE_TWITCH_TOKEN_URI = 'https://id.twitch.tv/oauth2/token'
TWITCH_API_SCOPE = (
    'channel:manage:polls+channel:read:polls' + '+openid+user:read:email'
)
TWITCH_TOKEN_TYPE = 'bearer'


def refresh_token(token):
    # CHECK WHETHER TOKEN IS VALID AND REFRESH IF NEEDED
    return False


def check_logged_in():
    return False


@app.route('/')
@app.route('/index')
def index():
    # Get state FROM COOKIE OR GENERATE A NEW ONE
    if 'state' in request.cookies:
        state = request.cookies.get('state')
    else:
        state = str(uuid.uuid4())
        # STORE NEW STATE IN DB (maybe not necessary)

    is_logged_in = check_logged_in()

    if is_logged_in:
        # If logged in, return home template
        template = render_template('home.html', title='SnaarfBot')
    else:
        # If not logged in, return index template
        # Build URL for login link
        auth_parameters = {
            'response_type': 'code',
            'client_id': os.getenv('TWITCH_CLIENT_ID'),
            'redirect_uri': os.getenv('TWITCH_REDIRECT_URI'),
            'state': state,
        }
        twitch_auth_link_uri = (
            BASE_TWITCH_AUTH_URI + '?' + urlencode(auth_parameters)
        )
        # Add scope manually - Twitch doesn't like urlencoded scope values
        twitch_auth_link_uri += '&scope=' + TWITCH_API_SCOPE
        # Return index template
        template = render_template(
            'index.html',
            title='SnaarfBot',
            twitch_uri=twitch_auth_link_uri,
            debug_data=str(state),
        )

    response = make_response(template)
    response.set_cookie('state', state)
    return response


@app.route('/twitch/auth_redirect')
def auth_redirect():
    # IS THERE A WAY TO ENSURE REDIRECT ACTUALLY CAME FROM TWITCH? (PROB NOT)

    # REQUEST SHOULD CONTAIN state AND AN auth_code
    if 'state' not in request.args or 'code' not in request.args:
        app.logger.error(
            'Bad input received from Twitch auth_redirect.'
            + ' Request args: %s',
            repr(request.args),
        )
        # TODO: RETURN 404 PAGE
        return ''

    # TODO: Handle use case where twitch sends error

    auth_code = request.args['code']

    # Make sure request state matches cookie state
    if request.args['state'] != request.cookies.get('state'):
        app.logger.error(
            'Insecure auth_redirect request detected.' + ' Request args: %s',
            repr(request.args),
        )
        # TODO:  RETURN 404 PAGE
        return ''

    # If Twitch changes the scope, log it, so we can investigate
    if request.args['scope'] != request.cookies.get('scope'):
        app.logger.warn(
            'Scope received from Twitch auth does not match '
            + 'requested scope. requested:|'
            + str(request.args['scope'])
            + '| received: |'
            + str(request.cookies.get('scope'))
            + '|'
        )

    # Use code to request a new access_token
    post_data = {
        'client_id': os.getenv('TWITCH_CLIENT_ID'),
        'client_secret': os.getenv('TWITCH_SECRET'),
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': os.getenv('TWITCH_REDIRECT_URI'),
        # TODO: Why is redirect_uri required???
    }
    token_response = requests.post(
        url=BASE_TWITCH_TOKEN_URI,
        data=post_data,
    )
    response_data = token_response.json()

    # Check for error response
    # TODO: figure out how to do schema validation later
    if 'error' in response_data or 'error_description' in response_data:
        app.logger.error(
            'Error requesting access token. response_data: '
            + repr(response_data)
        )
        return ''

    # Validate "valid" response
    if (
        'access_token' not in response_data
        or 'expires_in' not in response_data
        or 'refresh_token' not in response_data
        or 'token_type' not in response_data
        or response_data['token_type'] != TWITCH_TOKEN_TYPE
    ):
        app.logger.error(
            'Bad response from token server. '
            + 'post_data: '
            + repr(post_data)
            + 'response_data: '
            + repr(response_data)
        )
        return ''

    access_token = response_data['access_token']
    expires_in = int(response_data['expires_in'])
    expires = datetime.now() + timedelta(seconds=expires_in)
    # refresh_token = response_data['refresh_token']

    # Store tokens in DB with expire time
    # LEFT OFF HERE!!!

    # Create response
    template = render_template(
        'auth_redirect.html',
        title='SnaarfBot',
        debug_data=repr(request.args) + repr(response_data) + repr(expires),
    )
    response = make_response(template)
    # Store token in cookie
    response.set_cookie('access_token', access_token)
    return response


if __name__ == '__main__':
    app.run(host=os.getenv('DEV_HOST'), port=os.getenv('DEV_PORT'))
