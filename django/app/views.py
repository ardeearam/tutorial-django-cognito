from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect
from django.conf import settings
from django.urls import reverse
import requests
from .lib.cognito import verify_cognito_token
from .lib.utils import login_url

def home_view(request):
    return render(request, 'home.html', context= {
      'login_url': login_url(request)
    })
  
def callback_view(request):
  """Process authorization code from Cognito"""
  code = request.GET.get('code')
  if not code:
      return JsonResponse({'error': 'No code provided'}, status=400)
  
  # DEBUG: Check if session exists before we start
  print(f"🔍 Session key before: {request.session.session_key}")
  print(f"🔍 Session data before: {dict(request.session)}")
  
  # 1. Exchange code for tokens
  callback_url = request.build_absolute_uri('/callback')
  token_url = f"{settings.COGNITODOMAIN}/oauth2/token"
  
  response = requests.post(token_url, data={
      'grant_type': 'authorization_code',
      'client_id': settings.COGNITOCLIENTID,
      'code': code,
      'redirect_uri': callback_url,
  }, headers={'Content-Type': 'application/x-www-form-urlencoded'})
  
  if response.status_code != 200:
      return JsonResponse({'error': 'Token exchange failed'}, status=400)
  
  tokens = response.json()
  access_token = tokens.get('access_token')
  id_token = tokens.get('id_token')
  
  # 2. VERIFY the ID token (critical security step!)
  try:
      verified_user = verify_cognito_token(id_token, settings.COGNITOUSERPOOLID, settings.COGNITOCLIENTID, settings.COGNITOREGION)
      print(f"✅ Token verified for user: {verified_user.get('email')}")
  except Exception as e:
      print(f"❌ Token verification failed: {e}")
      return JsonResponse({'error': 'Invalid token'}, status=401)
  
  sub = verified_user.get('sub')
  email = verified_user.get('email')
  picture = verified_user.get('picture')
  first_name = verified_user.get('given_name')
  last_name = verified_user.get('family_name')
    
  
  # Set session data
  request.session['sub'] = sub
  request.session['email'] = email
  request.session['picture'] = picture
  request.session['first_name'] = first_name
  request.session['last_name'] = last_name
  
  #TODO: Save user information to database
  # user, created = User.objects.update_or_create(
  #   id=sub,
  #   defaults={
  #     'first_name': first_name,
  #     'last_name': last_name,
  #     'email': email,
  #     'picture': picture
  #   }
  # )
  
  # if created:
  #   # Create or get the organization
  #   org_name = f"{first_name} {last_name}'s Organization"
  #   organization, _ = Organization.objects.get_or_create(name=org_name)

  #   # Link the user to the organization
  #   OrganizationUser.objects.get_or_create(user=user, organization=organization)
  

  request.session.save()  # Explicitly save the session
  
  print(f"🔍 Login Successful: {sub} {first_name} {last_name} {email}")
  
  response = HttpResponseRedirect(f'/')
  
  # Double check the console for the available values
  # Comment out in production to reduce noise
  print ({
      'username': verified_user.get('cognito:username') or verified_user.get('username'),
      'email': email,
      'first_name': verified_user.get('given_name'),
      'last_name': verified_user.get('family_name'),
      'email_verified': verified_user.get('email_verified'),
      'sub': sub,  # Permanent user ID, use this as primary key
      'verified': True ,
      'exp': verified_user.get('exp'),
      'picture': picture
      
  }) 
  
  return response


def logout_view(request):
  request.session.clear()
  return HttpResponseRedirect(reverse('home'))