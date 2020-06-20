from django.http import HttpResponse
from django.http import HttpRequest, JsonResponse, HttpResponseForbidden
from django.contrib import auth
from django.core.mail import send_mail, send_mass_mail
from django.contrib.sessions.models import Session
from django.core import serializers
from django.db import utils as dbutils
from django import forms
from django.shortcuts import render, redirect
from epdimic import settings
from django.contrib.auth.models import Group

from . import models
from .decorators import GetUserFromRequestSession, group_required, login_required
from .mail_auth import GenerateVerifyTokenURL, ParseVerifyEmailURL

import json

showDebugLogs = True


# 表单的验证类
class UserInfoCheck(forms.Form):
    # 变量名字必须要跟form表单里的名字一一对应
    username = forms.CharField(min_length=4 ,error_messages={'required': '用户不能为空'})  # CharField表示传入的得是字符串
    password = forms.CharField(
        max_length=18,  # 最大字符串为18个
        min_length=6,  # 最小字符串为6个
        error_messages={'required': '密码不能为空', 'min_length': '最小字符为6个', 'max_length': '最大字符为18个'}
    )  # CharField表示传入的得是字符串
    email = forms.EmailField(error_messages={'required': '邮箱不能为空', 'invalid': '邮箱地址不正确'})  # EmailField表示传入的得是邮箱格式
    real_name = forms.CharField(error_messages={'required': '真实姓名不能为空'})
    phone = forms.RegexField(r"^1[3-9]\d{9}$", error_messages={'invalid': '手机号格式有误'})
    citizen_id = forms.RegexField(r"^[1-9][0-9]{5}([1][9][0-9]{2}|[2][0][0|1][0-9])([0][1-9]|[1][0|1|2])([0][1-9]|["
                                  r"1|2][0-9]|[3][0|1])[0-9]{3}([0-9]|[X])$", error_messages={'invalid': '身份证号格式有误'})


# 下面是各个视图函数
# 访问首页时
def OnRequestHome(request: HttpRequest):
    return render(request, 'index.html')


# 点击注册按钮时 跳转到注册页面
def OnGotoRegisterPage(request: HttpRequest):
    return HttpResponse("这是注册页面.jpg")


# 前端的注册表单提交时
def OnRegisterFormSubmit(request: HttpRequest):
    if showDebugLogs:
        print(GetUserFromRequestSession(request).username, request.body)
    data = json.loads(request.body)

    username = data['username']
    password = data['password']
    email = data['email']
    realName = data['real_name']
    phoneNum = data['phone']
    citizenID = data['citizen_id']
    print(data, username, password, email, realName, phoneNum, citizenID)
    msg = ""

    checkObj = UserInfoCheck({"username": username,
                              "password": password,
                              "email": email,
                              "real_name": realName,
                              "phone": phoneNum,
                              "citizen_id": citizenID})
    # checkObj.username = username
    # checkObj.password = password
    # checkObj.email = email
    # checkObj.real_name = realName
    # checkObj.phone = phoneNum
    # checkObj.citizen_id = citizenID

    print(checkObj)

    checkRes = checkObj.is_valid()

    print(checkRes)

    if checkRes:
        # 验证通过之后返回正确信息的一个字典obj.cleaned_data，这是个字典
        # 此处如果是注册功能的话，就可以把注册信息的字典写入数据库
        print(checkObj.cleaned_data)
        try:
            user = models.UserInfo.objects.create_user(username, password, phoneNum, email, realName, citizenID)
            user.is_active = False
            user.save()
        except Exception as e:
            msg = "创建用户失败 %s" % (str(e))
            return StateJsonRes(False, msg)

        AuthorizeUser(user, "common")
        user.save()

        try:
            SendAuthenticationMail(user=user, mode="register", expireTime=1200)
        except Exception as e:
            msg = "在发送验证邮件时出现问题 %s ，请点击页面上的按钮重新尝试发送" % (str(e))
            return StateJsonRes(False, msg)

        msg = "注册成功！我们已经向您的邮箱地址发送了一封验证邮件，请点击其中的验证链接以激活您的账号"
        return StateJsonRes(True, msg)
    else:
        # 验证不通过之后返回一个所有的错误信息：obj.errors，是一大串字符串一个包含user、pwd、email错误信息的html格式的ul标签
        print(checkObj.errors)
        # print(obj.errors['user'][0])
        msg = "注册失败，您提供的信息不合法，请检查后重新提交"
        return StateJsonRes(False, msg)

    #


# 注册时邮箱验证的链接被点击时
def OnRegisterMailConfirmed(request: HttpRequest):
    if showDebugLogs:
        print(GetUserFromRequestSession(request).username, request.body)
    msg = ""
    data = json.loads(request.body)
    token = data['token']
    user, appendix = ParseVerifyEmailURL(token)
    if user is None:
        msg = "这个链接不合法或已经失效，请重新进行邮箱验证"
        return StateJsonRes(False, msg)
    else:
        if user.is_active == False:
            user.is_active = True
            user.save()
            msg = "您的账号已成功激活！"
            return StateJsonRes(True, msg)
        else:
            msg = "您的账号已经是可用状态，无需激活！"
            return StateJsonRes(True, msg)


# 点击登录时 跳转到登录页面
def OnGotoLoginPage(request: HttpRequest):
    return HttpResponse("login")


# 点击登录按钮时，处理登录表单
def OnLoginRequest(request: HttpRequest):
    if showDebugLogs:
        print(GetUserFromRequestSession(request).username, request.body)
    msg = ""
    data = json.loads(request.body)
    username = data['username']
    password = data['password']
    print(username, password)
    user = auth.authenticate(request, username=username, password=password)
    if user is not None:
        if user.is_active is False:
            msg = "该用户未激活或已被禁用"
            return StateJsonRes(False, msg)
        auth.login(request, user)

        request.session.set_expiry(0)
        print(request.session.session_key)
        msg = "登录成功!"
        return StateJsonRes(True, msg, session_id=request.session.session_key)

    else:
        msg = "登录失败，用户名或密码有误"
        return StateJsonRes(False, msg)


# 超级管理员试图为某个账号授权时
@login_required
@group_required('superAdmin')
def OnUserAuthorizationRequest(request: HttpRequest):
    if showDebugLogs:
        print(GetUserFromRequestSession(request).username, request.body)
    msg = ""
    if request.method != "POST":
        msg = "错误的请求类型"
        return StateJsonRes(False, msg)
    FailNumber = 0
    i = 0
    data = json.loads(request.body)
    for groupName in data.keys():
        if groupName == "flag":
            continue
        i += 1
        targetUserName = data[groupName]
        if targetUserName == "":
            msg += "%d. %s组 未提供目标用户 已跳过;\n" % (i, groupName)
            continue
        if (groupName != "common") & (groupName != "admin_1") & (groupName != "admin_2") & (groupName != "admin_3") & (
                groupName != "admin_4") & (groupName != "admin_5"):
            msg += "%d. 目标用户组 %s 不存在;\n" % (i, groupName)
            FailNumber+=1
            continue
            # return StateJsonRes(False, msg)
        targetUser = models.UserInfo.objects.get(username=targetUserName)
        if targetUser is None:
            msg += "%d. 目标用%s 户不存在;\n" % (i, targetUserName)
            FailNumber += 1
            continue
            # return StateJsonRes(False, msg)
        AuthorizeUser(targetUser, groupName)
        msg += "%d. 成功将用户%s 增加%s 分组;\n" % (i, targetUserName, groupName)

    if FailNumber < i:
        return StateJsonRes(True, msg)
    else:
        return StateJsonRes(False, msg)


# 为用户授权
def AuthorizeUser(user: models.UserInfo, group_name):
    group = None
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        group = Group.objects.create(name=group_name)

    user.groups.add(group)
    user.save()
    return


# 通过用户名为用户授权
def AuthorizeUserOnName(username, group_name):
    user = models.UserInfo.objects.get(username = username)
    group = None
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        group = Group.objects.create(name=group_name)

    user.groups.add(group)
    user.save()
    return


# 请求进入到用户主页
@login_required
def OnGotoUserProfile(request: HttpRequest):

    if showDebugLogs:
        print(GetUserFromRequestSession(request).username, request.body)


    msg = ""
    if request.method != 'GET':
        msg = "非法的请求类型"
        return StateJsonRes(False, msg)
    user = GetUserFromRequestSession(request)
    if user is None:
        msg = "用户不存在"
        return StateJsonRes(False, msg)

    groups = []
    for i in user.groups.values_list("name", flat=True):
        groups.append(i)

    return JsonResponse(
        {
            "uid": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "real_name": user.real_name,
            "citizen_id": user.citizen_id,
            "groups": groups
         }
    )


# 修改个人信息的提交
@login_required
def OnModifyProfilePosted(request: HttpRequest):
    if showDebugLogs:
        print(GetUserFromRequestSession(request).username, request.body)
    msg = ""
    if request.method != 'POST':
        msg = "非法的请求类型"
        return StateJsonRes(False, msg)
    user = None
    # try:
    #     username = request.user.username
    user : models.UserInfo = GetUserFromRequestSession(request)
    if user is None:
        msg = "用户不存在"
        return StateJsonRes(False, msg)
    # except ValueError as e:
    #     msg = "查找用户出错 %s" % str(e)
    #     return StateJsonRes(False, msg)

    data = json.loads(request.body)

    keys = data.keys()
    try:
        for i in keys:
            item = data[i]
            if i == 'username':
                user.username = item
            elif i == 'real_name':
                user.real_name = item
            elif i == 'phone':
                user.phone = item
            elif i == 'email':
                user.email = item
            elif i == 'citizen_id':
                user.citizen_id = item
            else:
                pass
        user.save()
    except dbutils.IntegrityError:
        msg = "该用户名已被使用，请更换其他用户名再尝试"
        return StateJsonRes(False, msg)

    except Exception as e:
        msg = "修改信息出错 : %s" % (str(e))
        return StateJsonRes(False, msg)
    auth.login(request, user)

    msg = "信息修改成功"
    return StateJsonRes(True, msg, session_id=request.session.session_key)


# 发送验证邮件
def SendAuthenticationMail(user: models.UserInfo, mode, expireTime,appendix=None):
    title, msg = "", ""
    token_url = GenerateVerifyTokenURL(user, expireTime,appendix=appendix)
    final_url = ""
    if mode is "register":
        title = "注册验证----疫情防控系统邮箱验证"
        msg = "您收到该邮件是因为您已成功注册了疫情防控系统的用户，请点击下面的链接来激活您的账号，激活后您就可以通过账号登录到疫情防控系统中\n若非您本人操作，请忽略本条"
        final_url = settings.EMAIL_VERIFY_URL + "RealCreate/" + token_url
        html = '''
                                <p>您收到该邮件是因为您已成功注册了疫情防控系统的用户，请点击下面的链接来激活您的账号</p>
                                <a href="{}">{}</a>
                                <p>激活后您就可以通过账号登录到疫情防控系统中。</p>
                                <p>若非您本人操作，请忽略本条</p>
                                <p>此链接有效期为{}分钟</p>
                                '''.format(final_url, final_url, expireTime/60)
    elif mode is "changePassword":
        title = "密码修改验证----疫情防控系统邮箱验证"
        msg = "您正在请求修改密码，请点击下面的链接来完成身份确认，若非您本人操作，请忽略本条"
        final_url = settings.EMAIL_VERIFY_URL + "RealChange/" + token_url
        html = '''
                                <p>您正在请求修改密码，请点击下面的链接来验证您的身份</p>
                                <a href="{}">{}</a>
                                <p>若非您本人操作，请忽略本条</p>
                                <p>此链接有效期为{}分钟</p>
                                '''.format(final_url, final_url, expireTime/60)
    else:
        return

    receiver = [
        user.email
    ]
    # 发送邮件
    send_mail(subject=title, html_message=html, message=msg, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=receiver)


# 点击修改密码 发送邮件
@login_required
def OnChangePasswordRequest(request: HttpRequest):
    if showDebugLogs:
        print(GetUserFromRequestSession(request).username, request.body)
    msg = ""
    data = json.loads(request.body)
    newPass = data['new_password']
    user = GetUserFromRequestSession(request)
    if user is None:
        msg = "用户不存在"
        return StateJsonRes(False, msg)
    try:
        SendAuthenticationMail(user, 'changePassword', 1200, appendix={"new_password": newPass})
        msg = "我们已经向您发送了一封验证邮件，请点击其中的链接来完成您的密码重置"
        return StateJsonRes(True, msg)

    except Exception as e:
        msg = "邮件发送出错 %s，请重试" % (str(e))
        return StateJsonRes(False, msg)


# 点击邮件验证以后
def OnChangePassMailConfirmed(request: HttpRequest):
    if showDebugLogs:
        print(GetUserFromRequestSession(request).username, request.body)
    data = json.loads(request.body)
    token = data['token']
    user, appendix = ParseVerifyEmailURL(token)
    if user is None:
        msg = "这个链接不合法或已经失效，请重新进行邮箱验证"
        return StateJsonRes(False, msg)

    else:
        new_pass = appendix['new_password']
        # new_token = GenerateVerifyTokenURL(user, 1200)
        if new_pass is None:
            msg = "未获取到密码信息"
            return StateJsonRes(False, msg)
        try:
            user.set_password(new_pass)
            user.save()
        except Exception as e:
            msg = "修改密码时出现问题 %s" % (str(e))
            return StateJsonRes(False, msg)

        OnLogoutRequest(request)
        msg = "%s 密码修改成功，请用新密码重新登录" % user.username
        return StateJsonRes(True, msg)
        # return StateJsonRes(True, msg, token=new_token)
        # return redirect('http://127.0.0.1:8000/user/profile/changepass/set_new/' + new_token, request=request)


@login_required
@group_required('admin_1', 'superAdmin')
def AuthTest(request: HttpRequest):
    return HttpResponse("通过权限检测，访问成功")

# 点了确认修改 实际去保存新的密码 并让用户重新登录
# def OnConfirmNewPassword(request: HttpRequest):
#     if showDebugLogs:
#         print(request.user, request.body)
#     data = json.loads(request.body)
#     token = data['token']
#     user: models.UserInfo = ParseVerifyEmailURL(token)
#     print(request.method)
#     msg = ""
#
#     if user is None:
#         msg = "令牌不合法或已经失效，请重新进行邮箱验证"
#         return StateJsonRes(False, msg)
#     else:
#         if request.method == "POST":
#             newPassword = request.POST['new_password']
#             try:
#                 user.set_password(newPassword)
#                 user.save()
#             except Exception as e:
#                 msg = "修改密码时出现问题 %s" % (str(e))
#                 return StateJsonRes(False, msg)
#
#             print("%s 密码修改成功，请用新密码重新登录" % user.username)
#             OnLogoutRequest(request)
#             msg = "%s 密码修改成功，请用新密码重新登录" % user.username
#             return StateJsonRes(True, msg)
#
#         else:
#             msg = "不合法的请求类型"
#             return StateJsonRes(False, msg)


# 登出
@login_required
def OnLogoutRequest(request: HttpRequest):
    if showDebugLogs:
        print(GetUserFromRequestSession(request).username, request.body)
    user = GetUserFromRequestSession(request)
    # if user.is_authenticated:
    #     #user.is_authenticated = False
    logout(request)
    return StateJsonRes(True, "登出成功")


def CreateSuperUser(request: HttpRequest):
    return HttpResponse(request.headers.items)


def OnPermissionDenied(request: HttpRequest):
    if showDebugLogs:
        print(GetUserFromRequestSession(request).username, request.body)
    return HttpResponseForbidden("您无权访问该页面")


# 封禁用户
@group_required('superAdmin', 'admin_1', 'admin_2', 'admin_3', 'admin_4', 'admin_5')
@login_required
def OnDeactivateUserRequest(request: HttpRequest):
    if showDebugLogs:
        print(GetUserFromRequestSession(request).username, request.body)
    data = json.loads(request.body)
    targetUser = data['targetUser']
    return StateJsonRes(True, "")

# 取消用户的某个分组



def StateJsonRes(state: bool, msg: str, session_id=None, token=None):
    if token is None:
        return JsonResponse({"isSuccess": state,
                            "message": msg,
                             "session_id": session_id
                            },  json_dumps_params={'ensure_ascii': False})
    else:
        return JsonResponse({"isSuccess": state,
                            "message": msg,
                             "session_id": session_id,
                             "token": token
                            },  json_dumps_params={'ensure_ascii': False})


def Backend_CreateAdmin(username, password, group):
    admin: models.UserInfo = models.UserInfo.objects.create_user(username=username,password=password,phone="15111111111",email="296563502@qq.com",real_name="Lvcenia",citizen_id="511111111111111111")
    admin.is_active = True
    admin.is_staff = True
    admin.save()
    AuthorizeUser(admin, group)


def PrintUserInfo(username):
    try:
        user = models.UserInfo.objects.get(username=username)
    except models.UserInfo.DoesNotExist:
        print(username + " 用户不存在")
        return
    print(user.username,user.groups.values_list("name", flat=True),user.email)


def logout(request):
    """
    Remove the authenticated user's ID from the request and flush their session
    data.
    """
    # Dispatch the signal before the user is logged out so the receivers have a
    # chance to find out *who* logged out.
    user = GetUserFromRequestSession(request)
    if not getattr(user, 'is_authenticated', True):
        user = None

    try:
        session_id = request.headers['sessionid']
    except KeyError:
        return

    try:
        session = Session.objects.get(session_key=session_id)
    except Session.DoesNotExist:
        return
    session.delete()

    request.session.flush()
    if hasattr(request, 'user'):
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

