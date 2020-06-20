## Readme

新的用于整合的repository

先每个组一个branch吧，改完传到自己branch

病例监测子系统已经整合进去了

有几个需要注意的点，也是为了方便大家整合：

1. 五个app，一个组一个，不要动其他组的文件

2. urls.py文件只有一个，每个组的路径可以自己加在后面，不要改其他组的内容
   引用的自己模块文件夹下的文件时，比如views.py，可以用as避免重名，e.g.
   
```python
   from Group07 import views as g7
```

3. settings.py也只有一个，尽量不要修改

4. 可以使用各自的数据库，在settings里DATABASES里加上自己数据库的配置
   然后在dbRouter文件夹下面的db_router.py文件里的map里添上和自己app的对应关系就好了
   都有样例
   如果用的是本地的数据库，把scheme（create和insert语句）给出来，可以在我们的数据库上部署

5. 前端整合好了的话
   大家的前端文件都一样，templates里就不用动，就是前端build好的文件
   如果要改前端，拿着前端整合好build前的文件改完再build放进去

6. 上传了前端源代码，比后端的templates文件里的前端版本，改进了登录和注销的功能。

7. 关于权限检测，可以使用Group06.users.decorators中的两个装饰器 login_required 和 group_required
   【这两个装饰器的使用都需要在请求头中加上 "sessionid":"xxxxxxxx" （sessionid全小写）】
   这个sessionid在登录成功时会被写到用户浏览器的cookie中，key名也是sessionid
   因为在我们的实测中fetch带cookie有可能会有问题，所以麻烦手动从cookie中读取
   使用时，首先在需要使用的模块中引入
```python
   from Group07.users import decoators
```
   接着 在需要进行权限检测的视图函数上
```python
   # group_required接受一组用户group的字符串，如下例，代表这个example函数可以被拥有admin_1组或admin_2组的用户访问
   # 如果用户拥有权限，会被放行，反之，会重定向请求（302码）到后端的另一接口，然后返回一个HttpResponseForbidden（403码），内容是"您无权访问该页面"
   @group_required('admin_1','admin_2')  
   def example(request: HttpRequest)

   # login_required使用如下，它会验证用户的.is_authenticated属性，如果True，放行，否则重定向请求（302码）到后端的另一接口，然后返回一个HttpResponse（200ma），内容是"login"
   @login_required
   def example(request: HttpRequest)
   这样 就实现了权限和登录验证
```


把原先的后端放进去应该还是挺快的，这也是一个让自己代码更整洁的机会，可以删掉许多没用的东西

遇到具体问题请及时反馈沟通

8.测试