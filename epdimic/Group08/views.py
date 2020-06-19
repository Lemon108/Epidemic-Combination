from django.shortcuts import render
from django.http import HttpResponse
import json
from .models import Transport
from django.core.mail import send_mail
from epdimic import settings
# from Group06.models import UserInfo

def _Info(t):
    datanode= {}
    datanode['shift_id'] = t.id
    datanode['No'] = t.No
    datanode['start_p'] = t.start_p
    datanode['end_p'] = t.end_p
    datanode['date'] = t.departure_date.strftime('%Y-%m-%d')
    datanode['danger_level'] = t.danger_level
    datanode['type'] = t._type    
    return datanode

# Create your views here.
def search1(request):
    UserID = request.GET.get('uid')
    start_p = request.GET.get('start_p')
    end_p = request.GET.get('end_p')
    No = request.GET.get('No')
    Date = request.GET.get('date')
    _type = request.GET.get('type')
    if _type:
        transport = Transport.objects.filter(_type=_type)
    else:
        transport = Transport.objects.filter()
    data = []
    for t in transport:
        tmp1 = t.start_p
        tmp2 = t.end_p
        tmp3 = t.No
        tmp4 = t.departure_date.strftime('%Y-%m-%d')
        if (start_p in tmp1) and (end_p in tmp2) and (No in tmp3) and (Date in tmp4):
            datanode = _Info(t)
            data.append(datanode)

    res = HttpResponse(json.dumps(data), content_type='application.json')
    return res


def register(request):
    ID = request.GET.get('shift_id')
    UserID = request.GET.get('uid')
    flag = 1
    data = {}
    data['is_login'] = 1
    data['is_auth'] = 1
    data['is_register'] = 0
    try:
    	pass
        # u = UserInfo.objects.get(id=UserID)
        # tmp = u.citizen_id
        # if not tmp:
        #     data['is_auth'] = 0
    except:
        data['is_login'] = 0
        data['is_auth'] = 0

    try:
        t = Transport.objects.get(id=ID)
        tmp = t.register_id
        IDList = tmp.split('#')
        for i in  range(len(IDList)):
            if IDList[i] == UserID:
                data['is_register'] = 1
                flag = 0
                break
        if flag:
            tmp += UserID + '#'
            t.register_id = tmp
            t.save()
    except:
        pass
    
    res = HttpResponse(json.dumps(data), content_type='application.json')
    return res


def record(request):
    _No = request.GET.get('No')
    _start_p = request.GET.get('start_p')
    _end_p = request.GET.get('end_p')
    _date = request.GET.get('date')
    _danger_level = request.GET.get('danger_level')
    _type = request.GET.get('type')
    data = {}
    data['flag'] = 1
    try:
        t = Transport.objects.create()
        if _No:
            t.No = _No
        if _start_p:
            t.start_p = _start_p
        if _end_p:
            t.end_p = _end_p
        if _date:
            t.departure_date = _date
        if _danger_level:
            t.danger_level = _danger_level
        if _type:
            t._type = _type
        t.save()
    except:
        data['flag'] = 0

    res = HttpResponse(json.dumps(data), content_type='application.json')
    return res

def shifts(request):
    data = []
    transport = Transport.objects.filter()
    for t in transport:
            datanode = _Info(t)
            data.append(datanode)
    res = HttpResponse(json.dumps(data), content_type='application.json')
    return res

def mail(request):
    ID = request.GET.get('shift_id')
    receiverID = set()
    eList = []
    if not ID:
        try:
            transport = Transport.objects.filter(danger_level='3')
            for t in transport:
                tmp = t.register_id
                IDList = tmp.split('#')
                for i in IDList:
                    if i:
                        receiverID.add(i)
        except:
            pass
    else:
        try:
            t = Transport.objects.get(id=ID)
            tmp = t.register_id
            IDList = tmp.split('#')
            for i in IDList:
                if i:
                    receiverID.add(i)
        except:
            pass
    
    for j in  receiverID:
        try:
        	pass
            # u = UserInfo.objects.get(id=j)
            # tmp = u.email
            # if tmp:
            #     eList.append(u.email)
        except:
            pass

    msg = '您最近乘坐的列车或航班存在风险，请居家14天隔离'
    send_mail(
        subject='居家提醒',
        message=msg,
        from_email=settings.EMAIL_HOST_USER, 
        recipient_list=eList    
    )

    data = {}
    res = HttpResponse(json.dumps(data), content_type='application.json')
    return res


def delete(request):
    ID = request.GET.get('shift_id')
    try:
        t = Transport.objects.get(id=ID)
        t.delete()
    except:
        pass
    data = {}
    res = HttpResponse(json.dumps(data), content_type='application.json')
    return res


def detail(request):
    ID = request.GET.get('shift_id')
    data = []
    try:
        t = Transport.objects.get(id=ID)
        tmp = t.register_id
        IDList = tmp.split('#')
        for i in  range(len(IDList)):
            try:
            	pass
                # u = UserInfo.objects.get(id=IDList[i])
                # _username = u.username
                # _email = u.email
                # datanode = {}
                # datanode['name'] = _username
                # datanode['email'] = u.email
                # data.append(datanode)
            except:
                pass
    except:
        pass
    res = HttpResponse(json.dumps(data), content_type='application.json')
    return res


def modify(request):
    ID = request.GET.get('shift_id')    
    _danger_level = request.GET.get('danger_level')
    data = {}
    data['flag'] = 0
    try:
        t = Transport.objects.get(id=ID)
        t.danger_level = _danger_level
        t.save()
        data['flag'] = 1
    except:
        pass   
    res = HttpResponse(json.dumps(data), content_type='application.json')
    return res