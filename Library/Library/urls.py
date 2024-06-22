"""Library URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from myWEB import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.home),
    path('admin/', admin.site.urls),

    path('login_view/', views.login_view),  # 登录
    path('logout_view/', views.logout_view),  # 退出登�?

    path('reader_index/', views.reader_index),  # 读者首�?
    path('reader_search/', views.reader_search),  # 读者书目状态查�?
    path('reader_reserve/', views.reader_reserve),  # 读者预约登�?
    path('reader_reserve2/', views.reader_reserve2),
    path('reader_person/', views.reader_person),  # 读者个人状态查�?

    path('admin_index/', views.admin_index),  # 管理员首�?
    path('admin_search/', views.admin_search),  # 读者书目状态查�?
    path('admin_borrow/', views.admin_borrow),  # 管理员借书
    path('admin_return/', views.admin_return),  # 管理员还书
    path('admin_in/', views.admin_in),  # 管理员入�?
    path('admin_out/', views.admin_out),  # 管理员出�?

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
