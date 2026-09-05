(function () {
  var deptSelect = document.getElementById('department_id');
  var doctorSelect = document.getElementById('doctor_id');
  var dateInput = document.getElementById('preferred_date');

  if (dateInput) {
    var today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);
  }

  if (!deptSelect || !doctorSelect) return;

  var urlBase = deptSelect.getAttribute('data-doctors-url-base');
  var anyOptionText = doctorSelect.options[0] ? doctorSelect.options[0].text : '';

  function loadDoctors(slug, keepSelection) {
    if (!slug) return;
    var url = urlBase.replace('__SLUG__', slug);
    fetch(url)
      .then(function (res) { return res.json(); })
      .then(function (doctors) {
        doctorSelect.innerHTML = '';
        var anyOpt = document.createElement('option');
        anyOpt.value = '';
        anyOpt.textContent = anyOptionText;
        doctorSelect.appendChild(anyOpt);

        doctors.forEach(function (doc) {
          var opt = document.createElement('option');
          opt.value = doc.id;
          opt.textContent = doc.title ? doc.name + ' — ' + doc.title : doc.name;
          doctorSelect.appendChild(opt);
        });
      })
      .catch(function () { /* تجاهل الخطأ بصمت، يبقى الخيار الافتراضي */ });
  }

  deptSelect.addEventListener('change', function () {
    var opt = deptSelect.options[deptSelect.selectedIndex];
    loadDoctors(opt.getAttribute('data-slug'));
  });

  var preselected = deptSelect.options[deptSelect.selectedIndex];
  if (preselected && preselected.getAttribute('data-slug')) {
    loadDoctors(preselected.getAttribute('data-slug'));
  }
})();
