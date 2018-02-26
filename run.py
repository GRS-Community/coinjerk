#!flask/bin/python
from app import app

#shut up about the secret key
app.secret_key = "askldjfhaskldjfhlaksjhdfklajshdfkljasghdfjklhvgaskjdfygkasjdfhg"
app.run(host='0.0.0.0')
