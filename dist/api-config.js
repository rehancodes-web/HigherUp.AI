(function () {
  var RENDER_API = 'https://higherup-ai.onrender.com';
  var LOCAL_API = 'http://127.0.0.1:8000';
  var host = window.location.hostname;
  var isLocal = host === 'localhost' || host === '127.0.0.1' || host === '';
  var forceRender = new URLSearchParams(window.location.search).get('api') === 'render';
  window.HIGHERUP_API_BASE = isLocal && !forceRender ? LOCAL_API : RENDER_API;
  console.info('HigherUp API:', window.HIGHERUP_API_BASE);
})();
