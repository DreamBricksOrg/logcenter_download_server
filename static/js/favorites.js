(function () {
  const listEl = document.getElementById('favorites-list');
  const favoriteBtn = document.getElementById('favorite-btn');
  const overlay = document.getElementById('favorite-dialog-overlay');
  const nameInput = document.getElementById('favorite-name');
  const saveBtn = document.getElementById('favorite-save');
  const cancelBtn = document.getElementById('favorite-cancel');
  const errorEl = document.getElementById('favorite-error');

  function setError(message) {
    if (message) {
      errorEl.textContent = message;
      errorEl.hidden = false;
    } else {
      errorEl.hidden = true;
    }
  }

  function openDialog() {
    nameInput.value = '';
    setError(null);
    overlay.hidden = false;
    nameInput.focus();
  }

  function closeDialog() {
    overlay.hidden = true;
  }

  async function loadFavorites() {
    const response = await fetch('/api/favorites');
    const favorites = await response.json();
    renderFavorites(favorites);
  }

  function renderFavorites(favorites) {
    if (favorites.length === 0) {
      listEl.innerHTML = '<li class="empty-state">Nenhum favorito salvo ainda.</li>';
      return;
    }
    listEl.innerHTML = favorites.map((fav) => `
      <li class="favorite-item" data-filename="${fav.filename}">
        <button type="button" class="favorite-load" data-filename="${fav.filename}">
          <span class="favorite-name">${fav.name}</span>
          <span class="favorite-date">${fav.created_at}</span>
        </button>
        <button type="button" class="favorite-delete" data-filename="${fav.filename}" aria-label="Excluir favorito">
          <i data-lucide="trash-2"></i>
        </button>
      </li>
    `).join('');
    if (window.lucide) { window.lucide.createIcons(); }
  }

  listEl.addEventListener('click', async (event) => {
    const loadBtn = event.target.closest('.favorite-load');
    const deleteBtn = event.target.closest('.favorite-delete');
    if (loadBtn) {
      const response = await fetch(`/api/favorites/${encodeURIComponent(loadBtn.dataset.filename)}`);
      if (response.ok) {
        const favorite = await response.json();
        window.LogCenter.setPipelineText(favorite.pipeline);
      }
    } else if (deleteBtn) {
      await fetch(`/api/favorites/${encodeURIComponent(deleteBtn.dataset.filename)}`, { method: 'DELETE' });
      loadFavorites();
    }
  });

  favoriteBtn.addEventListener('click', openDialog);
  cancelBtn.addEventListener('click', closeDialog);

  saveBtn.addEventListener('click', async () => {
    const name = nameInput.value.trim();
    if (!name) {
      setError('Informe um nome.');
      return;
    }
    const response = await fetch('/api/favorites', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, pipeline: window.LogCenter.getPipelineText() }),
    });
    const data = await response.json();
    if (!response.ok) {
      setError(data.error || 'Erro ao salvar favorito.');
      return;
    }
    closeDialog();
    loadFavorites();
  });

  loadFavorites();
})();
