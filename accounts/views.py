from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
#Verification Email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from .forms import RegistrationForm
from .models import Account


# Create your views here.
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0]

            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()
            # User activation
            mail_subject = "Please activate your account"
            render_string = 'accounts/emails/account_verification_email.html'
            verify_email(request, user, mail_subject, render_string)
            # messages.success(request, "Thank you for registering. We have sent you verification email to your email address.")
            return redirect('/accounts/login/?command=verification&email='+email)
    else:
        form = RegistrationForm()
    context = {
        "form": form,
    }
    return render(request, 'accounts/register.html', context)

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = auth.authenticate(email=email, password=password)
        if user is not None:
            auth.login(request, user)
            messages.success(request, 'You are now logged in.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid Credentials!')
            return redirect('login')
    return render(request, 'accounts/login.html')

@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'You are logged out.')
    return redirect('login')


def verify_email(request, user, mail_subject, render_string):
    current_site = get_current_site(request)
    mail_subject = mail_subject
    message = render_to_string(render_string, {
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
    })
    to_email = user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulations! your account is now activated.')
        return redirect('login')
    else:
        messages.error(request, 'Oops! Invalid activation link')
        return redirect('register')


def forgotPassword(request):
    if request.method == "POST":
        email = request.POST['email']
        user_exist = Account.objects.filter(email=email).exists()
        if user_exist:
            user = Account.objects.get(email__exact=email)
            # Forgot Password Email
            mail_subject = "Reset Your Password"
            render_string = 'accounts/emails/reset_password_email.html'
            verify_email(request, user, mail_subject, render_string)
            messages.success(request, "A password reset link has been sent to your email address. Please check your email.")
            return redirect('login')
        else:
            messages.error(request, "Invalid email address")
            return redirect('forgotPassword')
    return render(request, 'accounts/forgot_password.html')


@login_required(login_url='login')
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)

    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, "Please reset your password")
        return redirect('resetPassword')
    else:
        messages.error(request, "The link has been expired")
        return redirect('login')

def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, "Password reset successfully")
            return redirect('login')
        else:
            messages.error(request, "Password doesn't not match")
            return redirect('resetPassword')
    else:
        return render(request, "accounts/reset_password.html")