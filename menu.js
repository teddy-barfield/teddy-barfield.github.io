// Opens and closes the Projects dropdown. Closes on outside click or Escape.
document.querySelectorAll(".menu").forEach(function (menu) {
  var toggle = menu.querySelector(".menu-toggle");
  var list = menu.querySelector(".menu-list");
  function setOpen(open) {
    toggle.setAttribute("aria-expanded", String(open));
    list.hidden = !open;
  }
  toggle.addEventListener("click", function () {
    setOpen(toggle.getAttribute("aria-expanded") !== "true");
  });
  document.addEventListener("click", function (e) {
    if (!menu.contains(e.target)) setOpen(false);
  });
  menu.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { setOpen(false); toggle.focus(); }
  });
});
