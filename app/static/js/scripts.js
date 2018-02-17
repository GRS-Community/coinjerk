function GetURL(username) {
  $.ajax({
 type: 'GET',
 url: 'https://api.twitch.tv/kraken/channels/'+username,
 headers: {
   'Client-ID': 'n7j8ddl0pu87ig063e6mnr33on17xw'
 },
 success: function(data) {
   $("#ProfilePicture").attr('src', data.logo);
 }
});
}
function AmountInput() {
  amount = $('#amountPaypalInput').val()
  prefix = ".0";
  var res = amount.concat(prefix);
  $("#PaypalAmount").attr('value', res);
}
