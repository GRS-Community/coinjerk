#!flask/bin/python
from flask import render_template, flash, redirect, session, url_for, \
        request, g, send_file, abort, jsonify 

from flask_login import current_user
from flask_qrcode import QRcode

from app import app, db, lm
from datetime import datetime, timedelta
from config import STREAMLABS_CLIENT_ID, STREAMLABS_CLIENT_SECRET

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
    user = { 'nickname': 'Amp' }
    return render_template(
            'index.html',
            user=user)

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

    return render_template(
            'registerpage.html',
            form=form,
            social_id=session['social_id'],
            nickname=session['nickname']
            )

@app.route('/login')
def login():
    if 'nickname' in session:
            return redirect(url_for('profile'))

    if request.args.get('code'):
        session.clear()
        authorize_call = {
                'grant_type'    : 'authorization_code',
                'client_id'     : STREAMLABS_CLIENT_ID,
                'client_secret' : STREAMLABS_CLIENT_SECRET,
                'code'          : request.args.get('code'),
                'redirect_uri'  : 'http://coinstream.co:5000/login'
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

        user_access = requiest.get(api_user,
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
            "&redirect_uri=http://coinstream.co:5000/login"+
            "&response_type=code"+
            "&scope=donations.read+donations.create", code=302
        )


@app.route('/newuser', methods=['GET', 'POST'])
def newuser():
    form = RegisterForm()
    print form.xpub_field.data

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
        except Exception,e:
            print str(e)

    try:
        username = session['nickname']
    except KeyError: 
        username = "UNKNOWN USERNAME"

    return render_template(
            'login.html',
            form=form)

@app.route('/register')
def register():
    return "no"

@app.route('/donatecallback', methods=['GET', 'POST'])
def donatecallback():
    print request.args
    return "Hello World!"

@app.route('/tip/<username>')
def tip(username):
    if username.lower() == "amperture" \
            or username.lower() == "darabidduckie":
        u = User.query.filter_by(social_id=username.lower()).first()
        if u:
            return render_template(
                    'tip.html',
                    nickname = u.nickname,
                    social_id = u.social_id,
                    display_text = u.display_text
                    )
    return abort(404)

def get_unused_address(social_id, deriv):
    '''
    Need to be careful about when to move up the latest_derivation listing.
    Figure only incrementing the database entry when blockchain activity is
    found is the least likely to create large gaps of empty addresses in
    someone's BTC Wallet.
    '''

    userdata = User.query.filter_by(social_id = social_id).first()

    # Pull BTC Address from given user data 
    key = Key.from_text(userdata.xpub).subkey(0). \
            subkey(deriv)
    address = key.address(use_uncompressed=False)

    # Check for existing payment request, delete if older than 5m.
    payment_request = PayReq.query.filter_by(addr=address).first()
    if payment_request:
        req_timestamp = payment_request.timestamp
        now_timestamp = datetime.utcnow()
        delta_timestamp = now_timestamp - req_timestamp
        if delta_timestamp > timedelta(seconds=60*5):
            db.session.delete(payment_request)
            db.session.commit()
            payment_request = None

    if not bitcoin.history(address):
        if not payment_request:
            return address
        else: 
            print "Address has payment request..."
            print "Address Derivation: ", deriv
            return get_unused_address(social_id, deriv + 1)
    else:
        print "Address has blockchain history, searching new address..."
        print "Address Derivation: ", userdata.latest_derivation
        userdata.latest_derivation = userdata.latest_derivation + 1
        db.session.commit()
        return get_unused_address(social_id, deriv + 1)

@app.route('/_create_payreq', methods=['POST'])
def create_payment_request():
    social_id = request.form['social_id']
    deriv = User.query.filter_by(social_id = social_id).first(). \
            latest_derivation
    address = get_unused_address(social_id, deriv)
    new_payment_request = PayReq(
            address,
            user_display=request.form['user_display'],
            user_identifier=request.form['user_identifier']+"_btc",
            user_message=request.form['user_message']
            )
    db.session.add(new_payment_request)
    db.session.commit()
    return jsonify(
            {'btc_addr': address}
            )

@app.route('/_verify_payment', methods=['POST'])
def verify_payment():
    btc_addr = request.form['btc_addr']
    social_id = request.form['social_id']
    payrec_check = PayReq.query.filter_by(addr=btc_addr).first()
    print "Checking for payment"
    payment_check_return = {
            'payment_verified' : "FALSE"
    }

    if bitcoin.history(btc_addr) and payrec_check:
        payment_check_return['payment_verified'] = "TRUE"
        print "Payment Found!"
        payment_notify(social_id, payrec_check)
        db.session.delete(payrec_check)
        db.session.commit()
    return jsonify(payment_check_return)

def payment_notify(social_id, payrec):
    user = User.query.filter_by(social_id=social_id).first()

    value = bitcoin.history(payrec.addr)[0]['value']
    exchange = Bitstamp().get_current_price()
    usd_value = ((value) * float(exchange)/100000000)
    usd_two_places = float(format(usd_value, '.2f'))

    token_call = {
                    'grant_type'    : 'refresh_token',
                    'client_id'     : STREAMLABS_CLIENT_ID,
                    'client_secret' : STREAMLABS_CLIENT_SECRET,
                    'refresh_token' : user.streamlabs_rtoken,
                    'redirect_uri'  : 'http://coinstream.co:5000/login'
    }
    headers = []
    tip_response = requests.post(
            api_token,
            data=token_call,
            headers=headers
    ).json()

    user.streamlabs_rtoken = tip_response['refresh_token']
    user.streamlabs_atoken = tip_response['access_token']
    db.session.commit()

    tip_call = {
            'name'       : payrec.user_display,
            'identifier' : payrec.user_identifier,
            'message'    : payrec.user_message,
            'amount'     : usd_two_places,
            'currency'   : 'USD',
            'access_token' : tip_response['access_token']
    }
    tip_check = requests.post(
            api_tips,
            data=tip_call,
            headers=headers
    ).json()

@app.errorhandler(404)
def handle404(e):
    return "That user or page was not found in our system! " \
            + "Tell them to sign up for CoinStream!"
