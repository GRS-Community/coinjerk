from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField, SelectField
from wtforms.validators import Required, Length, DataRequired


class RegisterForm(FlaskForm):
    unit_choices = [
            ('B', 'BTC'),
            ('m', 'mBTC'),
            ('u', 'Bits')
    ]

    currencies = [
            ('USD', 'USD'),
            ('GBP', 'GBP'),
            ('EUR', 'EUR'),
    ]

    unit_field = SelectField(
            u'Preferred Coin Units',
            choices = unit_choices,
            validators = [Required()])

    fiat_field = SelectField(
            u'Preferred Currency Conversion',
            choices = currencies,
            validators = [Required()])

    user_display_text_field = StringField(
            u'Display Text for User Page',
            )

    xpub_field = StringField(
            u'Your Extended Master Public Key',
            validators = [DataRequired()])

class ProfileForm(FlaskForm):
    xpub_field = StringField(
            u'New Extended/Master Public Key')

    user_display_text_field = StringField(
            u'Text to display on your page')

    paypal_email_field = StringField(
            u'Your Paypal Email')

    sound_ref_field = StringField(u'Donation Sound')

    text_color_field = StringField(u'Color on Donation Text')
