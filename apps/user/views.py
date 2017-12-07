from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from celery_tasks.tasks import send_register_active_email
import re
from user.models import User,Address,AddressManage
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.contrib.auth import authenticate,login,logout
from itsdangerous import SignatureExpired
from celery_tasks.tasks import send_register_active_email
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection
from goods.models import GoodsSKU
# Create your views here.

def index(request):
    return render(request,'index.html')
# def login(request):
#     return render(request,'login.html')
def register(request):
    if request.method=='GET':
        return render(request,'register.html')
    else:
        username=request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        if not all([username,password,email]):
            return render(request,'register.html',{'errmsg':'数据不完整'})
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request,'register.html',{'errmsg': '邮箱格式不正确'})
        if allow!='on':
            return render(request,'register.html',{'errmsg': '请同意协议'})
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:
                return render(request,'register.html',{'errmsg':'用户名已存在'})
        user = User.objects.create_user(username,email,password)
        user.is_active=0
        user.save()
        return redirect(reverse('goods:index'))

def register_handle(request):
    '''进行注册处理'''
    # 接收数据
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')
    allow = request.POST.get('allow')
    # 数据不完整
    if not all([username,password,email]):
       return render(request,'register.html', {'errmsg':'数据不完整'})
    # 校验邮箱
    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'errmsg':'邮箱格式不正确'})
    if allow != 'on':
        return render(request,'register.html',{'errmsg':'请同意协议'})
    # 校验用户名是否重复
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user=None
    if user:
        # 用户名已存在
        return render(request,'register.html',{'errmsg':'用户名已存在'})
    user=User.objects.create_user(username,email,password) # create_user 是django的内置函数
    user.is_active=0
    user.save()
    return redirect(reverse('goods:index'))

class RegisterView(View):
    def get(self,request):
        return render(request,'register.html')

    def post(self,request):
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 进行数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None

        if user:
            # 用户名已存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})
        user=User.objects.create_user(username,email,password)
        user.is_active=0
        user.save()
        # 发送激活邮件，包含激活链接: http://127.0.0.1:8000/user/active/3
        # 激活链接中需要包含用户的身份信息, 并且要把身份信息进行加密
        serializer = Serializer(settings.SECRET_KEY,3600)
        info = {'confirm':user.id}
        token = serializer.dumps(info) # bytes
        token = token.decode()
        # 发邮件
        # subject='天天生鲜欢迎信息'
        # message=''
        # sender = settings.EMAIL_FROM
        # recevier=[email]
        # html_message='<h1>%s请点击下面的链接<a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a></h1>'%(username,token,token)
        # # send_register_active_email.delay(email,username,token)
        # send_mail(subject,message,sender,recevier,html_message=html_message)
        send_register_active_email.delay(email,username,token)
        return redirect(reverse('goods:index'))

class ActiveView(View):
    '''用户激活'''
    def get(self,request,token):
        '''进行用户激活'''
        # 进行解密，获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY,3600)
        try:
            info=serializer.loads(token)
            # 获取待激活用户的id
            user_id = info['confirm']
            # 根据id获取用户信息
            user=User.objects.get(id=user_id)
            user.is_active=1
            user.save()
            return redirect(reverse('user:login'))# 跳转到登录页面
        except SignatureExpired as e:
            #激活链接已过期
            return HttpResponse('激活链接已过期')

#/user/login
class LoginView(View):
    def get(self,request):
        '''显示登录页面'''
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username=request.COOKIES.get('username')
            checked='checked'
        else:
            username = ''
            checked = ''
            # 使用模板
        return render(request,'login.html',{'username':username,'checked':checked})

    def post(self,request):
        '''登录校验'''
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        if not all([username,password]):
            return render(request,'login.html',{'errmsg':'数据不完整'})
            # 业务处理:登录校验
        user = authenticate(username=username,password=password)
        if user is not None:
            if user.is_active:
                # 用户已激活
                # 记录用户的登录状态
                login(request,user)
                next_url = request.GET.get('next',reverse('goods:index'))
                #next的值是需要跳转的地址,没有next,需要获取一个默认值,所以设置一个默认值,默认跳转首页
                # 跳转到首页
                response = redirect(next_url)#HttpResponseRedirect
                remember = request.POST.get('remember')
                if remember == 'on':
                    # 记住用户名
                    response.set_cookie('username',username,max_age=7*24*3600)
                else:
                    response.delete_cookie('username')
                # 返回response

                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg':'账户未激活'})
        else:
            # 用户名或密码错误
            return render(request, 'login.html', {'errmsg':'用户名或密码错误'})

#/user/logout
class LogoutView(View):
    def get(self,request):
        logout(request)
        return redirect(reverse('goods:index'))


class UserInfoView(LoginRequiredMixin,View):
    def get(self,request):
        user=request.user
        address=Address.objects.get_default_address(user)
        con = get_redis_connection('default')
        history_key = 'history_%d'%user.id
        # 获取用户最新浏览的5个商品的id
        sku_ids = con.lrange(history_key, 0, 4)  # [2,3,1]
        goods_li =[]
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)
        context = {'page':'user',
                   'address':address,
                   'goods_li':goods_li}
        return render(request,'user_center_info.html',context)
        # return render(request,'user_center_info.html',{'page':'user','address':address})

class UserOrderView(LoginRequiredMixin,View):
    def get(self,request):
        return render(request,'user_center_order.html',{'page':'order'})

class AddressView(LoginRequiredMixin,View):
    def get(self,request):
        user=request.user
        # try:
        #     address=Address.objects.get(user=user,is_default=True)
        # except Address.DoesNotExist:
        #     address=None
        address = Address.objects.get_default_address(user)
        return render(request,'user_center_site.html',{'page':'address','address':address})

    def post(self,request):
        # 接收数据
        receiver=request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        if not all([receiver,addr,phone]):
            return render(request,'user_center_site.html',{'errmsg':'数据不完整'})
        if not re.match(r'1[3|4|5|7|8][0-9]{9}$',phone):
            return render(request,'user_center_site.html',{'errmsg':'手机号不正确'})
        # 业务处理:地址添加
        # 如果用户已存在默认收货地址,添加的地址不作为默认收货地址,否则作为默认收货地址
        #huoqudaole 登录对下
        user=request.user
        # try:
        #     address=Address.objects.get(user=user,is_default=True)
        # except Address.DoesNotExist:
        #     address=None
        address = Address.objects.get_default_address(user)

        if address:
            is_default=False
        else:
            is_default=True

        Address.objects.create(
                            user=user,
                            receiver=receiver,
                            addr=addr,
                            zip_code=zip_code,
                            phone=phone,
                            is_default=is_default)
        return redirect(reverse('user:address'))
            # 校验数据
            # 业务处理
            # 返回应答
            # 获取用户信息
            # 获取收件人信息与添加

def cart(request):
    return render(request, 'cart1.html')

def submit(request):
    return render(request,'place_order.html')









