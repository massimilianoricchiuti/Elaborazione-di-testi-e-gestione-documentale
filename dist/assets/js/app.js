(() => {
  const toggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('#main-nav');
  if (toggle && nav) {
    const closeMenu = () => {
      toggle.setAttribute('aria-expanded', 'false');
      nav.classList.remove('open');
    };
    toggle.addEventListener('click', () => {
      const expanded = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!expanded));
      nav.classList.toggle('open', !expanded);
    });
    nav.addEventListener('click', closeMenu);
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && nav.classList.contains('open')) {
        closeMenu();
        toggle.focus();
      }
    });
    const current = location.pathname.split('/').pop() || 'index.html';
    nav.querySelectorAll('a').forEach((link) => {
      if (link.getAttribute('href').split('/').pop() === current) link.setAttribute('aria-current', 'page');
    });
  }

  const sectionNav = document.querySelector('.section-nav');
  if (sectionNav) {
    const header = document.querySelector('.site-header');
    const links = Array.from(sectionNav.querySelectorAll('a[href^="#"]'));
    const sections = links.map((link) => document.getElementById(link.hash.slice(1)));
    let framePending = false;
    const updateSection = () => {
      const offset = header.offsetHeight + sectionNav.offsetHeight + 16;
      document.documentElement.style.setProperty('--home-anchor-offset', `${offset}px`);
      document.documentElement.style.setProperty('--site-header-height', `${header.offsetHeight}px`);
      let current = 0;
      sections.forEach((section, index) => {
        if (section.getBoundingClientRect().top <= offset + 1) current = index;
      });
      if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2) current = sections.length - 1;
      links.forEach((link, index) => {
        if (index === current) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
      framePending = false;
    };
    const scheduleUpdate = () => {
      if (!framePending) {
        framePending = true;
        requestAnimationFrame(updateSection);
      }
    };
    window.addEventListener('scroll', scheduleUpdate, {passive: true});
    window.addEventListener('resize', scheduleUpdate);
    if ('ResizeObserver' in window) {
      const observer = new ResizeObserver(scheduleUpdate);
      observer.observe(header);
      observer.observe(sectionNav);
    }
    updateSection();
  }

  const normalize = (value) => (value || '').toLocaleLowerCase('it').trim();
  document.querySelectorAll('[data-enhanced]').forEach((element) => { element.hidden = false; });

  const xmlTree = document.querySelector('.xml-tree');
  const xmlSearch = document.querySelector('#xml-search');
  const nodes = xmlTree ? Array.from(xmlTree.querySelectorAll('.xml-node')) : [];
  const xmlSearchStatus = document.querySelector('#xml-search-status');
  const filterXml = () => {
    const query = normalize(xmlSearch.value);
    let matches = 0;
    // Children are visited first so a matching descendant keeps its ancestors visible.
    [...nodes].reverse().forEach((node) => {
      const match = Boolean(query) && normalize(node.dataset.xmlSearch).includes(query);
      if (match) matches += 1;
      const descendantMatch = Boolean(node.querySelector('.xml-node:not([hidden])'));
      node.hidden = Boolean(query) && !match && !descendantMatch;
      node.classList.toggle('xml-match', match);
      if (node.tagName === 'DETAILS') node.open = query ? !node.hidden : node.dataset.defaultOpen === 'true';
    });
    xmlSearchStatus.textContent = query ? `${matches} elementi corrispondenti` : '';
  };
  if (xmlTree && xmlSearch) {
    xmlSearch.addEventListener('input', filterXml);
    document.querySelectorAll('[data-tree-action]').forEach((button) => {
      button.addEventListener('click', () => {
        xmlSearch.value = '';
        filterXml();
        xmlTree.querySelectorAll('details').forEach((node) => { node.open = button.dataset.treeAction === 'expand'; });
      });
    });
  }

  const viewNav = document.querySelector('.document-views');
  if (viewNav) {
    const tabs = Array.from(viewNav.querySelectorAll('[data-view]'));
    const panels = Array.from(document.querySelectorAll('[data-view-panel]'));
    const index = document.querySelector('.sheet-index');
    viewNav.setAttribute('role', 'tablist');
    tabs.forEach((tab) => {
      tab.setAttribute('role', 'tab');
      tab.setAttribute('aria-controls', tab.dataset.view);
    });
    panels.forEach((panel) => { panel.setAttribute('role', 'tabpanel'); panel.tabIndex = 0; });
    const activateHash = (scroll = false) => {
      let id;
      try { id = decodeURIComponent(location.hash.slice(1)); } catch { id = ''; }
      const target = document.getElementById(id);
      const panel = target?.closest('[data-view-panel]') || panels[0];
      panels.forEach((item) => { item.hidden = item !== panel; });
      tabs.forEach((tab) => {
        const active = tab.dataset.view === panel.id;
        tab.setAttribute('aria-selected', String(active));
        tab.tabIndex = active ? 0 : -1;
      });
      if (index) index.hidden = panel.id !== 'scheda';
      if (target?.classList.contains('xml-node')) {
        xmlSearch.value = '';
        filterXml();
        let node = target;
        while (node && node !== xmlTree) {
          if (node.tagName === 'DETAILS') node.open = true;
          node = node.parentElement;
        }
      }
      if (scroll && target) requestAnimationFrame(() => target.scrollIntoView({block: 'start'}));
    };
    tabs.forEach((tab, position) => {
      tab.addEventListener('click', (event) => {
        event.preventDefault();
        history.pushState(null, '', `#${tab.dataset.view}`);
        activateHash();
      });
      tab.addEventListener('keydown', (event) => {
        let next;
        if (event.key === 'ArrowRight') next = (position + 1) % tabs.length;
        if (event.key === 'ArrowLeft') next = (position + tabs.length - 1) % tabs.length;
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = tabs.length - 1;
        if (next !== undefined) {
          event.preventDefault();
          tabs[next].focus();
          tabs[next].click();
        }
      });
    });
    window.addEventListener('hashchange', () => activateHash(true));
    // pushState tabs do not emit hashchange; back/forward must restore the selected view.
    window.addEventListener('popstate', () => activateHash(true));
    activateHash(Boolean(location.hash));
  }

  const table = document.querySelector('#archive-table');
  if (!table) return;
  const tbody = table.querySelector('tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  const search = document.querySelector('#search');
  const type = document.querySelector('#type-filter');
  const city = document.querySelector('#city-filter');
  const region = document.querySelector('#region-filter');
  const count = document.querySelector('#visible-count');
  const form = document.querySelector('[data-table-filters]');
  const empty = document.querySelector('#no-results');
  const filterRows = () => {
    const query = normalize(search.value);
    let visible = 0;
    rows.forEach((row) => {
      const searchable = normalize(`${row.dataset.cig} ${row.dataset.filename} ${row.dataset.title} ${row.dataset.authority}`);
      const show = (!query || searchable.includes(query)) &&
        (!type.value || row.dataset.type === type.value) &&
        (!city.value || row.dataset.city === city.value) &&
        (!region.value || row.dataset.region === region.value);
      row.hidden = !show;
      if (show) visible += 1;
    });
    count.textContent = String(visible);
    if (empty) empty.hidden = visible !== 0;
  };
  [search, type, city, region].forEach((control) => control.addEventListener('input', filterRows));
  form.addEventListener('submit', (event) => event.preventDefault());
  form.addEventListener('reset', () => window.setTimeout(filterRows, 0));
  filterRows();

  table.querySelectorAll('[data-sort]').forEach((button) => {
    button.addEventListener('click', () => {
      const key = button.dataset.sort;
      const numeric = button.dataset.sortType === 'number';
      const ascending = button.dataset.direction !== 'asc';
      table.querySelectorAll('th').forEach((header) => header.removeAttribute('aria-sort'));
      table.querySelectorAll('[data-sort]').forEach((other) => { if (other !== button) delete other.dataset.direction; });
      button.dataset.direction = ascending ? 'asc' : 'desc';
      button.closest('th').setAttribute('aria-sort', ascending ? 'ascending' : 'descending');
      rows.sort((a, b) => {
        const left = a.dataset[key] || '';
        const right = b.dataset[key] || '';
        // Missing amounts stay at the end in both directions.
        if (numeric && (left === '' || right === '')) return Number(left === '') - Number(right === '');
        const comparison = numeric ? Number(left) - Number(right) : left.localeCompare(right, 'it');
        return ascending ? comparison : -comparison;
      }).forEach((row) => tbody.appendChild(row));
    });
  });
})();
