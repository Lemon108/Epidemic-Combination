from django.contrib import admin
from django.urls import include, path
from django.conf.urls import url
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static

from Group07 import dbrequest as g7
import Group06
from Group09 import views as g9

urlpatterns = [
    path('admin/', admin.site.urls),

    path('ESS/background/write/', g9.updatePopulationFlow),
    path('ESS/getPopulationFlow/', g9.sendPopulationFlow),
    path('ESS/background/action/', g9.actionRelease),
    path('ESS/getNews', g9.sendNews),


    path('ESS/index', g7.rqst_process),
    path('ESS/situation', g7.rqst_process),
    path('ESS/situation$', g7.rqst_process),
    path('ESS/situation/situationMoreInfo', g7.rqst_process),
    path('ESS/situation/situationMoreInfo$', g7.rqst_process),
    path('ESS/background/Cases', g7.rqst_process),
    path('ESS/background/Cases$', g7.rqst_process),
  
    path('user/', include('Group06.users.urls')),
    path('news/', include('Group06.news.urls')),
    
    path('ESS/transport/', include('Group08.urls')),
    url(r'^(?P<path>.*)$', serve, {'document_root': ''}),
]
