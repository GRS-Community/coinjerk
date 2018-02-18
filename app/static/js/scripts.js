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

function AmountInput() {
  var amount = document.getElementById("amountPaypalInput").value.replace(",",".");
    var n = parseFloat(amount).toFixed("2");
    $("#PaypalAmount").attr('value', n);

}
