/* Thansk to https://xss-game.appspot.com/static/game-frame.js for this js code */
var originalAlert = window.alert;
window.alert = function(s) {
  setTimeout(function() {
    originalAlert("Congratulations, you advanced to the next level");
    window.location = "/advance";
  }, 50);
}
