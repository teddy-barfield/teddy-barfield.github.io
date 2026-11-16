// "On this page" return button for the long data pages.
// Any page that has the jump list (<nav class="toc" id="on-this-page">) and loads this file gets a small
// button fixed to the bottom-right corner. It appears once the list has scrolled off the top of the screen
// and takes the reader back to the list, so the next section is one tap away from anywhere on the page.
// It is an ordinary link to #on-this-page, so the browser's Back button returns to the place the reader left.
(function () {
  var toc = document.getElementById('on-this-page');
  if (!toc) return;
  toc.tabIndex = -1;   // lets the list take focus, so the keyboard carries on from its first link

  var link = document.createElement('a');
  link.className = 'to-toc';
  link.href = '#on-this-page';
  link.textContent = 'On this page';
  link.setAttribute('aria-label', 'Back to the "On this page" list of sections');
  link.hidden = true;
  var footer = document.querySelector('body > footer');
  document.body.insertBefore(link, footer);   // before the footer, so it is reached by Tab after the page's content
  document.body.classList.add('has-to-toc');  // the CSS leaves room under the footer so the button never covers it

  link.addEventListener('click', function () {
    toc.focus({ preventScroll: true });       // the link itself does the scrolling
  });

  function update() {
    // shown only when the whole list is above the top edge of the screen
    link.hidden = toc.getBoundingClientRect().bottom > 0;
  }
  if (window.IntersectionObserver) {
    new IntersectionObserver(update).observe(toc);
  } else {
    window.addEventListener('scroll', update, { passive: true });
  }
  update();
})();
