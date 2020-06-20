from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings
from .models import UserInfo


def GenerateVerifyTokenURL(user: UserInfo, duration, isUrl = True, appendix=None):
    """
    生成邮箱验证链接
    :param user: 当前登录用户
    :return: verify_url
    """
    serializer = Serializer(settings.SECRET_KEY, expires_in=duration)

    data = {'username': user.username, 'email': user.email, 'appendix': appendix}
    token = serializer.dumps(data).decode()
    if isUrl:
        return '?token=' + token
    else:
        return token


def ParseVerifyEmailURL(token):
    """
    验证token并提取user
    :param token: 用户信息签名后的结果
    :return: user, None
    """
    serializer = Serializer(settings.SECRET_KEY, expires_in=30)
    try:
        data = serializer.loads(token)
    except BadData:
        return None
    else:
        username = data.get('username')
        email = data.get('email')
        appendix = data.get('appendix')
        try:
            user = UserInfo.objects.get(username=username, email=email)
        except UserInfo.DoesNotExist:
            return None
        else:
            return user, appendix


