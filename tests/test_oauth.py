import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from snaarf_app.server import (
    refresh_token,
    get_user_id,
    set_user_id,
    check_logged_in,
    auth_redirect,
    index,
    app
)

@pytest.fixture
def mock_redis():
    """Mock RedisWrapper for testing."""
    # Mock session_cache (our RedisWrapper instance) instead of trying to mock Flask's session
    # This avoids "Working outside of request context" errors
    with patch('snaarf_app.server.session_cache') as mock:
        yield mock

@pytest.fixture
def mock_requests():
    """Mock requests for testing."""
    with patch('snaarf_app.server.requests') as mock:
        yield mock

@pytest.fixture
def client():
    """Create a test client for the app."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_refresh_token_success(mock_redis, mock_requests):
    """Test successful token refresh."""
    # Setup
    user_id = '123'
    old_refresh_token = 'old_refresh_token'
    new_access_token = 'new_access_token'
    new_refresh_token = 'new_refresh_token'
    expires_in = 3600

    mock_redis.hgetall.return_value = {
        'refresh_token': old_refresh_token
    }

    mock_response = MagicMock()
    mock_response.json.return_value = {
        'access_token': new_access_token,
        'refresh_token': new_refresh_token,
        'expires_in': expires_in
    }
    mock_requests.post.return_value = mock_response

    # Test
    result = refresh_token(user_id)

    # Verify
    assert result is True
    mock_redis.hset.assert_called_once()
    mock_redis.expire.assert_called_once_with(f'user:{user_id}', expires_in)

def test_refresh_token_no_tokens(mock_redis):
    """Test token refresh when no tokens exist."""
    # Setup
    user_id = '123'
    mock_redis.hgetall.return_value = None

    # Test
    result = refresh_token(user_id)

    # Verify
    assert result is False
    mock_redis.hset.assert_not_called()

def test_get_user_id_success(mock_redis, client):
    """Test successful user ID retrieval."""
    # Setup
    session_id = 'session123'
    user_id = 'user123'
    mock_redis.get.return_value = user_id

    # Use client.session_transaction() to properly set up Flask session context
    # This avoids "Working outside of request context" errors
    with client.session_transaction() as session:
        session['session_id'] = session_id
        result = get_user_id(session)

    # Verify
    assert result == user_id
    mock_redis.get.assert_called_once_with(f'session:{session_id}')

def test_get_user_id_no_session(client):
    """Test user ID retrieval when no session exists."""
    # Test
    with client.session_transaction() as session:
        result = get_user_id(session)

    # Verify
    assert result is None

def test_set_user_id_success(mock_redis, client):
    """Test successful user ID setting."""
    # Setup
    session_id = 'session123'
    user_id = 'user123'
    mock_redis.set.return_value = True

    # Use client.session_transaction() to properly test session operations
    # This provides a real Flask session context instead of trying to mock it
    with client.session_transaction() as session:
        result = set_user_id(session_id, user_id, session)
        assert result is True
        assert 'session_id' in session
        assert session['session_id'] == session_id

    mock_redis.set.assert_called_once()

def test_check_logged_in_valid_token(mock_redis):
    """Test login check with valid token."""
    # Setup
    user_id = 'user123'
    expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
    mock_redis.hgetall.return_value = {
        'expires_at': expires_at
    }

    result = check_logged_in(user_id)
    assert result is True

def test_check_logged_in_expired_token(mock_redis):
    """Test login check with expired token."""
    # Setup
    user_id = 'user123'
    expires_at = (datetime.now() - timedelta(hours=1)).isoformat()
    mock_redis.hgetall.return_value = {
        'expires_at': expires_at
    }

    with patch('snaarf_app.server.refresh_token', return_value=True):
        result = check_logged_in(user_id)
        assert result is True
        mock_redis.hgetall.assert_called_once_with(f'user:{user_id}')

def test_auth_redirect_success(mock_redis, mock_requests, client):
    """Test successful OAuth redirect."""
    # Setup
    auth_code = 'auth123'
    state = 'state123'
    scope = 'channel:manage:polls+channel:read:polls+openid+user:read:email'
    access_token = 'token123'
    refresh_token = 'refresh123'
    expires_in = 3600
    user_id = 'user123'

    mock_response = MagicMock()
    mock_response.json.return_value = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': expires_in,
        'token_type': 'bearer'
    }
    mock_requests.post.return_value = mock_response

    user_info_response = MagicMock()
    user_info_response.json.return_value = {
        'data': [{'id': user_id}]
    }
    mock_requests.get.return_value = user_info_response

    # Test - First set the state cookie by visiting the index page
    # The auth_redirect route validates the state parameter against the cookie
    # So we need to visit the index page and get the actual state value from the response
    index_response = client.get('/')
    # Extract the state cookie from the index response
    state_cookie = index_response.headers.get('Set-Cookie', '')
    if 'state=' in state_cookie:
        state_value = state_cookie.split('state=')[1].split(';')[0]
        # Use the actual state value from the cookie
        response = client.get(f'/twitch/auth_redirect?code={auth_code}&state={state_value}&scope={scope}')
    else:
        # Fallback to using the provided state
        response = client.get(f'/twitch/auth_redirect?code={auth_code}&state={state}&scope={scope}')

    # Verify the redirect
    assert response.status_code == 302  # Redirect status
    # Follow the redirect to see the final page
    # Mock the session functions because the redirect creates a new request context
    # and the session might not be properly maintained between requests in tests
    with patch('snaarf_app.server.get_user_id_controller', return_value=user_id):
        with patch('snaarf_app.server.check_logged_in', return_value=True):
            final_response = client.get(response.location)
            assert final_response.status_code == 200
            assert b'You are logged in' in final_response.data
    mock_redis.hset.assert_called_once()
    mock_redis.expire.assert_called_once_with(f'user:{user_id}', expires_in)

def test_auth_redirect_invalid_state(mock_redis, client):
    """Test OAuth redirect with invalid state."""
    # Test
    response = client.get('/twitch/auth_redirect?code=auth123&state=invalid_state',
                         headers={'Cookie': 'state=different_state'})

    # Verify
    assert response.status_code == 200
    # Look for the error message displayed by the 404 template
    assert b'Insecure auth_redirect request detected' in response.data
    mock_redis.hset.assert_not_called()

def test_index_logged_in(client):
    """Test index route when user is logged in."""
    # Setup
    # Mock the session functions to avoid "Working outside of request context" errors
    # The index route calls get_user_id_controller() which requires a request context
    with patch('snaarf_app.server.get_user_id_controller', return_value='user123'):
        with patch('snaarf_app.server.check_logged_in', return_value=True):
            # Test
            response = client.get('/')

    # Verify
    assert response.status_code == 200
    # Look for user-facing content that indicates the user is logged in
    assert b'You are logged in' in response.data

def test_index_not_logged_in(client):
    """Test index route when user is not logged in."""
    # Setup
    with patch('snaarf_app.server.get_user_id_controller', return_value=None):
        with patch('snaarf_app.server.check_logged_in', return_value=False):
            # Test
            response = client.get('/')

    # Verify
    assert response.status_code == 200
    # Look for user-facing content that indicates the user is not logged in
    assert b'Login with Twitch' in response.data 