import logging, os

# Must set this env var before importing any part of Django
# 'project' is the name of the project created with django-admin.py
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library
use_library('django', '1.1')

# Google App Engine imports.
from google.appengine.ext.webapp import util

# Force Django to reload its settings.
from django.conf import settings
settings._target = None



import logging
import django.core.handlers.wsgi
import django.core.signals
import django.db
import django.dispatch.dispatcher

def log_exception(*args, **kwds):
    logging.exception('Exception in request:')

# create a new signal object
sig = django.dispatch.Signal()
 
# Log errors.
sig.connect(log_exception, django.core.signals.got_request_exception)
 
# Unregister the rollback event handler.
sig.disconnect(django.db._rollback_on_exception, django.core.signals.got_request_exception)
 
def main():
    # Create a Django application for WSGI.
    application = django.core.handlers.wsgi.WSGIHandler()

    # Run the WSGI CGI handler with that application.
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
