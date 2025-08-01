from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, make_response, render_template, request, session, redirect, url_for
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import os
import redis
import requests
from urllib.parse import urlencode
import uuid
from .redis_wrapper import RedisWrapper

load_dotenv()

app = Flask(__name__)

# Configure Sessions
# Use Redis for storing the session data on the server-side
session_cache = RedisWrapper(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', '6379')),
    password=os.getenv('REDIS_AUTH_PASSWORD'),
    db=0
)
# Used to cryptographically-sign session ID cookies
app.secret_key = os.getenv('APP_SECRET_KEY')
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = session_cache._redis  # Use the underlying Redis instance for Flask-Session
# Create and initialize Flask-Session object AFTER `app` has been configured
server_session = Session(app)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Constants for Twitch Oauth2
BASE_TWITCH_AUTH_URI = 'https://id.twitch.tv/oauth2/authorize'
BASE_TWITCH_TOKEN_URI = 'https://id.twitch.tv/oauth2/token'
TWITCH_API_SCOPE = (
    'channel:manage:polls+channel:read:polls' + '+openid+user:read:email'
)
TWITCH_TOKEN_TYPE = 'bearer'

def refresh_token(user_id):
    """Refresh the access token using the refresh token."""
    try:
        # Get current tokens from Redis
        tokens = session_cache.hgetall(f'user:{user_id}')
        if not tokens:
            app.logger.error('No tokens found for user %s', user_id)
            return False

        refresh_token = tokens['refresh_token']
        
        # Request new token from Twitch
        post_data = {
            'client_id': os.getenv('TWITCH_CLIENT_ID'),
            'client_secret': os.getenv('TWITCH_SECRET'),
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        response = requests.post(
            BASE_TWITCH_TOKEN_URI,
            data=post_data,
            timeout=5
        )
        response.raise_for_status()
        response_data = response.json()

        # Validate response
        if ('access_token' not in response_data or 
            'expires_in' not in response_data or 
            'refresh_token' not in response_data):
            app.logger.error('Invalid token refresh response: %s', response_data)
            return False

        # Update tokens in Redis
        expires_in = int(response_data['expires_in'])
        expires = datetime.now() + timedelta(seconds=expires_in)
        
        session_cache.hset(f'user:{user_id}', {
            'access_token': response_data['access_token'],
            'refresh_token': response_data['refresh_token'],
            'expires_at': expires.isoformat()
        })
        session_cache.expire(f'user:{user_id}', expires_in)
        
        return True
    except (requests.exceptions.RequestException, redis.RedisError, UnicodeError) as e:
        app.logger.error('Failed to refresh token: %s', str(e))
        return False

def get_user_id_controller():
    """Controller function to get user ID from session."""
    return get_user_id(session)

def get_user_id(session_obj):
    """Business logic to get user ID from session."""
    session_id = session_obj.get('session_id')
    if not session_id:
        return None
    try:
        return session_cache.get(f'session:{session_id}')
    except (redis.RedisError, ValueError) as e:
        app.logger.error('Error getting user_id from session: %s', str(e))
        return None

def set_user_id_controller(user_id):
    """Controller function to set user ID in session."""
    session_id = str(uuid.uuid4())
    return set_user_id(session_id, user_id, session)

def set_user_id(session_id, user_id, session_obj):
    """Business logic to set user ID in session."""
    try:
        # Store session_id -> user_id mapping in Redis
        session_cache.set(f'session:{session_id}', user_id)
        # Store session_id in signed cookie - ensure it's a string
        session_obj['session_id'] = str(session_id)
        return True
    except (redis.RedisError, UnicodeEncodeError) as e:
        app.logger.error('Error setting user_id in session: %s', str(e))
        return False

def check_logged_in(user_id):
    """Business logic to check if user is logged in and has valid tokens."""
    if not user_id:
        return False

    try:
        tokens = session_cache.hgetall(f'user:{user_id}')
        if not tokens:
            return False
        
        # Check if token is expired or about to expire (within 5 minutes)
        expires_at = datetime.fromisoformat(tokens['expires_at'])
        if datetime.now() + timedelta(minutes=5) >= expires_at:
            # Try to refresh the token
            if not refresh_token(user_id):
                return False
            
        app.logger.debug('User %s is logged in', user_id)
        return True
    
    except (redis.RedisError, ValueError, KeyError) as e:
        app.logger.error('Error checking login status: %s', str(e))
        return False

@app.route('/')
@app.route('/index')
def index():
    # Get state from cookie or generate a new one
    if 'state' in request.cookies:
        state = request.cookies.get('state')
    else:
        state = str(uuid.uuid4())

    is_logged_in = check_logged_in(get_user_id_controller())

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
        )

    response = make_response(template)
    response.set_cookie('state', str(state))
    response.set_cookie('scope', str(TWITCH_API_SCOPE))
    return response


@app.route('/twitch/auth_redirect')
def auth_redirect():
    # REQUEST SHOULD CONTAIN state AND AN auth_code
    if 'state' not in request.args or 'code' not in request.args:
        error_message = 'Bad input received from Twitch auth_redirect.'
        app.logger.error(
            error_message
            + ' Request args: %s',
            repr(request.args),
        )

        # RETURN 404 PAGE WITH ERROR MESSAGE
        return render_template('404.html', error_message=error_message)

    # TODO: Handle use case where twitch sends error


    auth_code = request.args['code']

    # Make sure request state matches cookie state
    if request.args['state'] != request.cookies.get('state'):
        error_message = 'Insecure auth_redirect request detected.'
        app.logger.error(
            error_message
            + ' Request args: %s',
            repr(request.args),
        )
        # RETURN 404 PAGE WITH ERROR MESSAGE
        return render_template('404.html', error_message=error_message)

    # If Twitch changes the scope, log it, so we can investigate
    if request.args['scope'] != request.cookies.get('scope'):
        app.logger.warning(
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
            'Error requesting access token. Error: %s',
            response_data.get('error_description', response_data.get('error', 'Unknown error'))
        )
        return ''

    # Validate response
    if (
        'access_token' not in response_data
        or 'expires_in' not in response_data
        or 'refresh_token' not in response_data
        or 'token_type' not in response_data
        or response_data['token_type'] != TWITCH_TOKEN_TYPE
    ):
        app.logger.error(
            'Bad response from token server. Missing required fields. '
            'Response keys: %s',
            list(response_data.keys())
        )
        return ''

    access_token = response_data['access_token']
    expires_in = int(response_data['expires_in'])
    expires = datetime.now() + timedelta(seconds=expires_in)
    refresh_token = response_data['refresh_token']

    # Get user info from Twitch
    try:
        user_info_response = requests.get(
            'https://api.twitch.tv/helix/users',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Client-Id': os.getenv('TWITCH_CLIENT_ID')
            },
            timeout=5  # Add timeout to prevent hanging
        )
        user_info_response.raise_for_status()  # Raise exception for bad status codes
        user_data = user_info_response.json()
    except requests.exceptions.RequestException as e:
        app.logger.error('Failed to get user info from Twitch API: %s', str(e))
        return render_template('404.html', error_message='Failed to connect to Twitch API')
    except ValueError as e:
        app.logger.error('Invalid JSON response from Twitch API: %s', str(e))
        return render_template('404.html', error_message='Invalid response from Twitch API')
    
    if 'data' not in user_data or not user_data['data']:
        app.logger.error('No user data in Twitch API response. Response keys: %s', list(user_data.keys()))
        return render_template('404.html', error_message='No user information found in Twitch response')

    try:
        user_id = user_data['data'][0]['id']
    except (KeyError, IndexError) as e:
        app.logger.error('Invalid user data structure: %s', str(e))
        return render_template('404.html', error_message='Invalid user data structure from Twitch')

    # Store tokens in Redis with expiration
    try:
        session_cache.hset(f'user:{user_id}', {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_at': expires.isoformat()
        })
        session_cache.expire(f'user:{user_id}', expires_in)
    except redis.RedisError as e:
        app.logger.error('Failed to store tokens in Redis: %s', str(e))
        return render_template('404.html', error_message='Failed to store authentication data')

    # Create response
    try:
        # Store user_id securely in session
        if not set_user_id_controller(user_id):
            return render_template('404.html', error_message='Failed to create session')
        
        # Redirect to home page after successful OAuth
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error('Failed to create response: %s', str(e))
        return render_template('404.html', error_message='Failed to create response')


if __name__ == '__main__':
    app.run(host=os.getenv('DEV_HOST'), port=os.getenv('DEV_PORT'))
