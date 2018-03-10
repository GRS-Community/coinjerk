#!flask/bin/python
from flask import render_template, flash, redirect, session, url_for, \
        request, g, send_file, abort, jsonify

from flask_admin import Admin
from flask_bootstrap import Bootstrap
from flask_login import current_user
from flask_qrcode import QRcode

from app import app, db, lm
from datetime import datetime, timedelta
from config import STREAMLABS_CLIENT_ID, STREAMLABS_CLIENT_SECRET, \
        GROESTLTIP_REDIRECT_URI

from .forms import RegisterForm, ProfileForm
from .models import User, PayReq, Transaction


from pycoin_grs.key import Key
from exchanges.bitstamp import Bitstamp
from decimal import Decimal
import bitcoin
import requests
import time
import sys
import qrcode
from werkzeug.datastructures import ImmutableOrderedMultiDict


streamlabs_api_url = 'https://www.twitchalerts.com/api/v1.0/'
api_token = streamlabs_api_url + 'token'
api_user = streamlabs_api_url + 'user'
api_tips = streamlabs_api_url + "donations"
callback_result = 0

Bootstrap(app)

@app.route('/')
@app.route('/index')
def index():
    if 'nickname' in session:
        if 'social_id' in session:
            nickname=session['nickname']
            try:
                return redirect(url_for('user', username=nickname))
            except:
                return redirect(url_for('logout'))



    return render_template(
            'index.html')

@app.route('/user/<username>')
def user(username):



    # if 'nickname' in session:
    #     u = User.query.filter_by(social_id=username.lower()).first()
    #     if u:
    #         return render_template(
    #
    #             'user.html',
    #             social_id=session['social_id'],
    #             nickname=session['nickname'],
    #             display_text = u.display_text
    #
    #             )
    u = User.query.filter_by(social_id=username.lower()).first()
    if u:
        return render_template(

            'user.html',
            nickname = u.nickname,
            social_id = u.social_id,
            display_text = u.display_text

            )

    else:
        return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not "social_id" in session:
        return redirect(url_for('index'))
    form = ProfileForm()
    if request.method == "POST":
        u = User.query.filter_by(social_id=session['social_id']).first()
        if form.xpub_field.data:
            u.xpub = form.xpub_field.data
            u.latest_derivation = 0
        if form.user_display_text_field.data:
            u.display_text = form.user_display_text_field.data
        if form.paypal_email_field.data:
            u.paypal_email = form.paypal_email_field.data
            print(u.paypal_email)


        db.session.commit()
        nickname=session['nickname']
        return redirect(url_for('user', username=nickname))





    userlist = []
    '''
    userdb = User.query.all()
    for user in userdb:
        userdict = {}
        userdict['name'] = user.nickname
        userdict['num'] = 1
        userlist.append(userdict)
    '''
    userdata = User.query.filter_by(social_id=session['social_id']).first()
    if userdata.paypal_email:
        email = userdata.paypal_email
    else:
        email = optional = 'Optional: If you want to recieve paypal donations'
    return render_template(
            'usersettings.html',
            form=form,
            social_id=session['social_id'],
            nickname=session['nickname'],
            users = userlist,
            xpub = userdata.xpub,
            display_text = userdata.display_text,
            email = email
            )

@app.route('/users')
def users():
    return render_template(
            'users.html',
            users = User.query.all()
    )

@app.route('/history')
def history():
    return render_template(
            'history.html',
            tx = Transaction.query.order_by(Transaction.timestamp.desc()).all(),
            users = User.query.all()
    )

@app.route('/login')
@app.route('/launch')
def login():
    if 'nickname' in session:
        return redirect(url_for('user', username=session['nickname']))

    if request.args.get('code'):
        session.clear()
        authorize_call = {
                'grant_type'    : 'authorization_code',
                'client_id'     : STREAMLABS_CLIENT_ID,
                'client_secret' : STREAMLABS_CLIENT_SECRET,
                'code'          : request.args.get('code'),
                'redirect_uri'  : GROESTLTIP_REDIRECT_URI
        }

        headers = []

        token_response = requests.post(
                api_token,
                data=authorize_call,
                headers=headers
        )

        token_data = token_response.json()

        a_token = token_data['access_token']
        r_token = token_data['refresh_token']

        user_get_call = {
                'access_token' : a_token
        }

        user_access = requests.get(api_user,
                params=user_get_call)

        session.clear()
        session['social_id'] = user_access.json()['twitch']['name']
        session['nickname'] = user_access.json()['twitch']['display_name']
        session['access_token'] = a_token
        session['refresh_token'] = r_token

        valid_user = User.query.filter_by(social_id=session['social_id'])\
                .first()
        if valid_user:
            valid_user.streamlabs_atoken = a_token
            valid_user.streamlabs_rtoken = r_token
            db.session.commit()
            return redirect(url_for('profile'))
        else:
            return redirect(url_for('newuser'))

    return redirect(
        "http://www.twitchalerts.com/api/v1.0/authorize?client_id="+\
        STREAMLABS_CLIENT_ID +
        "&redirect_uri="+ GROESTLTIP_REDIRECT_URI +
        "&response_type=code"+
        "&scope=donations.create alerts.create", code=302
    )
@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('nickname', None)
    session.pop('social_id', None)
    return redirect(url_for('index'))

@app.route('/newuser', methods=['GET', 'POST'])
def newuser():
    print("entered /newuser")
    form = RegisterForm()

    if 'social_id' in session and request.method == 'POST':
        try:
            new_user = User(
                streamlabs_atoken = session['access_token'],
                streamlabs_rtoken = session['refresh_token'],
                xpub = form.xpub_field.data,
                social_id = session['social_id'],
                nickname = session['nickname'],
                latest_derivation = 0,
                display_text = form.user_display_text_field.data
            )
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('profile'))
        except Exception as e:
            print (str(e))

    try:
        username = session['nickname']
    except KeyError:
        username = "UNKNOWN USERNAME"

    return render_template(
            'register.html',
            form=form)

@app.route('/donatecallback', methods=['GET', 'POST'])
def donatecallback():
    print(request.args)
    return "Hello World!"

@app.errorhandler(404)
def handle404(e):
    return render_template(
            '404.html')

admin = Admin(app, name='Gronate', template_mode='bootstrap3')
'''
Admin

@app.route('/admin')
def admin():
    return render_template(
            'admin.html')
'''
'''
Testing code below, please ignore
'''
@app.route('/twitch/<username>')
def twitch(username):
    return redirect(
        "https://www.twitch.tv/"+username

    )

@app.route('/cancelled')
def cancelled_return():
    return render_template(
            'cancel.html')

@app.route('/about')
def about():
    return render_template(
            'about.html',
            users = User.query.all(),
            nickname=session['nickname']
    )

@app.route('/how')
def how():
    return render_template(
            'how.html'

    )
