```
mkdir tutorial-django-lambda
cd tutorial-django-lambda
python3 -m venv venv
source venv/bin/activate

pip install django authlib
pip freeze > requirements.txt

django-admin startproject app .
python manage.py runserver  #Visit http://127.0.0.1:8000/

#Code modifications:
# app/views.py - Create
# Add app/templates/app/index.html 
# app/urls.py - Map URLS to view
# app/settings.py
#   add "app" to INSTALLED_APPS
#   add AUTHLIB_OAUTH_CLIENTS
```