// Toolbar popup: lifetime count and a way to bring back a hidden button.
(function () {
  var api = typeof browser !== "undefined" ? browser : chrome;
  document.getElementById("ver").textContent = api.runtime.getManifest().version;
  api.storage.local.get(["total", "hidden"], function (r) {
    r = r || {};
    document.getElementById("total").textContent = r.total || 0;
    var hidden = Object.keys(r.hidden || {});
    var b = document.getElementById("unhide");
    if (hidden.length) {
      b.hidden = false;
      b.textContent = "Show the button again (" + hidden.join(", ") + ")";
      b.onclick = function () { api.storage.local.set({ hidden: {} }); b.hidden = true; };
    }
  });
})();
