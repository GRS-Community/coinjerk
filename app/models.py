from hashlib import md5

from app import app, db

from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False)

    # fiat currency user desires conversion to, ISO 4217 currencies accepted
    # e.g. "USD", "GBP", "EUR", etc.
    fiat = db.Column(db.String(3))

    # either 'B' for BTC, 'm' for mBTC, or 'u' for uBTC/bits
    unit = db.Column(db.String(1))

    # streamlabs tokens, retreived from streamlabs authorization
    streamlabs_atoken = db.Column(db.String(40))
    streamlabs_rtoken = db.Column(db.String(40))


    #BIP32 Extended Public Key
    xpub = db.Column(db.String(111))

    #Latest Unused Address from Derivation Path
    latest_derivation = db.Column(db.Integer)

    # Display Text for Tip Page
    display_text = db.Column(db.String(500),
            default="This user sure does work hard on their stream "+\
                "and a tip into their Groestlcoin Wallet would very much be "+\
                "appreciated!",
            nullable=False)


    paypal_email = db.Column(db.String(100))
    sound_ref = db.Column(db.String(200), default='https://uploads.twitchalerts.com/000/003/774/415/m_health.wav')
    text_color = db.Column(db.String(10), default='#0066ff')
    image_ref = db.Column(db.String(200), default='https://cdn.discordapp.com/attachments/416659759178055688/417986781053452288/grsloop.gif')

    # Transaction Linkage
    transactions = db.relationship(
            "Transaction",
            backref='user',
            lazy='dynamic')

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)
        except NameError:
            return str(self.id)

    def __repr__(self):
        return'<User %r>' %(self.id)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tx_id = db.Column(db.String(64), nullable=False, unique=True)
    timestamp = db.Column(db.DateTime)

    # Amount in BTC
    amount = db.Column(db.Float)

    # derivation path for xpub keys, implement path
    #TODO Implement "refresh addresses"
    # xpub = db.Column(db.String(111), nullable=False)
    # wallet_derivation = db.Column(db.Integer, nullable=False)

    twi_user = db.Column(db.String(25))
    twi_message = db.Column(db.String(255))

    # payment_method = db.Column(db.String(10))

    def __repr__(self):
        return '<Transaction %r>' %(self.tx_id)

# Payment Request Model
class PayReq(db.Model):
    # Unique Database ID
    id = db.Column(db.Integer, primary_key=True)

    # Bitcoin Address
    addr = db.Column(db.String(34), nullable=False)

    # Time of creation
    timestamp = db.Column(db.DateTime)

    # User Fields
    user_display = db.Column(db.String(25))
    user_identifier = db.Column(db.String())
    user_message = db.Column(db.String(255))

    amount = db.Column(db.String)


    def __init__(self, address, user_display=None, user_identifier=None,
            user_message=None, amount=None):
        self.addr = address
        self.timestamp = datetime.utcnow()
        self.user_display = 'AnonymousGroestler'
        self.user_identifier = 'GRS_Tip_PleaseCheckYourWallet'
        if user_display:
            self.user_display = user_display
        if user_identifier:
            self.user_identifier = user_identifier
        if user_message:
            self.user_message = user_message
        if amount:
            self.amount = amount

    def __repr__(self):
        return '<PayReq %r>' %(self.addr)
