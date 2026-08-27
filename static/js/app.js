(function () {
  const editor = document.getElementById('pipeline-editor');
  const runBtn = document.getElementById('run-btn');
  const runError = document.getElementById('run-error');
  const tableWrap = document.getElementById('preview-table-wrap');
  const resultCount = document.getElementById('result-count');
  const downloadButtons = {
    csv: document.getElementById('download-csv'),
    xlsx: document.getElementById('download-xlsx'),
    json: document.getElementById('download-json'),
  };

  function setRunError(message) {
    if (message) {
      runError.textContent = message;
      runError.hidden = false;
    } else {
      runError.hidden = true;
    }
  }

  function setDownloadsEnabled(enabled) {
    Object.values(downloadButtons).forEach((btn) => { btn.disabled = !enabled; });
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function renderTable(columns, rows) {
    if (rows.length === 0) {
      tableWrap.innerHTML = '<p class="empty-state">Nenhum resultado encontrado.</p>';
      return;
    }
    const thead = `<thead><tr>${columns.map((c) => `<th>${escapeHtml(c)}</th>`).join('')}</tr></thead>`;
    const tbody = `<tbody>${rows.map((row) => `<tr>${columns.map((c) => `<td>${escapeHtml(row[c] ?? '')}</td>`).join('')}</tr>`).join('')}</tbody>`;
    tableWrap.innerHTML = `<table class="table">${thead}${tbody}</table>`;
  }

  async function runPipeline() {
    setRunError(null);
    setDownloadsEnabled(false);
    runBtn.disabled = true;
    try {
      const response = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pipeline: editor.value }),
      });
      const data = await response.json();
      if (!response.ok) {
        setRunError(data.error || 'Erro ao executar a aggregation.');
        resultCount.textContent = '0 linhas';
        tableWrap.innerHTML = '<p class="empty-state">Rode uma aggregation para ver o resultado aqui.</p>';
        return;
      }
      resultCount.textContent = `${data.count} linha${data.count === 1 ? '' : 's'}`;
      renderTable(data.columns, data.rows);
      setDownloadsEnabled(data.count > 0);
    } catch (err) {
      setRunError('Erro de rede ao executar a aggregation.');
    } finally {
      runBtn.disabled = false;
    }
  }

  async function downloadFormat(fmt) {
    setRunError(null);
    try {
      const response = await fetch(`/download/${fmt}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pipeline: editor.value }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        setRunError(data.error || 'Erro ao gerar o arquivo.');
        return;
      }
      const blob = await response.blob();
      const disposition = response.headers.get('Content-Disposition') || '';
      const match = disposition.match(/filename="([^"]+)"/);
      const filename = match ? match[1] : `logcenter.${fmt}`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setRunError('Erro de rede ao baixar o arquivo.');
    }
  }

  runBtn.addEventListener('click', runPipeline);
  downloadButtons.csv.addEventListener('click', () => downloadFormat('csv'));
  downloadButtons.xlsx.addEventListener('click', () => downloadFormat('xlsx'));
  downloadButtons.json.addEventListener('click', () => downloadFormat('json'));

  window.LogCenter = {
    getPipelineText: () => editor.value,
    setPipelineText: (text) => { editor.value = text; },
  };
})();
