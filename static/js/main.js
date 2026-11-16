/* ============================================================
   ShopKhata — Main JS
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {

  /* ---- Sidebar toggle (mobile) ---- */
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  let overlay = document.getElementById('sidebarOverlay');

  // Create overlay element if missing
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'sidebarOverlay';
    document.body.appendChild(overlay);
  }

  function openSidebar() {
    sidebar && sidebar.classList.add('show');
    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    sidebar && sidebar.classList.remove('show');
    overlay.classList.remove('show');
    document.body.style.overflow = '';
  }

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function () {
      if (sidebar && sidebar.classList.contains('show')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  overlay.addEventListener('click', closeSidebar);

  // Close sidebar on nav link click (mobile)
  if (sidebar) {
    sidebar.querySelectorAll('.nav-link').forEach(function (link) {
      link.addEventListener('click', function () {
        if (window.innerWidth < 992) closeSidebar();
      });
    });
  }

  /* ---- Auto-dismiss flash alerts after 4 seconds ---- */
  document.querySelectorAll('[data-auto-dismiss]').forEach(function (el) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      if (bsAlert) bsAlert.close();
    }, 4000);
  });

  /* ---- Confirm delete dialogs ---- */
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      const msg = el.getAttribute('data-confirm') || 'Are you sure?';
      if (!window.confirm(msg)) {
        e.preventDefault();
      }
    });
  });

  /* ---- Payment page: fetch outstanding balance on customer change ---- */
  const customerSelect = document.getElementById('customer_id');
  const balanceDisplay = document.getElementById('customer-balance-display');

  if (customerSelect && balanceDisplay) {
    customerSelect.addEventListener('change', function () {
      const id = this.value;
      if (!id) {
        balanceDisplay.textContent = '';
        return;
      }
      fetch('/api/balance/' + id)
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data && typeof data.balance !== 'undefined') {
            const bal = parseFloat(data.balance);
            balanceDisplay.innerHTML =
              'Outstanding Balance: <strong class="' +
              (bal > 0 ? 'text-danger' : 'text-success') +
              '">₹' + bal.toFixed(2) + '</strong>';
          } else {
            balanceDisplay.textContent = '';
          }
        })
        .catch(function () {
          balanceDisplay.textContent = '';
        });
    });

    // Trigger on load if pre-selected
    if (customerSelect.value) {
      customerSelect.dispatchEvent(new Event('change'));
    }
  }

  /* ---- Set default date inputs to today ---- */
  document.querySelectorAll('input[type="date"][data-default-today], input[type="date"].today-default').forEach(function (el) {
    if (!el.value) {
      const today = new Date().toISOString().split('T')[0];
      el.value = today;
    }
  });

  /* ---- Sortable tables ---- */
  document.querySelectorAll('th[data-sort]').forEach(function (th) {
    th.style.cursor = 'pointer';
    th.addEventListener('click', function () {
      const table = th.closest('table');
      const tbody = table.querySelector('tbody');
      const idx = Array.from(th.parentElement.children).indexOf(th);
      const asc = th.getAttribute('data-sort-dir') !== 'asc';
      th.setAttribute('data-sort-dir', asc ? 'asc' : 'desc');

      const rows = Array.from(tbody.querySelectorAll('tr'));
      rows.sort(function (a, b) {
        const va = a.cells[idx] ? a.cells[idx].textContent.trim() : '';
        const vb = b.cells[idx] ? b.cells[idx].textContent.trim() : '';
        const na = parseFloat(va.replace(/[^0-9.-]/g, ''));
        const nb = parseFloat(vb.replace(/[^0-9.-]/g, ''));
        if (!isNaN(na) && !isNaN(nb)) return asc ? na - nb : nb - na;
        return asc ? va.localeCompare(vb) : vb.localeCompare(va);
      });
      rows.forEach(function (row) { tbody.appendChild(row); });

      // Update sort icons
      table.querySelectorAll('th[data-sort]').forEach(function (h) {
        h.querySelector('.sort-icon') && h.querySelector('.sort-icon').remove();
      });
      const icon = document.createElement('i');
      icon.className = 'bi bi-caret-' + (asc ? 'up' : 'down') + '-fill ms-1 sort-icon';
      th.appendChild(icon);
    });
  });

});
