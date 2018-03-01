

function GetURL(username) {
  $.ajax({
 type: 'GET',
 url: 'https://api.twitch.tv/kraken/channels/'+username,
 headers: {
   'Client-ID': 'n7j8ddl0pu87ig063e6mnr33on17xw'
 },
 success: function(data) {
   $("#ProfilePicture").attr('src', data.logo);
   $("#PaypalTwitchImgURL").attr('value', data.logo);
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
  var link = "http://127.0.0.1:5000/confirmation/";
  var return_url = link+userDisplay+"/to/"+socialId;
  $("#ReturnLink").attr('value', return_url);
  $.ajax({
              url: '/paypal',
              data: { 'user_display': $('#user_display').val(), 'user_identifier': $('#user_identifier').val(), 'user_message': $('#user_message').val() },
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
  console.log("Return_URL: " + return_url);

}
