import random
import string
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import UserProfile, PaymentRequest, LicenseKey


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not username or not password:
            messages.error(request, '⚠️ Please fill all fields!')
            return render(request, 'client/login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, '❌ Invalid username or password!')
    
    return render(request, 'client/login.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        confirm = request.POST.get('confirm', '').strip()
        
        if not username or not password or not confirm:
            messages.error(request, '⚠️ Please fill all fields!')
        elif len(password) < 4:
            messages.error(request, '⚠️ Password too short!')
        elif password != confirm:
            messages.error(request, '⚠️ Passwords do not match!')
        elif User.objects.filter(username=username).exists():
            messages.error(request, '⚠️ Username already taken!')
        else:
            user = User.objects.create_user(username=username, password=password)
            UserProfile.objects.create(user=user, credits=0)
            messages.success(request, '✅ Account created! Please login.')
            return redirect('login')
    
    return render(request, 'client/signup.html')


def logout_view(request):
    logout(request)
    messages.success(request, '✅ Logged out successfully!')
    return redirect('login')


@login_required(login_url='login')
def dashboard_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    generated_key = None
    error_msg = None

    if request.method == 'POST':
        license_type = request.POST.get('license_type')
        if not license_type:
            error_msg = '❌ Please select a plan!'
        else:
            cost = int(license_type)
            day_map = {1: 1, 5: 7, 15: 30}
            days = day_map.get(cost, 1)

            if profile.credits < cost:
                error_msg = '❌ Insufficient Credits! Recharge to continue.'
            else:
                profile.credits -= cost
                profile.save()
                key = 'DRIP-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
                LicenseKey.objects.create(user=request.user, key=key, days=days, credits_used=cost)
                generated_key = key
                messages.success(request, '✅ License key generated successfully!')

    return render(request, 'client/dashboard.html', {
        'profile': profile,
        'generated_key': generated_key,
        'error_msg': error_msg,
    })


@login_required(login_url='login')
def recharge_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    status_msg = None
    msg_type = 'error'

    if request.method == 'POST':
        utr = request.POST.get('utr', '').strip()
        credits = request.POST.get('credits', '7')
        
        if not utr or not credits:
            messages.error(request, '⚠️ Please fill all fields!')
        elif len(utr) != 12 or not utr.isdigit():
            messages.error(request, '❌ Invalid UTR! Must be exactly 12 digits.')
        elif PaymentRequest.objects.filter(utr=utr).exists():
            messages.error(request, '❌ This UTR already submitted!')
        else:
            try:
                credits = int(credits)
                amount_map = {7: 199, 15: 399}
                amount = amount_map.get(credits, 199)

                PaymentRequest.objects.create(
                    user=request.user,
                    utr=utr,
                    credits_requested=credits,
                    amount=amount,
                )
                messages.success(request, '✅ Payment submitted! Credits added in 10-30 mins.')
            except Exception as e:
                messages.error(request, f'❌ Error: {str(e)}')

    return render(request, 'client/recharge.html', {
        'profile': profile,
    })
