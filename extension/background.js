// Checks GitHub twice a day for a newer Second Wind and flags it.
// Unpacked extensions can't update themselves, so we tell people when (and how) to grab the new zip.
var api = typeof browser !== "undefined" ? browser : chrome;
var VERSION_URL = "https://raw.githubusercontent.com/IordAIXL/SecondWind/main/VERSION";

function newer(a, b) { // is a newer than b?
  var x = String(a).trim().split("."), y = String(b).trim().split(".");
  for (var i = 0; i < Math.max(x.length, y.length); i++) {
    var p = parseInt(x[i] || "0", 10), q = parseInt(y[i] || "0", 10);
    if (p !== q) return p > q;
  }
  return false;
}

function check() {
  var mine = api.runtime.getManifest().version;
  return fetch(VERSION_URL + "?t=" + Date.now(), { cache: "no-store" })
    .then(function (r) { return r.ok ? r.text() : null; })
    .then(function (latest) {
      if (!latest) return;
      latest = latest.trim();
      var update = newer(latest, mine) ? latest : null;
      api.storage.local.set({ update: update, checkedAt: Date.now() });
      try {
        api.action.setBadgeText({ text: update ? "NEW" : "" });
        api.action.setBadgeBackgroundColor({ color: "#fbbf24" });
      } catch (e) { /* no badge support */ }
    })
    .catch(function () { /* offline: try again later */ });
}

api.runtime.onInstalled.addListener(function () { api.storage.local.set({ update: null }); check(); });
api.runtime.onStartup.addListener(check);
try {
  api.alarms.create("sw-update-check", { periodInMinutes: 720 });
  api.alarms.onAlarm.addListener(function (a) { if (a.name === "sw-update-check") check(); });
} catch (e) { /* alarms unavailable */ }
api.runtime.onMessage.addListener(function (msg, sender, reply) {
  if (msg === "sw-check") { check().then(function () { reply(true); }); return true; }
  if (msg === "sw-reload") { api.runtime.reload(); }
});
