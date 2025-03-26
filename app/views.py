from django.http import HttpResponse
from django.shortcuts import render
from authlib.integrations.django_client import OAuth
from django.http import HttpResponse
from django.urls import reverse
from authlib.integrations.requests_client import OAuth2Session
from django.conf import settings
from django.shortcuts import redirect

oauth = OAuth()

oauth.register(
  name='oidc',
  authority=settings.AUTHLIB_OAUTH_CLIENTS.get('oidc').get('authority'),
  client_id=settings.AUTHLIB_OAUTH_CLIENTS.get('oidc').get('client_id'),
  client_secret=settings.AUTHLIB_OAUTH_CLIENTS.get('oidc').get('client_secret'),
  server_metadata_url=settings.AUTHLIB_OAUTH_CLIENTS.get('oidc').get('server_metadata_url'),
  client_kwargs=settings.AUTHLIB_OAUTH_CLIENTS.get('oidc').get('client_kwargs')
)


def index(request):
  return render(request, 'app/index.html', {'user': request.session.get('user')})


def login(request):
  redirect_uri = request.build_absolute_uri(reverse('authorize'))
  return oauth.oidc.authorize_redirect(request, redirect_uri)

def authorize(request):
  token = oauth.oidc.authorize_access_token(request)
  print(token)
  user = token['userinfo']
  request.session['user'] = user
  return redirect(reverse('index'))

def logout(request):
  request.session.pop('user', None)
  return redirect(reverse('index'))
  


