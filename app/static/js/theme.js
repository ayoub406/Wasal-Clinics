(function () {
  var root = document.documentElement;
  var toggle = document.getElementById('themeToggle');
  if (!toggle) return;

  toggle.addEventListener('click', function () {
    var isDark = root.getAttribute('data-theme') === 'dark';
    var next = isDark ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    localStorage.setItem('wisal-theme', next);
  });
})();
