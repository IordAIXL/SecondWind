// Toolbar popup: lifetime count, update notice, and a way to bring back a hidden button.
(function () {
  var api = typeof browser !== "undefined" ? browser : chrome;
  var $ = function (id) { return document.getElementById(id); };
  $("ver").textContent = api.runtime.getManifest().version;
  function render() {
    api.storage.local.get(["total", "hidden", "update", "checkedAt"], function (r) {
      r = r || {};
      $("total").textContent = r.total || 0;
      var hidden = Object.keys(r.hidden || {});
      var b = $("unhide");
      b.hidden = !hidden.length;
      if (hidden.length) {
        b.textContent = "Show the button again (" + hidden.join(", ") + ")";
        b.onclick = function () { api.storage.local.set({ hidden: {} }); b.hidden = true; };
      }
      $("upd").hidden = !r.update;
      if (r.update) $("newv").textContent = r.update;
    });
  }
  $("reload").onclick = function () { api.runtime.sendMessage("sw-reload"); window.close(); };
  $("chk").onclick = function (e) {
    e.preventDefault();
    $("chk").textContent = "Checking...";
    api.runtime.sendMessage("sw-check", function () {
      render();
      api.storage.local.get(["update"], function (r) { $("chk").textContent = r && r.update ? "Update found" : "You're up to date"; });
    });
  };
  render();
})();
