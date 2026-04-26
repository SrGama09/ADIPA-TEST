const API_BASE_URL = window.__ENV__?.API_BASE_URL || '';
const MAX_FILE_BYTES = 10 * 1024 * 1024;
const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.xlsx'];

const dropZone     = document.getElementById('drop-zone');
const fileInput    = document.getElementById('file-input');
const fileInfo     = document.getElementById('file-info');
const fileNameEl   = document.getElementById('file-name');
const fileSizeEl   = document.getElementById('file-size');
const btnProcess   = document.getElementById('btn-process');
const btnClear     = document.getElementById('btn-clear');
const spinner      = document.getElementById('spinner');
const errorBox     = document.getElementById('error-box');
const resultBox    = document.getElementById('result-box');
const resultCount  = document.getElementById('result-count');
const resultJson   = document.getElementById('result-json');
const questionsList = document.getElementById('questions-list');
const btnDownload  = document.getElementById('btn-download');

const TYPE_LABELS = {
  seleccion_multiple: 'Selección múltiple',
  verdadero_falso: 'Verdadero / Falso',
  desarrollo: 'Desarrollo',
  emparejamiento: 'Emparejamiento',
};

let selectedFile = null;
let lastResult   = null;

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

dropZone.addEventListener('click', (e) => {
  if (e.target.closest('label')) return;
  fileInput.click();
});

dropZone.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    fileInput.click();
  }
});

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) handleFile(fileInput.files[0]);
});

btnClear.addEventListener('click', resetSelection);

function handleFile(file) {
  clearMessages();
  const ext = '.' + (file.name.split('.').pop() || '').toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    showError(`Formato no soportado. Usa ${ALLOWED_EXTENSIONS.join(', ')}.`);
    resetSelection();
    return;
  }
  if (file.size > MAX_FILE_BYTES) {
    showError(`El archivo supera el máximo de ${formatSize(MAX_FILE_BYTES)}.`);
    resetSelection();
    return;
  }
  if (file.size === 0) {
    showError('El archivo está vacío.');
    resetSelection();
    return;
  }
  selectedFile = file;
  fileNameEl.textContent = file.name;
  fileSizeEl.textContent = formatSize(file.size);
  fileInfo.hidden = false;
  btnProcess.disabled = false;
}

function resetSelection() {
  selectedFile = null;
  fileInput.value = '';
  fileInfo.hidden = true;
  btnProcess.disabled = true;
}

function clearMessages() {
  errorBox.hidden = true;
  errorBox.textContent = '';
  resultBox.hidden = true;
  questionsList.innerHTML = '';
  resultJson.innerHTML = '';
  lastResult = null;
}

function setBusy(busy) {
  spinner.classList.toggle('is-active', busy);
  btnProcess.disabled = busy || !selectedFile;
  btnClear.disabled = busy;
  dropZone.setAttribute('aria-disabled', busy ? 'true' : 'false');
}

btnProcess.addEventListener('click', async () => {
  if (!selectedFile) return;
  clearMessages();
  setBusy(true);

  const formData = new FormData();
  formData.append('file', selectedFile);

  try {
    const response = await fetch(`${API_BASE_URL}/api/extract`, { method: 'POST', body: formData });
    let data;
    try { data = await response.json(); }
    catch { data = null; }

    if (!response.ok) {
      const detail = (data && data.detail) || `Error ${response.status}`;
      showError(detail);
      return;
    }

    lastResult = data;
    renderResult(data);
  } catch {
    showError('No se pudo conectar con el servidor. Intenta de nuevo.');
  } finally {
    setBusy(false);
  }
});

btnDownload.addEventListener('click', () => {
  if (!lastResult) return;
  const blob = new Blob([JSON.stringify(lastResult, null, 2)], { type: 'application/json' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = 'preguntas.json';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
});

function renderResult(data) {
  resultCount.textContent = `${data.total_preguntas} pregunta${data.total_preguntas === 1 ? '' : 's'} detectada${data.total_preguntas === 1 ? '' : 's'}`;
  questionsList.innerHTML = '';
  for (const q of data.preguntas) {
    questionsList.appendChild(renderQuestion(q));
  }
  resultJson.innerHTML = syntaxHighlight(JSON.stringify(data, null, 2));
  resultBox.hidden = false;
}

function renderQuestion(q) {
  const card = document.createElement('article');
  card.className = 'question-card';

  const head = document.createElement('div');
  head.className = 'question-head';
  const num = document.createElement('span');
  num.className = 'question-number';
  num.textContent = `Pregunta ${q.numero}`;
  const type = document.createElement('span');
  type.className = 'question-type';
  type.textContent = TYPE_LABELS[q.tipo] || q.tipo;
  head.append(num, type);

  const statement = document.createElement('p');
  statement.className = 'question-statement';
  statement.textContent = q.enunciado;

  card.append(head, statement);

  if (Array.isArray(q.alternativas) && q.alternativas.length > 0) {
    const list = document.createElement('ul');
    list.className = 'alternatives';
    for (const alt of q.alternativas) {
      const li = document.createElement('li');
      if (q.respuesta_correcta && alt.letra === q.respuesta_correcta) {
        li.classList.add('correct');
      }
      const letter = document.createElement('span');
      letter.className = 'alt-letter';
      letter.textContent = `${alt.letra}.`;
      const text = document.createElement('span');
      text.textContent = alt.texto;
      li.append(letter, text);
      list.appendChild(li);
    }
    card.appendChild(list);
  }

  if (q.respuesta_correcta && (!q.alternativas || q.alternativas.length === 0)) {
    const answer = document.createElement('p');
    answer.className = 'answer-line';
    answer.textContent = `Respuesta: ${q.respuesta_correcta}`;
    card.appendChild(answer);
  }

  return card;
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function syntaxHighlight(json) {
  const escaped = json
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  return escaped.replace(
    /("(\\u[\da-fA-F]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(\.\d+)?([eE][+-]?\d+)?)/g,
    (match) => {
      let cls = 'json-number';
      if (/^"/.test(match))               cls = /:$/.test(match) ? 'json-key' : 'json-string';
      else if (/true|false/.test(match))  cls = 'json-bool';
      else if (/null/.test(match))        cls = 'json-null';
      return `<span class="${cls}">${match}</span>`;
    }
  );
}
