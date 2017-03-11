
// Global vars
var isPaid = 0;

// When the document is ready
$(document).ready(function() { 
    // Events :)
    $('#user_form').submit(function (event) {
        createPayRequest();
    });
    $('#showModalButton').click(function (event) {
        // Stop redirections
        event.preventDefault();
        // Call our create pay request function
        createPayRequest(
                $('#user_display').val(),
                $('#user_identifier').val(),
                $('#user_message').val(),
                socialId
        );
    });
});
// We'll keep it inline for now...
function createPayRequest(userDisplay, userIdentifier, userMessage, socialId){
    // Get the value of some things on our form
    //$('#myModal').modal('show');
    // Create a new request to our server
    console.log("Social ID: " + socialId);
    console.log("User ID: " + userIdentifier);
    console.log("User Msg: " + userMessage);
    console.log("User Name: " + userDisplay);
    var resp = $.post('/_create_payreq', 
            // This will be formatted as a 'body' string in the post request
            {
                social_id: socialId,
                user_display: userDisplay,
                user_identifier: userIdentifier,
                user_message: userMessage
            }, 
            function (response)
            {
                console.log(response.btc_addr);
                $('#formBox').html(
                        "<p><strong>Please note that the payment will only be tracked while this page is open, and you have a five minute time limit. If either the page gets closed, or five minutes elapses after you see the Bitcoin address, please refresh the page to make a new payment request.</strong></p>"
                        )

                    $('#addressText').html(
                            "<p>Please send some bitcoin to the address <span class=\"highlight\">" + response.btc_addr + "</span></p>" +
                            "<p>Use either the QR code directly below with your mobile wallet, or the link to launch your wallet software.</p>"
                            );
                $('#addressQR').html("");
                $('#addressQR').qrcode({
                    text : "bitcoin:" + response.btc_addr
                });
                $('#addressLink').html(
                        "<p></p><p><a href=\"bitcoin:" + response.btc_addr + "\"type=\"button\" class=\"button2\">Launch Bitcoin Wallet</a></p>"
                        );

                // We use a global variable for isPaid because it will be easier to 'clear' it later
                isPaid = setTimeout(function() { 
                    verifyPayment(response.btc_addr)
                }, 5000);
            }
    , "json")
        .fail(
                function (request, status, errorThrown)
                {
                    // TODO: Handle Errors
                    console.log('We got an error! ' + status);
                }
             );

    // Proof of concept of live-updating code on page
    //<p><a href="bitcoin:{{ btc_addr }}" type="button" class="btn btn-primary">Launch Bitcoin Wallet</a>
    return false;
}

function verifyPayment(btc_addr){
    // Does this work? I have no idea!
    var postVars = "btc_addr="+btc_addr+"&social_id="+socialId;

    var resp = $.post('/_verify_payment',
            {
                social_id: socialId,
                btc_addr: btc_addr
            }, 
            function (response)
            {
                // Debug
                console.log(response.payment_verified)

                    // Unsure as to what it returns on the py
                    // You can make the json a boolean though?
                    if (response.payment_verified == "TRUE"){
                        // Clear our timeout
                        clearTimeout(isPaid);
                        $('#addressLocation').html(
                                "<strong>Payment Verified! "+nickname+" thanks you very much for the tip!</strong>" +
                                "<p>CoinJerk is a service provided for free and without ads, if you would like to help support " +
                                "the developer in general or help cover operating costs for CoinJerk, please consider " +
                                "<p><a href=\"https://coinjerk.com/tip/amperture\" class=\"button2\">Support the Developer</a></p><br>" + 
                                "<p><a href=\"https://coinjerk.com/tip/coinjerk\"class=\"button2\">Support CoinJerk</a></p>"
                                );
                    }
                    else {
                        // Not Paid
                        isPaid = setTimeout(function() { 
                            verifyPayment(btc_addr)
                        }, 5000);
                    }
            }
    , "json")
        .fail(
                function (request, status, errorThrown)
                {
                    // TODO: Handle Errors
                    console.log('We got an error! ' + status);
                }
             );
}
