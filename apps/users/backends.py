import httplib2
import json
import urllib

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q

from users.models import Profile


class CustomUserBackend(object):
    supports_anonymous_user = False
    supports_object_permissions = False

    def authenticate(self, username=None, password=None):
        try:
            key = '@' in username and 'email' or 'username'
            kwargs = {
                key: username
            }
            user = User.objects.get(**kwargs)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class BrowserIdBackend(object):
    supports_anonymous_user = False
    supports_object_permissions = False

    def authenticate(self, assertion=None, host=None, port=None):
        qs = urllib.urlencode({
            'assertion': assertion,
            'audience': '%s' % (host,)
        })
        if port and port != '80':
            qs['audience'] += ':%s' % (port,)
        client = httplib2.Http()
        url = getattr(settings, 'BROWSERID_VERIFY_URL',
                      'https://browserid.org/verify')
        response, content = client.request('%s?%s' % (url, qs))
        result = json.loads(content)
        if result['status'] == 'okay':
            email = result['email']
            users = User.objects.filter(Q(username=email) | Q(email=email))
            if users:
                user = users[0]
            else:
                profile = Profile.objects.create_profile(
                    username=email,
                    email=email, is_active=True)
                return profile.user
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None