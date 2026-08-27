(function () {
  const modeButtons = {
    single: document.getElementById('mode-single'),
    range: document.getElementById('mode-range'),
  };
  const endField = document.getElementById('date-end-field');
  const startLabel = document.getElementById('date-start-label');
  const applyBtn = document.getElementById('apply-date');
  const errorEl = document.getElementById('datepicker-error');
  let mode = 'single';

  function setMode(newMode) {
    mode = newMode;
    endField.hidden = mode === 'single';
    startLabel.textContent = mode === 'single' ? 'Data' : 'De';
    modeButtons.single.className = mode === 'single' ? 'btn btn-secondary btn-sm' : 'btn btn-ghost btn-sm';
    modeButtons.range.className = mode === 'range' ? 'btn btn-secondary btn-sm' : 'btn btn-ghost btn-sm';
  }

  modeButtons.single.addEventListener('click', () => setMode('single'));
  modeButtons.range.addEventListener('click', () => setMode('range'));

  function showError(message) {
    errorEl.textContent = message;
    errorEl.hidden = false;
  }

  function clearError() {
    errorEl.hidden = true;
  }

  function nextDay(dateStr) {
    const d = new Date(`${dateStr}T00:00:00Z`);
    d.setUTCDate(d.getUTCDate() + 1);
    return d.toISOString().slice(0, 10);
  }

  function buildClause() {
    const start = document.getElementById('date-start').value;
    if (!start) {
      showError('Escolha uma data.');
      return null;
    }
    if (mode === 'single') {
      return `timestamp: { $regex: "^${start}" }`;
    }
    const end = document.getElementById('date-end').value;
    if (!end) {
      showError('Escolha a data final do intervalo.');
      return null;
    }
    const endExclusive = nextDay(end);
    return `timestamp: { $gte: "${start}T00:00:00Z", $lt: "${endExclusive}T00:00:00Z" }`;
  }

  function findBlockEndLine(lines, startIndex) {
    let depth = 0;
    let started = false;
    for (let i = startIndex; i < lines.length; i++) {
      for (const ch of lines[i]) {
        if (ch === '{') {
          depth++;
          started = true;
        } else if (ch === '}') {
          depth--;
        }
      }
      if (started && depth <= 0) {
        return i;
      }
    }
    return startIndex;
  }

  function applyToEditor(clause) {
    const editor = document.getElementById('pipeline-editor');
    const lines = editor.value.split('\n');
    const timestampLineRe = /^\s*\/{0,2}\s*timestamp\s*:/;
    const matchLineRe = /\$match\s*:\s*\{/;

    const lineIndex = lines.findIndex((line) => timestampLineRe.test(line));
    if (lineIndex !== -1) {
      const indentMatch = lines[lineIndex].match(/^\s*/);
      const indent = indentMatch ? indentMatch[0] : '      ';
      const endLineIndex = findBlockEndLine(lines, lineIndex);
      const hadTrailingComma = /,\s*$/.test(lines[endLineIndex]);
      lines.splice(lineIndex, endLineIndex - lineIndex + 1, `${indent}${clause}${hadTrailingComma ? ',' : ''}`);
      editor.value = lines.join('\n');
      return true;
    }

    const matchIndex = lines.findIndex((line) => matchLineRe.test(line));
    if (matchIndex === -1) {
      showError('Não encontrei um estágio $match no pipeline.');
      return false;
    }
    const indentMatch = lines[matchIndex].match(/^\s*/);
    const indent = `${indentMatch ? indentMatch[0] : ''}  `;
    lines.splice(matchIndex + 1, 0, `${indent}${clause},`);
    editor.value = lines.join('\n');
    return true;
  }

  applyBtn.addEventListener('click', () => {
    clearError();
    const clause = buildClause();
    if (!clause) return;
    applyToEditor(clause);
  });

  setMode('single');
})();
