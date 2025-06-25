import requests
from jose import jwt
from jose.exceptions import JWTError



def verify_cognito_token(token, user_pool_id, client_id, region='us-east-1'):
    """Minimal secure token validation using python-jose"""
    # Get Cognito's public keys
    jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
    jwks_response = requests.get(jwks_url)
    jwks = jwks_response.json()
    
    # Get the token header to find the key ID
    header = jwt.get_unverified_header(token)
    kid = header.get('kid')
    
    if not kid:
        raise ValueError("Token header missing 'kid' field")
    
    # Find the matching key
    key = None
    for jwk in jwks['keys']:
        if jwk['kid'] == kid:
            key = jwk
            break
    
    if not key:
        raise ValueError(f"Unable to find key with kid: {kid}")
    
    # Verify and decode the token using python-jose
    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=['RS256'],
            audience=client_id,
            issuer=f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}",
            options={
                'verify_at_hash': False  # Disable at_hash validation since we don't have access_token
            }
        )
        return payload
    except JWTError as e:
        raise ValueError(f"Token validation failed: {str(e)}")