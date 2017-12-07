from django.conf.urls import url
from user.views import register,index,login,register_handle,RegisterView,ActiveView,LoginView,cart,submit,UserInfoView,UserOrderView,AddressView,LogoutView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # url(r'^index$',index,name='index'),
    # url(r'^login$',login,name='login'),
    #url(r'register$',register,name='register'),#zuche注册
    #url(r'^register_handle$',register_handle,name='register_handle'),# 注册处理
    url(r'^register$',RegisterView.as_view(),name='register'),
    url(r'^active/(?P<token>.*)$',ActiveView.as_view(),name='active'),# 用户激活
    url(r'^login$',LoginView.as_view(),name='login'),#login
    url(r'^logout$',LogoutView.as_view(),name='logout'),
    # url(r'^cart$',cart,name='cart'),
    # url(r'^place_order$',submit,name='submit'),
    # url(r'^$',login_required(UserInfoView.as_view()),name='user'),
    url(r'^$',UserInfoView.as_view(),name='user'),#用户中心
    url(r'^order$',UserOrderView.as_view(),name='order'),#订单页面
    url(r'address$',AddressView.as_view(),name='address'),#地址页面
]
