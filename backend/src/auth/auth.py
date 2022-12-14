import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'dev-7pd1ay12.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'csp'

## AuthError Exception

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

def get_token_auth_header():
    if "Authorization" in request.headers:
        get_auth_header = request.headers["Authorization"]
        bearer_token = get_auth_header.split(' ')
        if bearer_token[0] and bearer_token[0].lower() == "bearer" and bearer_token[1]:
            return bearer_token[1]
        
    raise AuthError({
        'success': False,
        'message': 'JWT not found',
        'error': 401
    }, 401)


def check_permissions(permission, payload):
    if "permissions" in payload:
        if permission in payload:
            return True
    raise AuthError({
        'success': False,
        "message": "Permission not in jwt",
        "error": 401
    }, 401)


def verify_decode_jwt(token):
    url = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(url.read())
    unverified_token = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_token:
        raise AuthError({
            'code': 'invalid_token',
            'description': 'Authorization'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_token['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Invalid claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_token',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
            'code': 'invalid_token',
            'description': 'Unable to find the appropriate key.'
        }, 400)

def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator