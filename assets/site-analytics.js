/* Stoneferry Trading: visitor analytics for every page of the site.

   TO SWITCH IT ON
   1. Create a free project at https://clarity.microsoft.com (sign in, "New project", site URL stoneferrytrading.com).
   2. Copy the Project ID from Settings > Overview. It looks like "k3x9abcd12".
   3. Paste it between the quotes on the CLARITY_PROJECT_ID line below and commit.
   While the ID is empty, nothing is loaded and nothing is recorded.

   WHAT IT DOES
   - Loads Microsoft Clarity: page views, clicks, scroll depth, time on page, session replays, heatmaps.
   - Tagged links: a link such as  https://stoneferrytrading.com/market-brief/?r=b053  marks that visit
     with the code "b053" (Clarity: Filters > Custom tags > ref). Use a short code per recipient, never a name
     or an email address.
   - Named events: any element with a  data-track="some_name"  attribute sends that event when clicked,
     and pages can call  sfTrack("some_name")  themselves (Clarity: Filters > Smart events / custom events).
   - Honors the browser's Global Privacy Control signal: if it is on, nothing is loaded.
*/
(function () {
  var CLARITY_PROJECT_ID = "";

  var w = window, d = document;

  w.sfTrack = function (name) {
    try { if (typeof w.clarity === "function") { w.clarity("event", String(name)); } } catch (e) {}
  };

  d.addEventListener("click", function (e) {
    var t = e.target && e.target.closest ? e.target.closest("[data-track]") : null;
    if (t) { w.sfTrack(t.getAttribute("data-track")); }
  });

  var ref = null;
  try {
    var m = /[?&]r=([A-Za-z0-9_-]{1,40})(?:&|#|$)/.exec(w.location.search);
    if (m) { ref = m[1]; w.sessionStorage.setItem("sf_ref", ref); }
    else { ref = w.sessionStorage.getItem("sf_ref"); }
  } catch (e) {}

  if (!CLARITY_PROJECT_ID) { return; }
  if (navigator.globalPrivacyControl === true) { return; }

  (function (c, l, a, r, i, t, y) {
    c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
    t = l.createElement(r); t.async = 1; t.src = "https://www.clarity.ms/tag/" + i;
    y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t, y);
  })(w, d, "clarity", "script", CLARITY_PROJECT_ID);

  if (ref) { w.clarity("set", "ref", ref); }
})();
