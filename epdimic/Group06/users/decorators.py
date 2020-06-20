# from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from .models import UserInfo
from urllib.parse import urlparse
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url
from django.contrib.sessions.models import Session
from django.http import HttpResponse
from django.http import HttpRequest, JsonResponse, HttpResponseForbidden
from django.contrib.auth.models import AnonymousUser


def GetUserFromRequestSession(request: HttpRequest):
    try:
        session_id = request.headers['sessionid']
    except KeyError:
        return AnonymousUser()

    try:
        session = Session.objects.get(session_key=session_id)
    except Session.DoesNotExist:
        return AnonymousUser()
    uid = session.get_decoded()['_auth_user_id']
    user = AnonymousUser()
    try:
        user = UserInfo.objects.get(id=uid)
        print("current User: " + user.username)
    except UserInfo.DoesNotExist:
        user = AnonymousUser()

    return user


def user_passes_test(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = GetUserFromRequestSession(request)
            if user.is_anonymous:
                print(" 用户不存在")
            else:
                print(user.username, user.groups.values_list("name", flat=True), user.email)
            if test_func(user):
                return view_func(request, *args, **kwargs)
            path = request.build_absolute_uri()
            if login_url is None:
                login_url='../../login/'
            resolved_login_url = resolve_url(login_url or settings.LOGIN_URL)
            # If the login url is the same scheme and net location then just
            # use the path as the "next" url.
            login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            current_scheme, current_netloc = urlparse(path)[:2]
            if ((not login_scheme or login_scheme == current_scheme) and
                    (not login_netloc or login_netloc == current_netloc)):
                path = request.get_full_path()
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(
                path, resolved_login_url, redirect_field_name)
        return _wrapped_view
    return decorator


def group_required(*group_names):
    """Requires user membership in at least one of the groups passed in."""

    def in_groups(u: UserInfo):
        if u is None:
            return False
        if u.is_authenticated:
            if bool(u.groups.filter(name__in=group_names)) | u.is_superuser:
                return True
        return False

    return user_passes_test(in_groups, login_url='../forbidden/')


def login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

