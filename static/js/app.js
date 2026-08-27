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
  const downloadDateOverlay = document.getElementById('download-date-dialog-overlay');
  const downloadDateInfo = document.getElementById('download-date-info');
  const downloadDateCancelBtn = document.getElementById('download-date-cancel');
  const downloadDateTodayBtn = document.getElementById('download-date-today');
  const downloadDatePipelineBtn = document.getElementById('download-date-pipeline');
  let pendingDownloadFormat = null;

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

  function extractPipelineDate() {
    const text = editor.value;
    const singleMatch = text.match(/\$regex:\s*"\^(\d{4}-\d{2}-\d{2})/);
    if (singleMatch) return singleMatch[1];
    const rangeMatch = text.match(/\$gte:\s*ISODate\("(\d{4}-\d{2}-\d{2})/);
    if (rangeMatch) return rangeMatch[1];
    return null;
  }

  function todayDateStr() {
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const dd = String(now.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
  }

  function openDownloadDateDialog(fmt) {
    pendingDownloadFormat = fmt;
    const pipelineDate = extractPipelineDate();
    downloadDatePipelineBtn.disabled = !pipelineDate;
    downloadDateInfo.textContent = pipelineDate
      ? `Data encontrada no aggregation: ${pipelineDate}`
      : 'Não encontrei uma data no aggregation.';
    downloadDateOverlay.hidden = false;
  }

  function closeDownloadDateDialog() {
    downloadDateOverlay.hidden = true;
    pendingDownloadFormat = null;
  }

  async function downloadFormat(fmt, dateStr) {
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
      const filename = `logcenter_${dateStr}.${fmt}`;
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
  downloadButtons.csv.addEventListener('click', () => openDownloadDateDialog('csv'));
  downloadButtons.xlsx.addEventListener('click', () => openDownloadDateDialog('xlsx'));
  downloadButtons.json.addEventListener('click', () => openDownloadDateDialog('json'));

  downloadDateCancelBtn.addEventListener('click', closeDownloadDateDialog);

  downloadDateTodayBtn.addEventListener('click', () => {
    const fmt = pendingDownloadFormat;
    closeDownloadDateDialog();
    downloadFormat(fmt, todayDateStr());
  });

  downloadDatePipelineBtn.addEventListener('click', () => {
    const fmt = pendingDownloadFormat;
    const pipelineDate = extractPipelineDate();
    closeDownloadDateDialog();
    downloadFormat(fmt, pipelineDate || todayDateStr());
  });

  window.LogCenter = {
    getPipelineText: () => editor.value,
    setPipelineText: (text) => { editor.value = text; },
  };
})();
