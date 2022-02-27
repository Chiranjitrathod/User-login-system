from base64 import urlsafe_b64decode, urlsafe_b64encode
from email.message import EmailMessage
from fnmatch import fnmatchcase
import imp
from weakref import ref
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib import messages
from pkg_resources import fixup_namespace_packages
from django.shortcuts import redirect,render
from django.contrib.auth import authenticate,login,logout
from user_login import settings
from django.core.mail import send_mail 
from django.core.mail import EmailMessage, send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.encoding import force_str
from .tokens import generate_token


import authentication
# Create your views here.

def home(request):
    return render(request,"authentication/index.html")


def signup(request):
    

    if request.method == "POST":
        # username = request.POST.get('username') this function is same as below
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        if User.objects.filter(username=username):
            messages.error(request,"Username already exist! please try some other username")
            return redirect('home')

        # if User.objects.filter(email=email):
        #     messages.error(request,"Email already registered!")
        #     return redirect('home')

        if len(username) > 10:
            messages.error(request,"Username must be under 10 characters")
        
        if pass1 != pass2:
            messages.error(request,"Paaswords doesn't match!")

        if not username.isalnum():
            messages.error(request,"Username must be an alphanumeric")
            return redirect('home')


        myuser = User.objects.create_user(username,email,pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = False
        myuser.save()

        messages.success(request,"your account has been successully created \n we have sent a confirmation email . please confirm your email in order to activate your account.")



        #welcome Email
        
        subject = "welcome to my website"
        message = "Hello " + myuser.first_name + "!!\n" + "Welcome to my website \n Thank you for visiting My website \n please confirm your email address in order to activate your account \n\n Thank you \n Chiranjit rathod"
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject,message,from_email,to_list,fail_silently = True)


        #Email confirmation and activation
        current_site = get_current_site(request)
        email_subject = "confirm your email"
        message2 = render_to_string('email_confirmation.html',{
            'name':myuser.first_name,
            'domain': current_site.domain,
            'uid': urlsafe_b64encode(force_bytes(myuser.pk)),
            'token':generate_token.make_token(myuser)
        })
        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email]
        )
        email.fail_silently = True
        email.send()


        return redirect('signin')
    
    return render(request,"authentication/signup.html")


def signin(request):
    if request.method == "POST":
        username = request.POST['username']
        pass1 = request.POST['pass1']

        user = authenticate(username=username,password=pass1)

        if user is not None:
            login(request,user)
            fname = user.first_name
            return render(request,"authentication/index.html",{'fname':fname})
            
        else:
            messages.error(request,"Invalid Credentials")
            return redirect('home')

    return render(request,"authentication/signin.html")


def signout(request):
    logout(request)
    messages.success(request,"Logged Out Successfully")
    return redirect('home')


def activate(request,uidb64,token):
    try:
        uid = force_str(urlsafe_b64decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except (TypeError,ValueError,OverflowError,User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser,token):
        myuser.is_active = True
        myuser.save()
        login(request,myuser)
        return render('home')
    else:
        return render(request,'activation_failed.html')