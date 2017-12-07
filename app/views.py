#!flask/bin/python
from flask import render_template, flash, redirect, session, url_for, \
        request, g, send_file, abort, jsonify

from flask_login import current_user
from flask_qrcode import QRcode

from app import app, db, lm
from datetime import datetime, timedelta
from config import STREAMLABS_CLIENT_ID, STREAMLABS_CLIENT_SECRET, \
        COINSTREAM_REDIRECT_URI

from .forms import RegisterForm, ProfileForm
from .models import User, PayReq

from pycoin.key import Key
from exchanges.bitstamp import Bitstamp
from decimal import Decimal
import bitcoin
import requests
import time
import sys
import qrcode

streamlabs_api_url = 'https://www.twitchalerts.com/api/v1.0/'
api_token = streamlabs_api_url + 'token'
api_user = streamlabs_api_url + 'user'
api_tips = streamlabs_api_url + "donations"
callback_result = 0


@app.route('/')
@app.route('/index')
def index():
    if 'nickname' in session:
        return render_template(
                'user.html',
                social_id=session['social_id'],
                nickname=session['nickname'])
    return render_template(
            'indextemplate.html')


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

        db.session.commit()




    userlist = []
    '''
    userdb = User.query.all()
    for user in userdb:
        userdict = {}
        userdict['name'] = user.nickname
        userdict['num'] = 1
        userlist.append(userdict)
    '''

    return render_template(
            'usersettings.html',
            form=form,
            social_id=session['social_id'],
            nickname=session['nickname'],
            users = userlist
            )

@app.route('/login')
@app.route('/launch')
def login():
    if 'nickname' in session:
            return redirect(url_for('index'))

    if request.args.get('code'):
        session.clear()
        authorize_call = {
                'grant_type'    : 'authorization_code',
                'client_id'     : STREAMLABS_CLIENT_ID,
                'client_secret' : STREAMLABS_CLIENT_SECRET,
                'code'          : request.args.get('code'),
                'redirect_uri'  : COINSTREAM_REDIRECT_URI
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
        "&redirect_uri="+ COINSTREAM_REDIRECT_URI +
        "&response_type=code"+
        "&scope=donations.create alerts.create", code=302
    )
@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('nickname', None)
    return redirect(url_for('index'))

@app.route('/newuser', methods=['GET', 'POST'])
def newuser():
    print("entered /newuser")
    form = RegisterForm()
    print(form.xpub_field.data)

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
            'login.html',
            form=form)

@app.route('/donatecallback', methods=['GET', 'POST'])
def donatecallback():
    print(request.args)
    return "Hello World!"

@app.errorhandler(404)
def handle404(e):
    return "That user or page was not found in our system! " \
            + "Tell them to sign up for CoinStream!"


'''
Testing code below, please ignore
'''
@app.route('/test')
def test():
    return render_template(
            'homepagetemplate.html')
