// Picks the API address automatically.
//  - Site opened on localhost / 127.0.0.1  -> your local FastAPI
//  - Site opened anywhere else (hosted)    -> the Render backend
//  - Add ?api=render to a local URL to test the Render backend from your laptop.
(function () {
  var RENDER_API = 'https://higherup-ai.onrender.com';
  var LOCAL_API = 'http://127.0.0.1:8000';
  var host = window.location.hostname;
  var isLocal = host === 'localhost' || host === '127.0.0.1' || host === '';
  var forceRender = new URLSearchParams(window.location.search).get('api') === 'render';
  window.HIGHERUP_API_BASE = isLocal && !forceRender ? LOCAL_API : RENDER_API;
  console.info('HigherUp API:', window.HIGHERUP_API_BASE);
})();
