## Setup instructions

* Clone repository
* Activate your virtualenv
* `$ pip install -r requirements.txt`
* Create `config.ini` file with Streamlabs API key details
* `$ export FLASK_APP=run.py` or `$ set FLASK_APP=run.py`(Windows)
* `$ flask run

### config.ini example

```
[CoinStream]
secret_key = xxx
streamlabs_client_id = xxx
streamlabs_client_secret = xxx
redirect_uri = http://127.0.0.1:5000/launch
```