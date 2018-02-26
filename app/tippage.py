#!flask/bin/python
from flask import render_template, flash, redirect, session, url_for, \
        request, g, send_file, abort, jsonify

from flask_login import current_user
from flask_qrcode import QRcode

from app import app, db, lm
from datetime import datetime, timedelta
from config import STREAMLABS_CLIENT_ID, STREAMLABS_CLIENT_SECRET, \
        GROESTLTIP_REDIRECT_URI

from .forms import RegisterForm, ProfileForm
from .models import User, PayReq, Transaction

from pycoin.key import Key
from pycoin.key.validate import is_address_valid
from exchanges.bitstamp import Bitstamp
from exchanges.GRS_bittrex import GRS_price
from decimal import Decimal
from .payment import check_payment_on_address, check_address_history
import pprint
import json
import bitcoin
import requests
import time
import sys
import qrcode
import os

streamlabs_api_url = 'https://www.twitchalerts.com/api/v1.0/'
api_token = streamlabs_api_url + 'token'
api_user = streamlabs_api_url + 'user'
api_tips = streamlabs_api_url + "donations"
api_custom = streamlabs_api_url + "alerts"
callback_result = 0

# @app.route('/_delete_transaction_history')
# def delete_transaction_history():
#     Transaction.query.delete()
#     db.session.commit()
#     return redirect(url_for('history'))
# @app.route('/_delete_payreq_history')
# def delete_payreq_history():
#     PayReq.query.delete()
#     db.session.commit()
#     return redirect(url_for('history'))

@app.route('/_verify_payment', methods=['POST'])
def verify_payment():
    btc_addr = request.form['btc_addr']
    social_id = request.form['social_id']
    db.session.commit()
    payrec_check = PayReq.query.filter_by(addr=btc_addr).first()

    print("PAYMENT CHECK")
    history_check = check_address_history(btc_addr)
    payment_check_return = {
            'transaction_found': None,
            'payment_verified' : "FALSE",
            'user_display'     : User.query.filter_by(
                social_id=social_id
                ).first().nickname
    }
    print("***" + "checking for history on: " + btc_addr + "***\n")
    if history_check and payrec_check:
        payment_check_return['payment_verified'] = "TRUE"
        print("Payment Found!")
        amount = check_payment_on_address(btc_addr)
        print(amount)
        payment_check_return['transaction_found'] = history_check[0]['tx_hash']

        payment_notify(social_id,
                payrec_check,
                amount,
                history_check[0]['tx_hash'],
                btc_addr)

        db.session.delete(payrec_check)
        db.session.commit()
    return jsonify(payment_check_return)

def payment_notify(social_id, payrec, balance, txhash, grs_addr):
    '''
    Exchange Rate json file contains:
    'exchange' : BitStamp/BitFinex/Kraken/Etc
    'rate'     : USD-Pair Exchange Rate for BTC
    'datetime' : timestamp of when last grabbed
    '''
    user = User.query.filter_by(social_id=social_id).first()
    value = balance * GRS_price()
    print(GRS_price())
    print(value)
    is_latest_exchange_valid = False

    # if exchangerate.json doesnt already exists, create a new one
    if not os.path.exists('exchangerate.json'):
        f = open('exchangerate.json', 'w')
        f.write("{}")
        f.close()

    with open("exchangerate.json", 'r') as f:
        latestexchange = json.loads(f.read())
        # if the file is valid ('datetime' key exists), go on and parse it
        if 'datetime' in latestexchange:
            latestexchange['datetime'] = datetime.strptime(
                latestexchange['datetime'], '%Y-%m-%d %H:%M:%S.%f')

            if (datetime.today() - latestexchange['datetime']) <= timedelta(hours=1):
                print("using existing exchange rate")
                is_latest_exchange_valid = True
                exchange = latestexchange['rate']

    # If we fail to get exchange rate from Bitstamp,
    # use old, stored value.
    print("Exchange rate too old! Grabbing exchange rate from Bitstamp")
    try:
        exchange = Bitstamp().get_current_price()
        latestexchange = {
                'exchange' : 'bitstamp',
                'rate'     : float(exchange),
                'datetime' : str(datetime.today())
                }

        print("exchage rate data found!")
        print(latestexchange)
        with open('exchangerate.json', 'w') as f:
            print("Opened exchange rate file for recording")
            json.dump(latestexchange, f)
        print("exchange rate recorded")
    except:
        if is_latest_exchange_valid:
            exchange = latestexchange['rate']
        else:
            raise ValueError('No exchange rate available!')




    # print("Converting Donation Amount to USD")
    # print(value)
    # print(exchange)
    # print(type(value))
    # print(type(exchange))
    # print(float(exchange)/100000000)

    usd_value = ((value) * float(exchange)/100000000)
    usd_two_places = float(format(usd_value, '.2f'))
    grs_amount = ((balance) /100000000)
    #print(usd_two_places)
    token_call = {
                    'grant_type'    : 'refresh_token',
                    'client_id'     : STREAMLABS_CLIENT_ID,
                    'client_secret' : STREAMLABS_CLIENT_SECRET,
                    'refresh_token' : user.streamlabs_rtoken,
                    'redirect_uri'  : GROESTLTIP_REDIRECT_URI
    }
    headers = []
    #print("Acquiring Streamlabs Access Tokens")
    tip_response = requests.post(
            api_token,
            data=token_call,
            headers=headers
    ).json()
    #print("Tokens Acquired, Committing to Database")

    user.streamlabs_rtoken = tip_response['refresh_token']
    user.streamlabs_atoken = tip_response['access_token']
    db.session.commit()

    # grs_amount_display = " ("+ str(grs_amount) +" GRS Donated)"
    # tip_call = {
    #         'name'       : payrec.user_display,
    #         'identifier' : payrec.user_identifier,
    #         'message'    : payrec.user_message+grs_amount_display,
    #         'amount'     : usd_two_places,
    #         'currency'   : 'USD',
    #         'access_token' : tip_response['access_token']
    # }
    # tip_check = requests.post(
    #         api_tips,
    #         data=tip_call,
    #         headers=headers
    #     ).json()
    donation = " | " + social_id +" donated " + str(grs_amount) + " GRS($" + str(usd_two_places) + ")"
    tip_call = {
            'type'       : 'donation',
            'message'    : payrec.user_message+donation,
            'image_href' : 'https://cdn.discordapp.com/attachments/416659759178055688/417663443814973450/GRSLOGOSPININANDOUT.gif',
            'sound_href' : 'http://uploads.twitchalerts.com/000/003/774/415/m_health.wav',
            'duration'   : 3,
            'special_text_color' : '#42ff42',
            'access_token' : tip_response['access_token']
    }
    print(tip_call)

    tip_check = requests.post(
            api_custom,
            data=tip_call,
            headers=headers
    ).json()
    print(tip_check)
    # custom_notify(social_id, payrec.user_message, value, usd_two_places)
    print("Saving transaction data in database...")
    # transaction = Transaction.query.filter_by(addr=btc_addr).first()
    payreq = PayReq.query.filter_by(addr=grs_addr).first()
    new_transaction = Transaction(
        twi_user=payreq.user_display,
        twi_message=payreq.user_message,
        user_id=social_id,
        tx_id=txhash,
        amount=grs_amount,
        timestamp=payreq.timestamp
        )
    db.session.add(new_transaction)
    db.session.commit()

    print("Transaction data saved!")
    print("Donation Alert Sent")


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
            user_identifier=request.form['user_identifier']+"_grs",
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
                display_text = u.display_text,
                email = u.paypal_email
                )
    else:
        return render_template(

            '404.html',
            username=username
            )

def get_unused_address(social_id, deriv):
    '''
    Need to be careful about when to move up the latest_derivation listing.
    Figure only incrementing the database entry when blockchain activity is
    found is the least likely to create large gaps of empty addresses in
    someone's BTC Wallet.
    '''
    pp = pprint.PrettyPrinter(indent=2)
    userdata = User.query.filter_by(social_id = social_id).first()

    # Pull BTC Address from given user data
    key = Key.from_text(userdata.xpub).subkey(0). \
            subkey(deriv)

    address = key.address(use_uncompressed=False)

    # if is_address_valid(userdata.xpub) == "GRS":
    #     return "STREAMER SUBMITTED GRSADDR INSTEAD OF XPUB, PLEASE INFORM "\
    #             + "STREAMER OR DEVELOPER"
    #
    # if is_address_valid(address) != "GRS":
    #     return "NO VALID ADDRESS, PLEASE INFORM STREAMER OR DEVELOPER"

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

    pp.pprint(check_payment_on_address(address))
    if not check_address_history(address):
        if not payment_request:
            return address
        else:
            print("Address has payment request...")
            print("Address Derivation: ", deriv)
            return get_unused_address(social_id, deriv + 1)
    else:
        print("Address has blockchain history, searching new address...")
        print("Address Derivation: ", userdata.latest_derivation)
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



def custom_notify(social_id, user_message, value, usd_two_places):
    user = User.query.filter_by(social_id=social_id).first()


    token_call = {
                    'grant_type'    : 'refresh_token',
                    'client_id'     : STREAMLABS_CLIENT_ID,
                    'client_secret' : STREAMLABS_CLIENT_SECRET,
                    'refresh_token' : user.streamlabs_rtoken,
                    'redirect_uri'  : GROESTLTIP_REDIRECT_URI
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

    donation = " | " + social_id +" donated " + str(value) + " GRS($" + str(usd_two_places) + ")",

    tip_call = {
            'type'       : 'donation',
            'message'    : user_message + str(donation),
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
    print(tip_check)

    return "Hello World"

@app.route('/paypal', methods=['POST'])
def create_payment_request_paypal():
    print("create_payment_request_paypal():")

    if (request.form['user_display'] == ""):
        user_display = "AnonymousPaypaler"

    else:
        user_display = request.form['user_display']

    user_identifier = request.form['user_identifier']
    user_message = request.form['user_message']

    new_payment_request = PayReq(
            address="Streamer's paypal email",
            user_display=user_display,
            user_identifier=user_identifier+"_paypal",
            user_message=user_message
            )

    db.session.add(new_payment_request)
    db.session.commit()

    return jsonify({'data' : 'Payment Request made for: '+user_display})



@app.route('/confirmation/<username>/to/<social_id>', methods=['POST', 'GET'])
def confirmation(username,social_id):
    print(username)
    payreq = PayReq.query.filter_by(user_display=username).first()
    # try:
    if (payreq.user_display == "AnonymousGroestler"):
        user_display = "AnonymousPaypaler"
    else:
        user_display = payreq.user_display

    # except:
    #     return render_template(
    #             'cancel.html'
    #     )

    user_identifier = payreq.user_identifier
    user_message = payreq.user_message

    #Paypal post
    payer_email = request.form.get('payer_email')
    unix = int(time.time())
    payment_date = request.form.get('payment_date')
    username = request.form.get('custom')
    payment_gross = request.form.get('payment_gross')
    payment_fee = request.form.get('payment_fee')
    payment_status = request.form.get('payment_status')
    txn_id = request.form.get('txn_id')


    user = User.query.filter_by(social_id=social_id).first()

    token_call = {
                    'grant_type'    : 'refresh_token',
                    'client_id'     : STREAMLABS_CLIENT_ID,
                    'client_secret' : STREAMLABS_CLIENT_SECRET,
                    'refresh_token' : user.streamlabs_rtoken,
                    'redirect_uri'  : GROESTLTIP_REDIRECT_URI
    }
    headers = []
    #print("Acquiring Streamlabs Access Tokens")
    tip_response = requests.post(
            api_token,
            data=token_call,
            headers=headers
    ).json()
    #print("Tokens Acquired, Committing to Database")

    user.streamlabs_rtoken = tip_response['refresh_token']
    user.streamlabs_atoken = tip_response['access_token']
    db.session.commit()
    #print("Tokens Committed to database, sending donation alert")

    tip_call = {
            'name'       : user_display,
            'identifier' : payreq.user_identifier,
            'message'    : payreq.user_message,
            'amount'     : payment_gross,
            'currency'   : 'USD',
            'access_token' : tip_response['access_token']
    }
    print(tip_call)

    tip_check = requests.post(
            api_tips,
            data=tip_call,
            headers=headers
    ).json()
    print(tip_check)
    # custom_notify(social_id, payrec.user_message, value, usd_two_places)
    print("Donation Alert Sent")
    new_transaction = Transaction(
        twi_user=user_display,
        twi_message=user_message,
        user_id=social_id,
        tx_id=txn_id,
        amount=payment_gross,
        timestamp=payreq.timestamp
        )
    db.session.add(new_transaction)
    db.session.commit()


    return render_template(
            'confirmation.html',
            payer_email=payer_email,
            payment_date=payment_date,
            twitch_link="https://www.twitch.tv/"+social_id,
            payment_gross=payment_gross,
            payment_fee=payment_fee,
            payment_status=payment_status,
            txn_id=txn_id,
            user_display=user_display,
            user_identifier=user_identifier,
            user_message=user_message

            )
'''
TIP PAGE SETTINGS:
    - Alert System
        - Donation
          - Converted (bitstamp API)
          - mBTC to USD (no API, but assumes BTC/USD conversion rate of 1/1000)
'''
