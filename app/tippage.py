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
from pycoin.key.validate import is_address_valid
from exchanges.bitstamp import Bitstamp
from decimal import Decimal
import json
import bitcoin
import requests
import time
import sys
import qrcode

streamlabs_api_url = 'https://www.twitchalerts.com/api/v1.0/'
api_token = streamlabs_api_url + 'token'
api_user = streamlabs_api_url + 'user'
api_tips = streamlabs_api_url + "donations"
api_custom = streamlabs_api_url + "alerts"
callback_result = 0

@app.route('/_verify_payment', methods=['POST'])
def verify_payment():
    btc_addr = request.form['btc_addr']
    social_id = request.form['social_id']
    payrec_check.user_identifier = request.form['userID'].append('_btc')
    payrec_check.user_message = request.form['userMsg']
    payrec_check.user_display = request.form['userName']
    db.session.commit()
    payrec_check = PayReq.query.filter_by(addr=btc_addr).first()
    print "PAYMENT CHECK"
    payment_check_return = {
            'payment_verified' : "FALSE",
            'user_display'     : User.query.filter_by(
                social_id=social_id
                ).first().nickname
    }

    print "***" + "checking for history" + "*** \r\n \r\n\r\n"
    history_check = bitcoin.history(btc_addr)
    #print "***" + history_check + "*** \r\n \r\n\r\n"
    if history_check and payrec_check:
        payment_check_return['payment_verified'] = "TRUE"
        print "Payment Found!"
        payment_notify(social_id, payrec_check)
        db.session.delete(payrec_check)
        db.session.commit()
    return jsonify(payment_check_return)

def payment_notify(social_id, payrec):
    '''
    Exchange Rate json file contains:
    'exchange' : BitStamp/BitFinex/Kraken/Etc
    'rate'     : USD-Pair Exchange Rate for BTC
    'datetime' : timestamp of when last grabbed
    '''
    user = User.query.filter_by(social_id=social_id).first()

    value = bitcoin.history(payrec.addr)[0]['value']
    with open("exchangerate.json", 'r') as f:
        latestexchange = json.loads(f.read())
        latestexchange['datetime'] = datetime.strptime(
                latestexchange['datetime'], '%Y-%m-%d %H:%M:%S.%f')

    if (datetime.today() - latestexchange['datetime']) <= timedelta(hours=1):
        exchange = latestexchange['rate']

    else:
        # If we fail to get exchange rate from Bitstamp, 
        # use old, stored value.
        try:
            exchange = Bitstamp().get_current_price()
            latestexchange = {
                    'exchange' : 'bitstamp',
                    'rate'     : exchange,
                    'datetime' : str(datetime.today())
                    }
            with open('exchangerate.json', 'w') as f:
                json.dump(latestexchange, f)

        except:
            exchange = latestexchange['rate']




    usd_value = ((value) * float(exchange)/100000000)
    usd_two_places = float(format(usd_value, '.2f'))
    token_call = {
                    'grant_type'    : 'refresh_token',
                    'client_id'     : STREAMLABS_CLIENT_ID,
                    'client_secret' : STREAMLABS_CLIENT_SECRET,
                    'refresh_token' : user.streamlabs_rtoken,
                    'redirect_uri'  : COINSTREAM_REDIRECT_URI
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

    return tip_check

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

@app.route('/tip/<username>')
def tip(username):
    u = User.query.filter_by(social_id=username.lower()).first()
    if u:
        return render_template(
                'tipv2.html',
                nickname = u.nickname,
                social_id = u.social_id,
                display_text = u.display_text
                )
    else:
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

    if is_address_valid(userdata.xpub) == "BTC":
        return "STREAMER SUBMITTED BTCADDR INSTEAD OF XPUB, PLEASE INFORM "\
                + "STREAMER OR DEVELOPER"

    if is_address_valid(key.address(use_uncompressed=False)) != "BTC":
        return "NO VALID ADDRESS, PLEASE INFORM STREAMER OR DEVELOPER"

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

'''
Testing code below, please ignore
'''
@app.route('/tiptest/<username>')
def tiptest(username):
    u = User.query.filter_by(social_id=username.lower()).first()
    if u:
        return render_template(
                    'tiptemplate.html',
                    nickname = u.nickname,
                    social_id = u.social_id,
                    display_text = u.display_text
                    )
    else:
        return abort(404)

#@app.route('/customalerttest')
def custom_notify():
    user = User.query.filter_by(social_id='amperture').first()

    usd_two_places = 15.00

    token_call = {
                    'grant_type'    : 'refresh_token',
                    'client_id'     : STREAMLABS_CLIENT_ID,
                    'client_secret' : STREAMLABS_CLIENT_SECRET,
                    'refresh_token' : user.streamlabs_rtoken,
                    'redirect_uri'  : COINSTREAM_REDIRECT_URI
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
            'type'       : 'donation',
            'message'    : '*Amperture* says hello there, and sent some *Bitcoin*!',
            'image_href' : '', 
            'sound_href' : 'http://uploads.twitchalerts.com/000/003/774/415/m_health.wav', 
            'duration'   : 3,
            'special_text_color' : '#42ff42',
            'access_token' : tip_response['access_token']
    }

    tip_check = requests.post(
            api_custom,
            data=tip_call,
            headers=headers
    ).json()
    print tip_check

    return "Hello World"

'''
TIP PAGE SETTINGS:
    - Alert System
        - Donation
          - Converted (bitstamp API)
          - mBTC to USD (no API, but assumes BTC/USD conversion rate of 1/1000)

'''
