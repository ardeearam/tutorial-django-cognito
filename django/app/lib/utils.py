from django.conf import settings

def current_host(request):
    request_host = request.get_host()
    scheme = 'https' if request.is_secure() else 'http'
    full_host = f"{scheme}://{request_host}"
    return full_host
  
def login_url_scopes():
  scopes = [
    'email',
    'openid',
    'profile'
  ]
  return '+'.join(scopes)

def login_url(request):
    full_host = current_host(request)
    scopes = login_url_scopes()
    login_url =  f'{settings.COGNITODOMAIN}/login?client_id={settings.COGNITOCLIENTID}&response_type=code&scope={scopes}&redirect_uri={full_host}/callback'
    return login_url