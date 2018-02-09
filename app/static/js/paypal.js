function Paypal() {
  paypal.Button.render({
    env: 'production', // Or 'sandbox',

    client: {
         sandbox:    'AVkP9pyDzHK7c2yVs0PH_taoFwhUiF72LPi4XxXbLkMTePpJEeoBFuLS7K99Y-ZHJfm3Mjlnki1H5dhE',
         production: 'ATZ25QipZ_kOVl5Ec6Z_a3epSBNi53-R5CGkeadGNOKZg0O0_CEb51ewX-cYssbD0ksK9WVLpmOtj5B6'
     },

    commit: true, // Show a 'Pay Now' button

    style: {
                label: 'paypal',
                size:  'medium',    // small | medium | large | responsive
                shape: 'rect',     // pill | rect
                color: 'blue',     // gold | blue | silver | black
                tagline: false
            },

    payment: function(data, actions) {
        return actions.payment.create({
                payment: {
                    transactions: [
                        {
                            amount: { total: '1.00', currency: 'USD' }
                        }
                    ]
                }
            });
    },

    onAuthorize: function(data, actions) {
      /*
       * Execute the payment here
       */
    },

    onCancel: function(data, actions) {
      return actions.payment.execute().then(function(payment) {

              // The payment is complete!
              // You can now show a confirmation message to the customer
          });
    },

    onError: function(err) {
      /*
       * An error occurred during the transaction
       */
    }
  }, '#paypal-button');
}
