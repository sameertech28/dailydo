/* DailyDo — main.js */

document.addEventListener('DOMContentLoaded', function () {

  // ── AUTO-DISMISS TOASTS ──
  const toasts = document.querySelectorAll('.toast-alert');
  toasts.forEach(toast => {
    setTimeout(() => {
      toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(16px)';
      setTimeout(() => toast.remove(), 400);
    }, 4000);
  });

  // ── TOGGLE REMOVED TASKS ──
  const collapsedHeaders = document.querySelectorAll('.collapsed-header');
  collapsedHeaders.forEach(header => {
    header.addEventListener('click', function () {
      const targetId = this.dataset.toggle;
      const target = document.getElementById(targetId);
      const arrow = this.querySelector('.toggle-arrow');
      if (target) {
        const isHidden = target.style.display === 'none' || target.style.display === '';
        target.style.display = isHidden ? 'flex' : 'none';
        target.style.flexDirection = 'column';
        if (arrow) {
          arrow.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0)';
        }
      }
    });
  });

  // ── TASK COMPLETE ANIMATION ──
  document.querySelectorAll('.check-btn:not(.check-btn--done):not(.check-btn--removed):not(.check-btn--archived)').forEach(btn => {
    btn.addEventListener('click', function () {
      const card = this.closest('.task-card');
      if (card) {
        card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        card.style.opacity = '0.5';
        card.style.transform = 'scale(0.98)';
      }
    });
  });

  // ── CHARACTER COUNTER FOR TASK TITLE ──
  const titleInput = document.querySelector('#id_title');
  if (titleInput) {
    const maxLen = 200;
    const counter = document.createElement('div');
    counter.className = 'form-hint char-counter';
    counter.style.textAlign = 'right';
    titleInput.parentNode.appendChild(counter);

    function updateCounter() {
      const remaining = maxLen - titleInput.value.length;
      counter.textContent = `${titleInput.value.length}/${maxLen}`;
      counter.style.color = remaining < 20 ? '#ef4444' : '';
    }

    titleInput.addEventListener('input', updateCounter);
    updateCounter();
  }

  // ── CONFIRM REMOVE TASK ──
  document.querySelectorAll('.task-btn--remove').forEach(btn => {
    btn.addEventListener('click', function (e) {
      const title = this.closest('.task-card')?.querySelector('.task-title')?.textContent?.trim();
      if (!confirm(`Remove "${title || 'this task'}" from today's list?`)) {
        e.preventDefault();
        e.stopPropagation();
      }
    });
  });

  // ── DATE FILTER AUTO-SUBMIT ──
  const dateFilter = document.querySelector('#date-filter');
  if (dateFilter) {
    dateFilter.addEventListener('change', function () {
      this.closest('form').submit();
    });
  }

  // ── KEYBOARD SHORTCUT: N to add new task ──
  document.addEventListener('keydown', function (e) {
    if (e.key === 'n' && !e.ctrlKey && !e.metaKey && !e.shiftKey) {
      const activeTag = document.activeElement?.tagName?.toLowerCase();
      if (activeTag === 'input' || activeTag === 'textarea') return;
      const addBtn = document.querySelector('.btn-add');
      if (addBtn) {
        e.preventDefault();
        addBtn.click();
      }
    }
  });

  // ── CAPACITY BAR FILL ──
  const capacityFill = document.querySelector('.capacity-fill');
  if (capacityFill) {
    // Read remaining from the label
    const label = document.querySelector('.capacity-label');
    if (label) {
      const match = label.textContent.match(/(\d+)\/(\d+)/);
      if (match) {
        const remaining = parseInt(match[1]);
        const max = parseInt(match[2]);
        const used = max - remaining;
        const pct = Math.round((used / max) * 100);
        capacityFill.style.width = pct + '%';
      }
    }
  }

  // ── PROGRESS BAR ANIMATION ON LOAD ──
  const progressFill = document.querySelector('.progress-fill');
  if (progressFill) {
    const targetWidth = progressFill.style.width;
    progressFill.style.width = '0';
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        progressFill.style.width = targetWidth;
      });
    });
  }

});
