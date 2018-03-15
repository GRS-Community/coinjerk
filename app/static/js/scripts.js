function GetURL(username) {
  $.ajax({
 type: 'GET',
 url: 'https://api.twitch.tv/kraken/channels/'+username,
 headers: {
   'Client-ID': 'n7j8ddl0pu87ig063e6mnr33on17xw'
 },
 success: function(data) {
   $("#ProfilePicture").attr('src', data.logo);
   // $("#ProfileBanner").attr('src', data.profile_banner);
 }
});
}

function GetBannerURL(username) {
  $.ajax({
    type: 'GET',
    url: 'https://api.twitch.tv/kraken/channels/'+username,
    headers: {
    'Client-ID': 'n7j8ddl0pu87ig063e6mnr33on17xw'
  },
  success: function(data) {
    if (data.profile_banner == null) {
      $("#ProfileBanner").css("height", "0");

    }
    else
      $("#ProfileBanner").css({"background" : "url('" + data.profile_banner + "') left bottom", "height" : "380px"});
    }
  });
}
function GetStreamStatus(username) {
  $.ajax({
 type: 'GET',
 url: 'https://api.twitch.tv/kraken/streams/'+username,
 headers: {
   'Client-ID': 'n7j8ddl0pu87ig063e6mnr33on17xw'
 },
 success: function(data) {
   if (data.stream == null) {
     $('#Status').html("<span><div class=\"status-light sl-red\"></div>OFFLINE</span>")
   }
   else
    $('#Status').html("<span><div class=\"status-light sl-green\"></div>LIVE</span>")


 }
});
}

function createPayRequestPaypal() {
  // Converting the amount input into the correct format
  postVars = "social_id="+socialId;
  var amount = document.getElementById("amountPaypalInput").value.replace(",",".");
  var n = parseFloat(amount).toFixed("2");
  $("#PaypalAmount").attr('value', n);
  // Getting form data
  var userDisplay = $("#user_display").val();
  var userIdentifier = $('#user_identifier').val();
  var userMessage = $('#user_message').val();

  if(userDisplay == ''){
         var userDisplay = "AnonymousDonator"
    }
  // Making Return_URL
  var confirmation_link = "http://groestltip.groestlcoin.org/confirmation/";
  var confirmation_return_url = confirmation_link+userDisplay+"/to/"+socialId;
  $("#ReturnLink").attr('value', confirmation_return_url);

  var notify_link = "http://groestltip.groestlcoin.org/ipn/";
  var notify_return_url = notify_link+userDisplay+"/to/"+socialId;
  $("#ReturnData").attr('value', notify_return_url);

  $.ajax({
              url: '/paypal',
              data: { 'user_display': $('#user_display').val(), 'user_identifier': $('#user_identifier').val(), 'user_message': $('#user_message').val(), 'amount': $("#PaypalAmount").val() },
              type: 'POST',
              async: false,
              success: function(response) {
                  console.log(response.data);
              },
              error: function(jqXHR, textStatus){ console.log( "Request failed: " + textStatus ) }
          });
  //Printing stuff into console
  console.log("userDisplay: "+userDisplay);
  console.log("userIdentifier: "+userIdentifier);
  console.log("userMessage: "+userMessage);
  console.log("Return_URL: " + confirmation_return_url);
  console.log("DataReturn_URL: " + notify_return_url);

}
